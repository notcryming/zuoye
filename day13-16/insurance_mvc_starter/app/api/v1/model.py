"""模型模块路由

【MVC 归属】Controller 层（表现层）
【思路】
1. POST /train          训练三模型（admin）→ 选优 → 建实验记录
2. GET  /experiments    实验记录分页（支持 model_name 过滤）
3. GET  /best           获取当前最优模型
4. POST /predict        全量客户预测 → 回写 predicted_prob
5. POST /predict_upload 上传 Excel 离线预测（不入库）
6. GET  /visualization/<chart_type> 模型评估可视化（ROC/混淆矩阵/特征重要性/指标对比）
7. GET  /export/<model_name>  导出 .joblib 模型文件（admin）
8. POST /import         导入 .joblib 模型文件（admin）

严格对齐 auth.py / data.py 写法：BizException + json 响应；
@login_required / @role_required("admin") 权限装饰器。
"""
import os
from flask import Blueprint, request, send_file
from app.core.database import get_db
from app.core.response import json, BizException
from app.core.dependencies import login_required, role_required, get_current_user
from app.core.config import settings
from app.models.experiment import Experiment
from app.services.ml_service import (
    train_model, predict_all, predict_upload_excel, generate_visualization,
    import_model as import_model_service,
)

bp = Blueprint("model", __name__)


def _parse_int_arg(name: str, default=None):
    """公共辅助：从 query 取整型参数，非法抛 BizException(1001)"""
    val = request.args.get(name)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except ValueError:
        raise BizException(1001, f"参数 {name} 必须为整数", 400)


def _get_model_dir() -> str:
    """获取模型存储目录的绝对路径，不存在则创建"""
    model_dir = os.path.abspath(settings.MODEL_DIR)
    os.makedirs(model_dir, exist_ok=True)
    return model_dir


# ===== 3.1 训练模型 =====
@bp.route("/train", methods=["POST"])
@role_required("admin")
def train():
    """模型训练：取参数 → 调 ml_service.train_model → 返回 {best_model, results}

    请求体（可选，不传用默认值）：
    - models: list[str]  null=训练全部三算法
    - test_size: float   默认 0.2
    - random_state: int  默认 42
    - params: object     按模型名覆盖超参
    """
    user = get_current_user()
    db = get_db()

    train_params = request.get_json(silent=True) or {}
    result = train_model(db, train_params, user.id)
    return json(result)


# ===== 3.2 实验记录分页 =====
@bp.route("/experiments", methods=["GET"])
@login_required
def experiments():
    """实验记录分页查询：page/per_page + model_name 过滤"""
    page = _parse_int_arg("page", default=1)
    per_page = _parse_int_arg("per_page", default=50)
    if page < 1:
        raise BizException(1001, "page 必须 >= 1", 400)
    if per_page < 1:
        raise BizException(1001, "per_page 必须 >= 1", 400)

    model_name = request.args.get("model_name") or None

    db = get_db()
    data = Experiment.paginate_list(db, page, per_page, model_name)
    return json(data)


# ===== 3.3 获取最佳模型 =====
@bp.route("/best", methods=["GET"])
@login_required
def best():
    """获取当前最优模型：返回 {model_name, roc_auc, experiment_id}"""
    db = get_db()
    exp = Experiment.get_best_model(db)
    if not exp:
        raise BizException(3002, "无最佳模型，请先训练", 400)

    return json({
        "model_name": exp.model_name,
        "roc_auc": exp.roc_auc,
        "experiment_id": exp.id,
    })


# ===== 3.4 全量预测 =====
@bp.route("/predict", methods=["POST"])
@login_required
def predict():
    """全量客户预测：加载模型 → predict_proba → 回写 predicted_prob

    请求体（可选）：{ model_name: string }（缺省用最佳模型）
    """
    user = get_current_user()
    db = get_db()
    body = request.get_json(silent=True) or {}
    model_name = body.get("model_name")

    result = predict_all(db, model_name, user.id)
    return json(result)


# ===== 3.5 上传数据预测 =====
@bp.route("/predict_upload", methods=["POST"])
@login_required
def predict_upload():
    """上传 Excel 离线预测：解析 → 预测 → 返回结果（不入库）

    请求体：multipart/form-data
    - file: Excel 文件（必填）
    - model: 模型名（可选，缺省用最佳模型）
    """
    file = request.files.get("file")
    if not file:
        raise BizException(1001, "未上传文件，请选择 Excel 文件", 400)

    if not file.filename.lower().endswith((".xlsx", ".xls")):
        raise BizException(1001, "仅支持 .xlsx/.xls 格式", 400)

    model_name = request.form.get("model") or None

    db = get_db()
    result = predict_upload_excel(db, file, model_name)
    return json(result)


# ===== 3.6 模型评估可视化 =====
@bp.route("/visualization/<chart_type>", methods=["GET"])
@login_required
def visualization(chart_type: str):
    """模型评估可视化：返回 {chart_type, image_base64, format:"png"}

    路径参数：chart_type ∈ roc_curve / metrics_comparison / confusion_matrix / feature_importance
    查询参数：model（confusion_matrix / feature_importance 必填）
    """
    model_name = request.args.get("model") or None

    # confusion_matrix / feature_importance 必须指定 model
    if chart_type in ("confusion_matrix", "feature_importance") and not model_name:
        raise BizException(1001, f"{chart_type} 需要指定 model 参数", 400)

    db = get_db()
    image_base64 = generate_visualization(db, chart_type, model_name)

    return json({
        "chart_type": chart_type,
        "image_base64": image_base64,
        "format": "png",
    })


# ===== 3.7 导出模型文件 =====
@bp.route("/export/<model_name>", methods=["GET"])
@role_required("admin")
def export_model(model_name: str):
    """导出 .joblib 模型文件：返回二进制文件流

    路径参数：model_name（如 xgboost / logistic_regression / random_forest）
    """
    model_dir = _get_model_dir()
    model_path = os.path.join(model_dir, f"{model_name}.joblib")

    # 防路径穿越：确保解析后的绝对路径的父目录就是 model_dir
    abs_model_path = os.path.abspath(model_path)
    if os.path.dirname(abs_model_path) != model_dir:
        raise BizException(1001, "非法的模型名", 400)

    if not os.path.exists(model_path):
        raise BizException(3002, f"模型文件不存在：{model_name}", 400)

    return send_file(
        model_path,
        as_attachment=True,
        download_name=f"{model_name}.joblib",
        mimetype="application/octet-stream",
    )


# ===== 3.8 导入模型文件 =====
@bp.route("/import", methods=["POST"])
@role_required("admin")
def import_model():
    """导入 .joblib 模型文件：校验 → 保存到 MODEL_DIR → 记录日志 → 返回 {model_name, path}

    请求体：multipart/form-data
    - file: .joblib 文件（必填）
    """
    file = request.files.get("file")
    if not file:
        raise BizException(1001, "未上传文件，请选择 .joblib 模型文件", 400)

    user = get_current_user()
    db = get_db()
    result = import_model_service(db, file, user.id)
    return json(result)
