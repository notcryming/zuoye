"""日志模块路由

【MVC 归属】Controller 层（表现层）
【思路】
1. GET /logs  操作日志分页查询（仅 admin）→ 支持 user_id / action 过滤

严格对齐 auth.py / data.py / model.py 写法：BizException + json 响应；
@login_required + @role_required("admin") 双重鉴权装饰器。

为什么日志查询仅 admin 可访问？
  操作日志含全量用户的行为审计数据（含其他用户 ID、操作详情），
  普通用户无权查看他人操作记录，仅 admin 可审计全量日志。
"""
from flask import Blueprint, request
from app.core.database import get_db
from app.core.response import json, BizException
from app.core.dependencies import login_required, role_required
from app.models.operation_log import OperationLog, VALID_ACTIONS

bp = Blueprint("log", __name__)


def _parse_int_arg(name: str, default=None):
    """公共辅助：从 query 取整型参数，非法抛 BizException(1001)"""
    val = request.args.get(name)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except ValueError:
        raise BizException(1001, f"参数 {name} 必须为整数", 400)


# ===== 5.1 操作日志查询 =====
@bp.route("/logs", methods=["GET"])
@login_required
@role_required("admin")
def logs():
    """操作日志分页查询：仅 admin 可访问

    查询参数：
    - page: int       页码（默认 1）
    - per_page: int   每页条数（默认 50）
    - user_id: int    按用户过滤（可选）
    - action: string  按操作类型过滤（可选，须为合法枚举值）
    """
    page = _parse_int_arg("page", default=1)
    per_page = _parse_int_arg("per_page", default=50)
    filter_user_id = _parse_int_arg("user_id", default=None)
    filter_action = request.args.get("action") or None

    if page < 1:
        raise BizException(1001, "page 必须 >= 1", 400)
    if per_page < 1:
        raise BizException(1001, "per_page 必须 >= 1", 400)

    # action 合法性校验
    if filter_action and filter_action not in VALID_ACTIONS:
        raise BizException(1001, f"非法 action 值，允许值：{VALID_ACTIONS}", 400)

    db = get_db()
    data = OperationLog.paginate_logs(
        db, page=page, per_page=per_page,
        filter_user_id=filter_user_id, filter_action=filter_action,
    )
    return json(data)
