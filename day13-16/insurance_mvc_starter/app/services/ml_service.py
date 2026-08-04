"""机器学习核心业务服务

【MVC 归属】业务层（Service 层）
【思路】
1. train_model：LR/XGBoost/RF 三模型训练，分层拆分、不平衡权重、标准化仅训练集 fit、
   ROC-AUC 评估、自动标记最优模型、joblib 存储 model+scaler 捆绑文件
2. predict_all：加载最优模型，全量客户特征标准化预测正类概率，回写 predicted_prob
3. predict_upload_excel：解析上传 Excel，批量输出预测结果不入库
4. generate_visualization：读取实验 params 内图表 json，返回 base64 图片字符串

严格遵循 AI 技术方案 2.x：
- stratify=y 分层抽样
- StandardScaler 仅训练集 fit，测试集/预测集只 transform（防数据泄漏）
- XGBoost 用 scale_pos_weight，LR/RF 用 class_weight="balanced"
- model + scaler 一起 joblib.dump，预测时一起加载
"""
import os
import io
import json as json_lib
import numpy as np
import pandas as pd
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, roc_curve, confusion_matrix,
)
import xgboost as xgb
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.response import BizException
from app.core.dependencies import record_operate_log
from app.models.customers import Customer
from app.models.experiment import Experiment
from app.utils.data_processor import (
    encode_raw_features, FEATURE_COLUMNS, ORIGINAL_FEATURE_COLUMNS, LABEL_COLUMN,
    COLUMN_MAP, NUMERIC_COLUMNS, INT_COLUMNS,
)
from app.utils.visualizer import render_ml_chart, ML_SUPPORTED_CHARTS
from app.utils.chart_cache import batch_set, clear_namespace, invalidate_key, get_cached_chart, set_cached_chart

# 三种模型名 → 中文显示（对齐 API 文档）
ALL_MODEL_NAMES = ["logistic_regression", "xgboost", "random_forest"]


def _get_model_dir() -> str:
    """获取模型存储目录的绝对路径，不存在则创建"""
    model_dir = os.path.abspath(settings.MODEL_DIR)
    os.makedirs(model_dir, exist_ok=True)
    return model_dir


def _get_model(model_name: str, params: dict, n_neg: int, n_pos: int):
    """根据模型名创建模型实例，配置不平衡处理参数

    逐字思路：
    1. logistic_regression → class_weight="balanced"
    2. random_forest → class_weight="balanced"
    3. xgboost → scale_pos_weight = n_neg / n_pos
    4. params 里的超参覆盖默认值
    """
    extra = params.get(model_name, {}) if params else {}

    if model_name == "logistic_regression":
        defaults = {"max_iter": 1000, "class_weight": "balanced", "random_state": 42}
        defaults.update(extra)
        return LogisticRegression(**defaults)

    elif model_name == "random_forest":
        defaults = {"n_estimators": 100, "class_weight": "balanced", "random_state": 42}
        defaults.update(extra)
        return RandomForestClassifier(**defaults)

    elif model_name == "xgboost":
        spw = n_neg / n_pos if n_pos > 0 else 1
        defaults = {
            "n_estimators": 100,
            "scale_pos_weight": spw,
            "random_state": 42,
            "eval_metric": "logloss",
        }
        defaults.update(extra)
        return xgb.XGBClassifier(**defaults)

    else:
        raise BizException(1001, f"未知模型名：{model_name}", 400)


def _get_feature_importance(model, model_name: str) -> dict:
    """提取特征重要性（LR 用 coef_ 绝对值，RF/XGBoost 用 feature_importances_）"""
    if model_name == "logistic_regression":
        importances = np.abs(model.coef_[0])
    else:
        importances = model.feature_importances_

    return {name: float(val) for name, val in zip(FEATURE_COLUMNS, importances)}


# 极度不平衡阈值：训练集正负比 > 5:1 视为极度不平衡，需先重采样
IMBALANCE_RATIO_THRESHOLD = 5.0


def _check_balance(y: np.ndarray) -> tuple:
    """检查标签平衡性

    逐字思路：
    1. 统计正负样本数
    2. 计算不平衡比 = 多数类 / 少数类
    3. ratio > IMBALANCE_RATIO_THRESHOLD 视为极度不平衡
    4. 返回 (ratio, is_extreme, n_pos, n_neg)
    """
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())
    if n_pos == 0 or n_neg == 0:
        return float("inf"), True, n_pos, n_neg
    ratio = max(n_pos, n_neg) / min(n_pos, n_neg)
    return ratio, ratio > IMBALANCE_RATIO_THRESHOLD, n_pos, n_neg


def _resample(X, y, random_state: int = 42) -> tuple:
    """随机过采样少数类，使训练集达到平衡

    【为什么用随机过采样而非 SMOTE】
    - SMOTE 需引入 imblearn 依赖，且 38 万行生成合成样本较慢；
    - 随机过采样零依赖（仅 numpy），速度快，配合算法层 class_weight/scale_pos_weight
      双重应对不平衡，教学版足够。

    【注意】X 可能是 pandas DataFrame（train_test_split 对 DataFrame 仍返回 DataFrame），
    用整数索引时必须走 .iloc 行索引，不能直接 X[idx]（按列取会抛 KeyError）。

    逐字思路：
    1. 找出少数类与多数类
    2. 从少数类索引有放回采样到与多数类相同数量
    3. 与多数类索引拼接 → shuffle 打乱顺序
    4. X 若为 DataFrame 用 iloc，否则用 numpy 切片 → 返回 (X_res, y_res)
    """
    n_pos = int((y == 1).sum())
    n_neg = int((y == 0).sum())

    if n_pos == n_neg:
        return X, y

    if n_pos > n_neg:
        majority_label, minority_label = 1, 0
        n_majority = n_pos
    else:
        majority_label, minority_label = 0, 1
        n_majority = n_neg

    rng = np.random.RandomState(random_state)
    majority_idx = np.where(y == majority_label)[0]
    minority_idx = np.where(y == minority_label)[0]
    # 有放回采样少数类到与多数类等量
    oversample_idx = rng.choice(minority_idx, size=n_majority, replace=True)

    all_idx = np.concatenate([majority_idx, oversample_idx])
    rng.shuffle(all_idx)

    # DataFrame 走 .iloc 行索引，numpy 直接切片
    if isinstance(X, pd.DataFrame):
        X_res = X.iloc[all_idx]
    else:
        X_res = X[all_idx]
    # y 是 ndarray 或 Series，两种写法都兼容
    if isinstance(y, pd.Series):
        y_res = y.iloc[all_idx].values
    else:
        y_res = y[all_idx]
    return X_res, y_res


def train_model(db: Session, train_params: dict, user_id: int) -> dict:
    """三模型训练：分层拆分 → 平衡检查/重采样 → 标准化 → 训练 → 评估 → 选优 → 持久化 → 建实验记录

    逐字思路：
    1. 查全量客户数据 → 无数据抛 BizException(2001)
    2. encode_raw_features 特征编码（含 id 剔除、保费分箱）→ 拆 X/y
    3. stratify=y 分层拆分训练/测试集
    4. 检查训练集 Response 平衡性，极度不平衡则对训练集随机过采样
       （只动训练集，测试集保持原始分布，评估才真实）
    5. StandardScaler 仅 fit 训练集 → transform 训练集和测试集
    6. 逐模型训练 → 评估 5 指标 → 算 ROC/混淆矩阵/特征重要性 → joblib 存 model+scaler
    7. 建实验记录，params 存可视化 JSON
    8. 按 ROC-AUC 选最优 → clear_old_best → 标记 is_best
    9. 返回 {best_model, results}
    """
    # 1. 取数据
    rows = Customer.all_rows(db)
    if not rows:
        raise BizException(2001, "暂无客户数据，请先上传 Excel", 400)

    df = pd.DataFrame(rows)

    # 2. 特征编码
    X = encode_raw_features(df)
    y = df[LABEL_COLUMN].astype(int).values

    # 3. 分层拆分
    test_size = train_params.get("test_size", 0.2)
    random_state = train_params.get("random_state", 42)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # 4. 平衡检查 + 重采样（仅训练集）
    ratio, is_extreme, _, _ = _check_balance(y_train)
    resampled = False
    if is_extreme:
        X_train, y_train = _resample(X_train, y_train, random_state)
        resampled = True

    # 5. 标准化（仅训练集 fit）
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)  # 测试集只 transform，防泄漏

    # 6. 不平衡权重参数（重采样后需基于新的 y_train 重新统计）
    n_neg = int((y_train == 0).sum())
    n_pos = int((y_train == 1).sum())

    # 6. 确定要训练的模型
    model_names = train_params.get("models") or ALL_MODEL_NAMES
    params_override = train_params.get("params") or {}

    model_dir = _get_model_dir()

    # 7. 逐模型训练
    results = {}
    experiments = []
    all_metrics = {}

    for model_name in model_names:
        try:
            model = _get_model(model_name, params_override, n_neg, n_pos)
            model.fit(X_train_scaled, y_train)

            # 预测
            y_pred = model.predict(X_test_scaled)
            y_proba = model.predict_proba(X_test_scaled)[:, 1]  # 正类概率

            # 评估指标
            metrics = {
                "accuracy": float(accuracy_score(y_test, y_pred)),
                "precision": float(precision_score(y_test, y_pred, zero_division=0)),
                "recall": float(recall_score(y_test, y_pred, zero_division=0)),
                "f1_score": float(f1_score(y_test, y_pred, zero_division=0)),
                "roc_auc": float(roc_auc_score(y_test, y_proba)),
            }
            results[model_name] = metrics
            all_metrics[model_name] = metrics

            # 可视化数据
            fpr, tpr, _ = roc_curve(y_test, y_proba)
            cm = confusion_matrix(y_test, y_pred).tolist()
            feature_imp = _get_feature_importance(model, model_name)

            params_json = json_lib.dumps({
                "roc": {
                    "fpr": fpr.tolist(),
                    "tpr": tpr.tolist(),
                    "auc": metrics["roc_auc"],
                },
                "confusion_matrix": cm,
                "feature_importances": feature_imp,
                "model_name": model_name,
            })

            # 持久化 model + scaler
            model_path = os.path.join(model_dir, f"{model_name}.joblib")
            joblib.dump({"model": model, "scaler": scaler}, model_path)

            # 建实验记录
            exp = Experiment.create_record(db, {
                "model_name": model_name,
                "accuracy": metrics["accuracy"],
                "precision": metrics["precision"],
                "recall": metrics["recall"],
                "f1_score": metrics["f1_score"],
                "roc_auc": metrics["roc_auc"],
                "params": params_json,
                "model_path": model_path,
                "is_best": False,
                "created_by": user_id,
            })
            experiments.append(exp)

        except BizException:
            raise
        except Exception as e:
            raise BizException(3001, f"模型 {model_name} 训练失败：{e}", 500)

    # 8. 更新每个实验的 params，补充 all_metrics（供 metrics_comparison 可视化）
    all_metrics_json = all_metrics
    for exp in experiments:
        params_data = json_lib.loads(exp.params) if exp.params else {}
        params_data["all_metrics"] = all_metrics_json
        exp.params = json_lib.dumps(params_data)
    db.commit()

    # 9. 选最优模型（按 ROC-AUC 降序）
    best_model_name = max(results, key=lambda k: results[k]["roc_auc"])

    # 清旧 best → 标记新 best
    Experiment.clear_old_best(db)
    best_exp = experiments[[e.model_name for e in experiments].index(best_model_name)]
    best_exp.is_best = True
    db.commit()

    # 记录操作日志（不阻断主业务流程）
    record_operate_log(db, user_id, "model_training", {
        "best_model": best_model_name,
        "models_trained": list(results.keys()),
        "test_size": test_size,
        "random_state": random_state,
        "imbalance_ratio": round(float(ratio), 4),
        "resampled": resampled,
        "train_size_after_resample": int(len(y_train)),
        "results": results,
    })

    # ===== 缓存：训练完成后预渲染所有 ML 图表（每张模型 3 图 + 1 张指标对比）=====
    # 失败不阻断主流程
    try:
        clear_namespace("ml")
        cache_items = {}
        # 每个模型：ROC / 混淆矩阵 / 特征重要性
        for exp in experiments:
            try:
                params_data = json_lib.loads(exp.params) if exp.params else {}
                params_data["model_name"] = exp.model_name
                m = exp.model_name
                for ct in ["roc_curve", "confusion_matrix", "feature_importance"]:
                    if ct in ML_SUPPORTED_CHARTS:
                        cache_items[f"{ct}:{m}"] = render_ml_chart(ct, params_data)
            except Exception:
                pass
        # 多模型指标对比图（metrics_comparison 不带模型后缀）
        try:
            cache_items["metrics_comparison"] = render_ml_chart(
                "metrics_comparison", {"all_metrics": all_metrics}
            )
        except Exception:
            pass
        batch_set("ml", cache_items)
    except Exception:
        pass

    return {
        "best_model": best_model_name,
        "results": results,
        "balance_info": {
            "imbalance_ratio": round(float(ratio), 4),
            "resampled": resampled,
            "threshold": IMBALANCE_RATIO_THRESHOLD,
        },
    }


def _load_model_bundle(model_name: str = None, db: Session = None) -> tuple:
    """加载模型 + scaler 捆绑文件

    逐字思路：
    1. model_name 为空 → 取最优模型实验记录 → 从 model_path 加载
    2. model_name 不为空 → 直接从 MODEL_DIR/{model_name}.joblib 加载
    3. 文件不存在 → BizException(3002)
    4. 返回 (model, scaler, actual_model_name)
    """
    model_dir = _get_model_dir()

    if model_name:
        # 指定模型名 → 直接找文件
        model_path = os.path.join(model_dir, f"{model_name}.joblib")
        actual_name = model_name
    else:
        # 未指定 → 取最优模型
        if db is None:
            raise BizException(3002, "未指定模型名且无法查询最优模型", 400)
        best_exp = Experiment.get_best_model(db)
        if not best_exp:
            raise BizException(3002, "无最佳模型，请先训练", 400)
        model_path = best_exp.model_path
        actual_name = best_exp.model_name

    if not model_path or not os.path.exists(model_path):
        raise BizException(3002, f"模型文件不存在：{actual_name}", 400)

    try:
        bundle = joblib.load(model_path)
    except Exception as e:
        raise BizException(3002, f"模型加载失败：{e}", 500)

    return bundle["model"], bundle["scaler"], actual_name


def predict_all(db: Session, model_name: str = None, user_id: int = None) -> dict:
    """全量客户预测：加载模型 → 特征编码 → scaler.transform → predict_proba → 回写 DB

    逐字思路：
    1. 加载模型 + scaler（model_name 为空用最优模型）
    2. 查全量客户 → 无数据抛 BizException(2001)
    3. encode_raw_features 编码 → scaler.transform（禁止 fit！）
    4. predict_proba 取正类概率 → 回写 customers.predicted_prob
    5. 返回 {model_name, predicted_count}
    """
    # 1. 加载模型
    model, scaler, actual_name = _load_model_bundle(model_name, db)

    # 2. 取数据
    rows = Customer.all_rows(db)
    if not rows:
        raise BizException(2001, "暂无客户数据，请先上传 Excel", 400)

    df = pd.DataFrame(rows)

    # 3. 特征编码 + 标准化（只 transform，不 fit）
    X = encode_raw_features(df)
    X_scaled = scaler.transform(X)

    # 4. 预测正类概率
    proba = model.predict_proba(X_scaled)[:, 1]

    # 5. 回写 DB
    customers = db.query(Customer).order_by(Customer.id).all()
    for customer, prob in zip(customers, proba):
        customer.predicted_prob = float(prob)
    db.commit()

    # 记录操作日志（不阻断主业务流程）
    record_operate_log(db, user_id, "prediction", {
        "model_name": actual_name,
        "predicted_count": len(customers),
    })

    return {
        "model_name": actual_name,
        "predicted_count": len(customers),
    }


def predict_upload_excel(db: Session, file, model_name: str = None) -> dict:
    """上传 Excel 离线预测：解析 → 编码 → 标准化 → 预测 → 返回结果（不入库）

    逐字思路：
    1. 加载模型 + scaler
    2. 读 Excel → 保留原始数据（id 等） + 编码特征
    3. scaler.transform → predict_proba
    4. 组装统计 + 预测明细返回
    """
    # 1. 加载模型
    model, scaler, actual_name = _load_model_bundle(model_name, db)

    # 2. 读 Excel
    try:
        stream = io.BytesIO(file.read())
        df = pd.read_excel(stream)
    except Exception as e:
        raise BizException(2002, f"Excel 解析失败：{e}", 400)

    if df.empty:
        raise BizException(2002, "Excel 文件为空", 400)

    # 列名转小写下划线
    rename_map = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # 校验原始特征列（编码前；annual_premium 会被 encode_raw_features 分箱为 annual_premium_bin）
    missing = set(ORIGINAL_FEATURE_COLUMNS) - set(df.columns)
    if missing:
        raise BizException(2002, f"缺少必要特征列：{','.join(sorted(missing))}", 400)

    # 数值列转换
    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # 剔除非法行
    feature_numeric = [c for c in NUMERIC_COLUMNS if c in df.columns and c != "response"]
    df = df.dropna(subset=feature_numeric).copy()

    for col in INT_COLUMNS:
        if col in df.columns and col != "response":
            df[col] = df[col].astype(int)

    # 3. 特征编码 + 标准化
    X = encode_raw_features(df)
    X_scaled = scaler.transform(X)

    # 4. 预测
    proba = model.predict_proba(X_scaled)[:, 1]

    # 5. 组装结果
    predictions = []
    for idx, (_, row) in enumerate(df.iterrows()):
        pred = {
            "id": int(row["id"]) if "id" in row else idx + 1,
            "predicted_prob": float(proba[idx]),
            "predicted_label": int(proba[idx] >= 0.5),
        }
        # 附带原始特征信息（供前端展示）
        for col in ["gender", "age", "annual_premium", "vehicle_age", "vehicle_damage"]:
            if col in row:
                pred[col] = row[col]
        if "response" in row:
            pred["actual_response"] = int(row["response"])
        predictions.append(pred)

    # 统计
    proba_arr = np.array(proba)
    statistics = {
        "total": len(predictions),
        "positive_count": int((proba_arr >= 0.5).sum()),
        "negative_count": int((proba_arr < 0.5).sum()),
        "avg_prob": float(proba_arr.mean()),
        "max_prob": float(proba_arr.max()),
        "min_prob": float(proba_arr.min()),
    }

    return {
        "model_name": actual_name,
        "total_count": len(predictions),
        "statistics": statistics,
        "predictions": predictions,
    }


def generate_visualization(db: Session, chart_type: str, model_name: str = None) -> str:
    """模型评估可视化：优先读缓存 → 未命中再画图 → 写缓存

    逐字思路：
    1. 缓存 key 规则：metrics_comparison → "metrics_comparison"
                  单模型图 → "roc_curve:<model>" / "confusion_matrix:<model>" / ...
    2. 命中则直接返回缓存 base64（秒级）
    3. 未命中走原逻辑，渲染后写入缓存
    """
    # 1. 解析 cache_key
    if chart_type == "metrics_comparison":
        cache_key = "metrics_comparison"
        resolved_model = None
    else:
        # 单模型图：先确定实际模型名
        if model_name:
            exp = Experiment.get_by_name(db, model_name)
        else:
            exp = Experiment.get_best_model(db)
        if not exp:
            raise BizException(3002, "无模型实验记录，请先训练模型", 400)
        resolved_model = exp.model_name
        cache_key = f"{chart_type}:{resolved_model}"

    # 2. 查缓存（无过期时间，训练完成/上传数据时 clear_namespace 触发失效）
    cached = get_cached_chart("ml", cache_key)
    if cached:
        return cached

    # 3. 未命中 → 实时渲染
    if chart_type == "metrics_comparison":
        batch = Experiment.get_latest_batch(db, limit=3)
        if not batch:
            raise BizException(3002, "无训练实验记录，请先训练模型", 400)
        metrics_map = {}
        for exp in batch:
            metrics_map[exp.model_name] = {
                "accuracy": exp.accuracy,
                "precision": exp.precision,
                "recall": exp.recall,
                "f1_score": exp.f1_score,
                "roc_auc": exp.roc_auc,
            }
        data = {"all_metrics": metrics_map}
        image_base64 = render_ml_chart(chart_type, data)
    else:
        # resolved_model 已经在上面查过了，再查一次取完整 params
        exp = Experiment.get_by_name(db, resolved_model)
        if not exp:
            raise BizException(3002, "无模型实验记录，请先训练模型", 400)
        try:
            data = json_lib.loads(exp.params) if exp.params else {}
        except json_lib.JSONDecodeError:
            raise BizException(3002, "实验记录 params 解析失败", 500)
        data["model_name"] = resolved_model
        image_base64 = render_ml_chart(chart_type, data)

    # 4. 写缓存（兜底，不阻断）
    try:
        set_cached_chart("ml", cache_key, image_base64)
    except Exception:
        pass

    return image_base64


def import_model(db: Session, file, user_id: int) -> dict:
    """导入 .joblib 模型文件：校验 → 保存 → 记录操作日志

    逐字思路：
    1. 校验文件格式（.joblib 后缀）
    2. secure_filename 过滤路径穿越（如 ../../etc/passwd.joblib → etc_passwd.joblib）
    3. 从文件名提取模型名 → 保存到 MODEL_DIR
    4. 记录 model_import 操作日志（不阻断主业务流程）
    5. 返回 {model_name, path}
    """
    from werkzeug.utils import secure_filename

    if not file.filename.lower().endswith(".joblib"):
        raise BizException(1001, "仅支持 .joblib 格式", 400)

    # secure_filename 过滤路径穿越
    safe_name = secure_filename(file.filename)
    if not safe_name:
        raise BizException(1001, "文件名非法", 400)

    # 从文件名提取模型名（如 xgboost.joblib → xgboost）
    model_name = os.path.splitext(safe_name)[0]

    model_dir = _get_model_dir()
    model_path = os.path.join(model_dir, f"{model_name}.joblib")
    file.save(model_path)

    # 记录操作日志（不阻断主业务流程）
    record_operate_log(db, user_id, "model_import", {
        "model_name": model_name,
        "model_path": model_path,
    })

    return {
        "model_name": model_name,
        "path": model_path,
    }
