"""邮件模块路由

【MVC 归属】Controller 层（表现层）
【思路】
1. GET  /targets          高潜客户筛选（分位数 + 分页）
2. POST /generate         批量生成营销邮件（customer_ids / limit 二选一）
3. GET  /prompt           获取当前生效 Prompt 模板
4. PUT  /prompt           更新 Prompt 模板
5. GET  /records          分页查询邮件记录（普通用户看自己，admin 看全部）
6. GET  /records/<rid>    单条邮件详情（含 content 正文）
7. PUT  /records/<rid>    修改邮件主题/正文
8. PATCH /records/<rid>   修改邮件状态
9. DELETE /records/<rid>  单条删除邮件
10. DELETE /records       批量删除邮件

严格对齐 auth.py / data.py / model.py 写法：BizException + json 响应；
@login_required 鉴权装饰器；_parse_int_arg 公共参数解析。
"""
from flask import Blueprint, request
from app.core.database import get_db
from app.core.response import json, BizException
from app.core.dependencies import login_required, get_current_user, record_operate_log
from app.models.email_record import EmailRecord
from app.services.email_service import (
    filter_high_target_customers, batch_generate_emails,
    get_active_prompt, update_prompt_template,
)

bp = Blueprint("email", __name__)


def _parse_int_arg(name: str, default=None):
    """公共辅助：从 query 取整型参数，非法抛 BizException(1001)"""
    val = request.args.get(name)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except ValueError:
        raise BizException(1001, f"参数 {name} 必须为整数", 400)


def _parse_float_arg(name: str, default=None):
    """公共辅助：从 query 取浮点型参数，非法抛 BizException(1001)"""
    val = request.args.get(name)
    if val is None or val == "":
        return default
    try:
        return float(val)
    except ValueError:
        raise BizException(1001, f"参数 {name} 必须为数字", 400)


# ===== 4.1 筛选高潜客户 =====
@bp.route("/targets", methods=["GET"])
@login_required
def targets():
    """高潜客户筛选：按 predicted_prob 分位数取 top (1-percentile) 客户

    查询参数：percentile（默认 0.9）、page（默认 1）、per_page（默认 20）
    响应：{threshold, total, customers: [...]}
    """
    percentile = _parse_float_arg("percentile", default=0.9)
    page = _parse_int_arg("page", default=1)
    per_page = _parse_int_arg("per_page", default=20)

    if page < 1:
        raise BizException(1001, "page 必须 >= 1", 400)
    if per_page < 1:
        raise BizException(1001, "per_page 必须 >= 1", 400)
    if not (0 < percentile < 1):
        raise BizException(1001, "percentile 必须在 0~1 之间", 400)

    db = get_db()
    result = filter_high_target_customers(db, percentile)

    # 内存分页（高潜客户量不大，避免复杂 SQL 分页）
    customers = result["customers"]
    total = len(customers)
    pages = (total + per_page - 1) // per_page if per_page else 0
    start = (page - 1) * per_page
    end = start + per_page
    paged_customers = customers[start:end]

    return json({
        "threshold": result["threshold"],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": pages,
        "customers": paged_customers,
    })


# ===== 4.2 生成营销邮件 =====
@bp.route("/generate", methods=["POST"])
@login_required
def generate():
    """批量生成营销邮件：customer_ids 指定客户 / limit 取 top N

    请求体（二选一）：
    - customer_ids: list[int]  指定客户 id 列表
    - limit: int               自动取 top N（默认 5，customer_ids 为空时生效）
    """
    user = get_current_user()
    db = get_db()
    body = request.get_json(silent=True) or {}

    customer_ids = body.get("customer_ids")
    limit = body.get("limit", 5)

    if not isinstance(limit, int) or limit < 1:
        raise BizException(1001, "limit 必须为正整数", 400)

    if customer_ids is not None and not isinstance(customer_ids, list):
        raise BizException(1001, "customer_ids 必须为数组", 400)

    result = batch_generate_emails(db, customer_ids, limit, user.id)
    return json(result)


# ===== 4.3 获取 Prompt 模板 =====
@bp.route("/prompt", methods=["GET"])
@login_required
def get_prompt():
    """获取当前生效 Prompt 模板：返回 {name, content}"""
    db = get_db()
    result = get_active_prompt(db)
    return json(result)


# ===== 4.4 更新 Prompt 模板 =====
@bp.route("/prompt", methods=["PUT"])
@login_required
def update_prompt():
    """更新 Prompt 模板：请求体 {content: string}

    响应：{name, content}
    """
    body = request.get_json(silent=True) or {}
    content = body.get("content")
    if not content or not content.strip():
        raise BizException(1001, "content 不能为空", 400)

    db = get_db()
    result = update_prompt_template(db, content)
    return json(result)


# ===== 4.5 邮件记录列表 =====
@bp.route("/records", methods=["GET"])
@login_required
def records():
    """分页查询邮件记录：普通用户仅看自己，admin 看全部（附 created_by_username）

    查询参数：page（默认 1）、per_page（默认 50）、status（可选 generated/failed/sent）
    """
    user = get_current_user()
    page = _parse_int_arg("page", default=1)
    per_page = _parse_int_arg("per_page", default=50)
    status_filter = request.args.get("status") or None

    if page < 1:
        raise BizException(1001, "page 必须 >= 1", 400)
    if per_page < 1:
        raise BizException(1001, "per_page 必须 >= 1", 400)

    db = get_db()
    data = EmailRecord.paginate_records(
        db, user_id=user.id, page=page, per_page=per_page,
        status_filter=status_filter, is_admin=(user.role == "admin"),
    )
    return json(data)


# ===== 4.6 邮件详情 =====
@bp.route("/records/<int:record_id>", methods=["GET"])
@login_required
def record_detail(record_id: int):
    """单条邮件详情：返回完整 content 正文

    普通用户只能查看自己创建的记录，admin 可查看全部。
    """
    user = get_current_user()
    db = get_db()
    record = EmailRecord.get_by_id(db, record_id)

    if not record:
        raise BizException(2001, "邮件记录不存在", 404)

    # 权限校验：普通用户只能看自己的
    if user.role != "admin" and record.created_by != user.id:
        raise BizException(2001, "邮件记录不存在", 404)

    return json(record.to_dict(include_content=True))


# ===== 4.7 更新邮件记录 =====
@bp.route("/records/<int:record_id>", methods=["PUT"])
@login_required
def update_record(record_id: int):
    """修改邮件主题/正文：请求体 {email_subject?, email_content?}

    普通用户只能修改自己的记录，admin 可修改全部。
    """
    user = get_current_user()
    db = get_db()
    record = EmailRecord.get_by_id(db, record_id)

    if not record:
        raise BizException(2001, "邮件记录不存在", 404)

    if user.role != "admin" and record.created_by != user.id:
        raise BizException(2001, "邮件记录不存在", 404)

    body = request.get_json(silent=True) or {}

    # API 文档用 email_subject / email_content，映射到 ORM 字段
    update_dict = {}
    if "email_subject" in body:
        update_dict["subject"] = body["email_subject"]
    if "email_content" in body:
        update_dict["content"] = body["email_content"]

    if not update_dict:
        raise BizException(1001, "请提供 email_subject 或 email_content", 400)

    updated = EmailRecord.update_record(db, record_id, update_dict)

    # 记录操作日志（不阻断主业务流程）
    record_operate_log(db, user.id, "email_update", {
        "record_id": record_id,
        "update_fields": list(update_dict.keys()),
    })

    return json(updated.to_dict(include_content=True))


# ===== 4.8 标记邮件状态 =====
@bp.route("/records/<int:record_id>", methods=["PATCH"])
@login_required
def patch_status(record_id: int):
    """修改邮件状态：请求体 {status: string}

    普通用户只能修改自己的记录，admin 可修改全部。
    """
    user = get_current_user()
    db = get_db()
    record = EmailRecord.get_by_id(db, record_id)

    if not record:
        raise BizException(2001, "邮件记录不存在", 404)

    if user.role != "admin" and record.created_by != user.id:
        raise BizException(2001, "邮件记录不存在", 404)

    body = request.get_json(silent=True) or {}
    new_status = body.get("status")
    if not new_status:
        raise BizException(1001, "status 不能为空", 400)

    valid_statuses = {"generated", "failed", "sent"}
    if new_status not in valid_statuses:
        raise BizException(1001, f"status 必须为 {valid_statuses} 之一", 400)

    updated = EmailRecord.patch_status(db, record_id, new_status)

    # 记录操作日志（不阻断主业务流程）
    record_operate_log(db, user.id, "email_mark", {
        "record_id": record_id,
        "new_status": new_status,
    })

    return json(updated.to_dict())


# ===== 4.9 删除单条邮件 =====
@bp.route("/records/<int:record_id>", methods=["DELETE"])
@login_required
def delete_record(record_id: int):
    """单条删除邮件：返回 {success: true}

    普通用户只能删除自己的记录，admin 可删除全部。
    """
    user = get_current_user()
    db = get_db()
    record = EmailRecord.get_by_id(db, record_id)

    if not record:
        raise BizException(2001, "邮件记录不存在", 404)

    if user.role != "admin" and record.created_by != user.id:
        raise BizException(2001, "邮件记录不存在", 404)

    EmailRecord.delete_single(db, record_id)

    # 记录操作日志（不阻断主业务流程）
    record_operate_log(db, user.id, "email_delete", {
        "record_id": record_id,
    })

    return json({"success": True})


# ===== 4.10 批量删除邮件 =====
@bp.route("/records", methods=["DELETE"])
@login_required
def batch_delete_records():
    """批量删除邮件：请求体 {record_ids: array<int>}

    普通用户只能删除自己的记录，admin 可删除全部。
    返回：{deleted_count: int}
    """
    user = get_current_user()
    db = get_db()
    body = request.get_json(silent=True) or {}

    record_ids = body.get("record_ids")
    if not record_ids or not isinstance(record_ids, list):
        raise BizException(1001, "record_ids 必须为非空数组", 400)

    # 权限校验：普通用户只能删自己的 → 先查出属于自己的 id 子集
    if user.role != "admin":
        own_ids = set(
            r.id for r in db.query(EmailRecord.id).filter(
                EmailRecord.id.in_(record_ids),
                EmailRecord.created_by == user.id,
            ).all()
        )
        record_ids = [rid for rid in record_ids if rid in own_ids]
        if not record_ids:
            raise BizException(2001, "无可删除的邮件记录", 404)

    deleted_count = EmailRecord.batch_delete(db, record_ids)

    # 记录操作日志（不阻断主业务流程）
    record_operate_log(db, user.id, "email_delete", {
        "record_ids": record_ids,
        "deleted_count": deleted_count,
    })

    return json({"deleted_count": deleted_count})
