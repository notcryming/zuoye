"""数据模块路由

【MVC 归属】Controller 层（表现层）
【思路】
1. POST /upload   上传 Excel → 解析 → 覆盖入库 → 返回 imported_count + quality_report
2. GET  /customers 分页查询客户（支持 gender/age/previously_insured/keyword 过滤）
3. GET  /export    导出当前筛选数据为 Excel
4. GET  /statistics 数据统计（总数/性别分布/正负样本比/年龄统计）
5. GET  /quality   数据质量报告（缺失/重复/类型）
6. GET  /visualization/<chart_type> EDA 可视化（base64 PNG）

严格对齐 auth.py 写法：BizException + json 响应；类方法封装数据操作。
"""
import io
import pandas as pd
from flask import Blueprint, request, send_file
from sqlalchemy import func
from app.core.database import get_db
from app.core.response import json, BizException
from app.core.dependencies import login_required, get_current_user
from app.models.customers import Customer
from app.utils.data_processor import parse_excel, build_quality_report, get_last_errors, get_last_raw_report
from app.utils.visualizer import render_chart, SUPPORTED_CHARTS
from app.utils.chart_cache import get_cached_chart, set_cached_chart, batch_set, clear_namespace

bp = Blueprint("data", __name__)

# 上传文件大小上限：50MB（实际 38 万行数据约 21MB，留余量）
MAX_UPLOAD_SIZE = 50 * 1024 * 1024
ALLOWED_EXTENSIONS = (".xlsx", ".xls")


def _parse_int_arg(name: str, default=None):
    """公共辅助：从 query 取整型参数，非法抛 BizException(1001)"""
    val = request.args.get(name)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except ValueError:
        raise BizException(1001, f"参数 {name} 必须为整数", 400)


def _parse_filters() -> dict:
    """解析筛选参数（customers 分页 / export 复用）"""
    return {
        "gender": request.args.get("gender") or None,
        "age_min": _parse_int_arg("age_min"),
        "age_max": _parse_int_arg("age_max"),
        "previously_insured": _parse_int_arg("previously_insured"),
        "keyword": request.args.get("keyword") or None,
    }


# ===== 2.1 上传 Excel 数据 =====
@bp.route("/upload", methods=["POST"])
@login_required
def upload():
    """上传 Excel：取文件 → 校验大小/格式 → 解析 → 覆盖入库 → 返回质量报告

    逐字思路：
    1. request.files 取 file；没有 → BizException 1001
    2. 校验扩展名 + 大小（50MB）
    3. parse_excel 解析（失败内部抛 2002）
    4. Customer.bulk_create 覆盖入库（内部清旧数据）
    5. 组装 imported_count + quality_report 返回
    """
    file = request.files.get("file")
    if not file:
        raise BizException(1001, "未上传文件，请选择 Excel 文件", 400)

    # 校验扩展名
    if not file.filename.lower().endswith(ALLOWED_EXTENSIONS):
        raise BizException(1001, "仅支持 .xlsx/.xls 格式", 400)

    # 校验大小
    file.stream.seek(0, 2)
    size = file.stream.tell()
    file.stream.seek(0)
    if size > MAX_UPLOAD_SIZE:
        raise BizException(1001, "文件过大，限制 50MB", 400)

    # 解析 Excel
    rows = parse_excel(file)
    if not rows:
        raise BizException(2002, "解析后无有效数据行", 400)

    # 覆盖入库
    user = get_current_user()
    db = get_db()
    imported_count = Customer.bulk_create(db, rows, user.id)

    # 质量报告：优先用"原始数据"报告（缺失值才真实反映原始数据）
    quality_report = get_last_raw_report() or build_quality_report(rows)
    quality_report["invalid_rows"] = get_last_errors()  # 附非法行明细

    # ===== 缓存：上传后同步预渲染 4 张 EDA 图，清空旧 ML 图 =====
    # 为什么"同步"而不是"异步线程"：38 万行渲染 4 张图约 2~3 秒，
    # 同步渲染可把缓存写好再返回，用户点"数据概览"时秒出；
    # 失败不阻断主流程（try/except 兜底），下次进入仍走实时渲染。
    try:
        clear_namespace("eda")
        clear_namespace("ml")  # 数据变更，旧模型图表全部失效
        all_customer_rows = Customer.all_rows(db)
        cache_items = {}
        for ct in SUPPORTED_CHARTS:
            try:
                cache_items[ct] = render_chart(ct, all_customer_rows)
            except Exception:
                pass
        batch_set("eda", cache_items)
    except Exception:
        pass  # 缓存失败静默，不影响上传响应

    return json({
        "imported_count": imported_count,
        "quality_report": quality_report,
    })


# ===== 2.2 客户列表分页 =====
@bp.route("/customers", methods=["GET"])
@login_required
def customers():
    """分页查询客户：page/per_page + 筛选条件，返回 API 文档 0.3 分页结构"""
    page = _parse_int_arg("page", default=1)
    per_page = _parse_int_arg("per_page", default=50)
    if page < 1:
        raise BizException(1001, "page 必须 >= 1", 400)
    if per_page < 1:
        raise BizException(1001, "per_page 必须 >= 1", 400)

    filters = _parse_filters()
    db = get_db()
    data = Customer.paginate(db, page, per_page, filters)
    return json(data)


# ===== 2.3 数据导出 =====
@bp.route("/export", methods=["GET"])
@login_required
def export():
    """导出当前筛选条件下的全量客户为 Excel（不分页）"""
    filters = _parse_filters()
    db = get_db()

    # 复用模型的过滤逻辑，取全量（不分页）
    query = Customer.apply_filters(db.query(Customer), filters)
    customers_list = query.order_by(Customer.id).all()
    rows = [c.to_dict() for c in customers_list]

    if not rows:
        raise BizException(2001, "当前筛选无数据可导出", 404)

    # 写入 Excel
    output = io.BytesIO()
    pd.DataFrame(rows).to_excel(output, index=False)
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="customers.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ===== 2.3 数据概览统计 =====
@bp.route("/statistics", methods=["GET"])
@login_required
def statistics():
    """数据统计：总数 / 性别分布 / 正负样本比 / 年龄统计

    响应 data 对齐 API 文档 2.3 statistics 结构：
    { total, gender_distribution, response_distribution, age_stats }
    """
    db = get_db()

    total = Customer.count(db)
    if total == 0:
        return json({
            "total": 0,
            "gender_distribution": {},
            "response_distribution": {},
            "age_stats": {"min": 0, "max": 0, "avg": 0},
        })

    # 性别分布
    gender_rows = db.query(Customer.gender, func.count(Customer.id)).group_by(Customer.gender).all()
    gender_distribution = {g: c for g, c in gender_rows}

    # 正负样本分布（response 0/1）
    resp_rows = db.query(Customer.response, func.count(Customer.id)).group_by(Customer.response).all()
    response_distribution = {str(r): c for r, c in resp_rows}

    # 年龄统计
    age_row = db.query(
        func.min(Customer.age),
        func.max(Customer.age),
        func.avg(Customer.age),
    ).first()
    age_stats = {
        "min": int(age_row[0]) if age_row[0] is not None else 0,
        "max": int(age_row[1]) if age_row[1] is not None else 0,
        "avg": round(float(age_row[2]), 2) if age_row[2] is not None else 0,
    }

    return json({
        "total": total,
        "gender_distribution": gender_distribution,
        "response_distribution": response_distribution,
        "age_stats": age_stats,
    })


# ===== 2.4 数据质量报告 =====
@bp.route("/quality", methods=["GET"])
@login_required
def quality():
    """数据质量报告：返回 {total_rows, total_cols, missing_values, duplicates, dtypes}

    响应 data 对齐 API 文档 2.4，无数据时返回空结构（total_rows=0）。
    """
    db = get_db()
    report = Customer.quality_report(db)
    return json(report)


# ===== 2.5 EDA 可视化 =====
@bp.route("/visualization/<chart_type>", methods=["GET"])
@login_required
def visualization(chart_type: str):
    """EDA 可视化：优先读缓存 → 未命中再渲染 → 写缓存

    逐字思路：
    1. get_cached_chart 命中 → 直接返回，秒出图
    2. 未命中 → 查全表 + render_chart
    3. 渲染结果写入缓存，下次打开直接命中
    """
    # 1. 查缓存（EDA 缓存无过期时间，数据变更时由 upload clear_namespace 触发失效）
    cached = get_cached_chart("eda", chart_type)
    if cached:
        return json({
            "chart_type": chart_type,
            "image_base64": cached,
            "format": "png",
            "cached": True,
        })

    db = get_db()
    rows = Customer.all_rows(db)
    if not rows:
        raise BizException(2001, "暂无数据，请先上传 Excel", 404)

    image_base64 = render_chart(chart_type, rows)

    # 写缓存（单图，避免并发打开时重复渲染）
    try:
        set_cached_chart("eda", chart_type, image_base64)
    except Exception:
        pass

    return json({
        "chart_type": chart_type,
        "image_base64": image_base64,
        "format": "png",
        "cached": False,
    })
