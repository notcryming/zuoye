"""EDA 可视化工具

【MVC 归属】工具层（纯函数，不依赖业务层 / Flask）
【思路】
1. render_chart(chart_type, rows) -> str：按 chart_type 画图 → base64 PNG 字符串
2. 四种图表：response_distribution / gender_response / age_distribution / premium_distribution
3. 未知 chart_type 抛 BizException(1001)
4. 中文字体显式设置，避免中文乱码

为什么返回 base64 字符串（不带 data: 前缀）？
  API 文档 2.5 约定前端自行拼 data:image/png;base64, 前缀显示。
"""
import base64
import io
import matplotlib
matplotlib.use("Agg")  # 无界面后端，服务器画图必备
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from app.core.response import BizException

# 支持的图表类型
SUPPORTED_CHARTS = {
    "response_distribution",
    "gender_response",
    "age_distribution",
    "premium_distribution",
}

# 中文字体：按优先级尝试，避免中文乱码（方块/缺字）
# Windows: Microsoft YaHei / SimHei（系统自带）
# Docker/Linux: Noto Sans CJK SC（fonts-noto-cjk 包安装）+ WenQuanYi Zen Hei（fonts-wqy-zenhei 包安装）
# 注：fc-list 查询到的 Noto CJK 家族名可能为 "Noto Sans CJK JP/SC/TC/KR/HK"，需逐一尝试
_CANDIDATE_FONTS = [
    # Windows 系统自带
    "Microsoft YaHei", "微软雅黑", "SimHei", "黑体", "Microsoft JhengHei",
    # Docker 安装的 fonts-noto-cjk（全名 / 简体 / 通用名）
    "Noto Sans CJK SC", "Noto Sans CJK JP", "Noto Sans CJK TC",
    "Noto Sans SC", "Noto Sans CJK", "Noto Serif CJK SC",
    # Docker 安装的 fonts-wqy-zenhei（文泉驿正黑）
    "WenQuanYi Zen Hei", "WenQuanYi Zen Hei Sharp", "WenQuanYi Micro Hei", "文泉驿正黑",
    # 兜底（无中文但不会报错）
    "DejaVu Sans", "Arial",
]
_FOUND_FONT = None
for _font in _CANDIDATE_FONTS:
    try:
        _path = matplotlib.font_manager.findfont(_font, fallback_to_default=False)
        if _path and "DejaVuSans" not in _path and "Arial.ttf" not in _path:
            _FOUND_FONT = _font
            break
    except Exception:
        continue
if not _FOUND_FONT:
    # 如果名称查找都失败，直接注册系统字体文件路径（Docker 内安装的字体文件固定位置）
    import os as _os
    _FONT_CANDIDATE_PATHS = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
    ]
    for _p in _FONT_CANDIDATE_PATHS:
        if _os.path.exists(_p):
            try:
                _fp = matplotlib.font_manager.FontProperties(fname=_p)
                _name = _fp.get_name()
                matplotlib.font_manager.fontManager.addfont(_p)
                plt.rcParams["font.sans-serif"] = [_name, "DejaVu Sans"]
                _FOUND_FONT = _name
                break
            except Exception:
                continue
if _FOUND_FONT:
    plt.rcParams["font.sans-serif"] = [_FOUND_FONT, "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False  # 负号正常显示


def render_chart(chart_type: str, rows: list[dict]) -> str:
    """画图 → 返回 base64 编码的 PNG 字符串（不带 data: 前缀）

    逐字思路：
    1. 校验 chart_type，未知 → BizException(1001)
    2. rows 转 DataFrame
    3. 按 chart_type 分发到对应画图函数
    4. savefig 到 BytesIO → base64 编码 → 返回字符串
    """
    if chart_type not in SUPPORTED_CHARTS:
        raise BizException(1001, f"未知图表类型：{chart_type}，支持 {sorted(SUPPORTED_CHARTS)}", 400)

    df = pd.DataFrame(rows)

    fig, ax = plt.subplots(figsize=(8, 5), dpi=100)

    if chart_type == "response_distribution":
        _draw_response_distribution(df, ax)
    elif chart_type == "gender_response":
        _draw_gender_response(df, ax)
    elif chart_type == "age_distribution":
        _draw_age_distribution(df, ax)
    elif chart_type == "premium_distribution":
        _draw_premium_distribution(df, ax)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


# ===== 各图表绘制（私有）=====
def _draw_response_distribution(df: pd.DataFrame, ax):
    """Response 0/1 分布柱状图（正负样本比）"""
    counts = df["response"].value_counts().sort_index()
    labels = ["未购买 (0)" if k == 0 else "已购买 (1)" for k in counts.index]
    ax.bar(labels, counts.values, color=["#5B9BD5", "#ED7D31"])
    ax.set_title("Response 分布（正负样本比）")
    ax.set_ylabel("人数")
    for i, v in enumerate(counts.values):
        ax.text(i, v, str(v), ha="center", va="bottom")


def _draw_gender_response(df: pd.DataFrame, ax):
    """性别 × Response 交叉柱状图"""
    pivot = pd.crosstab(df["gender"], df["response"])
    pivot.plot(kind="bar", ax=ax, color=["#5B9BD5", "#ED7D31"])
    ax.set_title("性别 × Response 交叉分布")
    ax.set_xlabel("性别")
    ax.set_ylabel("人数")
    ax.legend(["未购买 (0)", "已购买 (1)"], title="Response")
    plt.setp(ax.get_xticklabels(), rotation=0)


def _draw_age_distribution(df: pd.DataFrame, ax):
    """年龄分布直方图"""
    ax.hist(df["age"], bins=20, color="#70AD47", edgecolor="white")
    ax.set_title("年龄分布")
    ax.set_xlabel("年龄")
    ax.set_ylabel("人数")


def _draw_premium_distribution(df: pd.DataFrame, ax):
    """年保费分布直方图"""
    ax.hist(df["annual_premium"], bins=30, color="#FFC000", edgecolor="white")
    ax.set_title("年保费分布")
    ax.set_xlabel("年保费")
    ax.set_ylabel("人数")


# ====================================================================
# 机器学习模型评估可视化
# ====================================================================

# ML 图表类型（对齐 API 文档 3.6）
ML_SUPPORTED_CHARTS = {
    "roc_curve",
    "metrics_comparison",
    "confusion_matrix",
    "feature_importance",
}

# 模型名 → 中文显示名
MODEL_DISPLAY = {
    "logistic_regression": "逻辑回归",
    "xgboost": "XGBoost",
    "random_forest": "随机森林",
}


def render_ml_chart(chart_type: str, data: dict) -> str:
    """ML 模型评估画图 → 返回 base64 编码的 PNG 字符串

    逐字思路：
    1. 校验 chart_type，未知 → BizException(1001)
    2. 按 chart_type 分发到对应画图函数
    3. savefig 到 BytesIO → base64 编码 → 返回字符串

    data 是从 experiments.params 反序列化的 JSON dict，
    包含 roc / confusion_matrix / feature_importances / all_metrics 等字段。
    """
    if chart_type not in ML_SUPPORTED_CHARTS:
        raise BizException(1001, f"未知图表类型：{chart_type}，支持 {sorted(ML_SUPPORTED_CHARTS)}", 400)

    fig, ax = plt.subplots(figsize=(8, 5), dpi=100)

    if chart_type == "roc_curve":
        _draw_roc_curve(data, ax)
    elif chart_type == "confusion_matrix":
        _draw_confusion_matrix(data, ax)
    elif chart_type == "feature_importance":
        _draw_feature_importance(data, ax)
    elif chart_type == "metrics_comparison":
        _draw_metrics_comparison(data, ax)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")


def _draw_roc_curve(data: dict, ax):
    """ROC 曲线：从 params 中取 fpr/tpr/auc 画图

    data 结构：{"roc": {"fpr": [...], "tpr": [...], "auc": 0.82}, "model_name": "xgboost"}
    """
    roc = data.get("roc", {})
    fpr = roc.get("fpr", [])
    tpr = roc.get("tpr", [])
    auc = roc.get("auc", 0)
    model_name = data.get("model_name", "模型")

    display_name = MODEL_DISPLAY.get(model_name, model_name)

    ax.plot(fpr, tpr, color="#ED7D31", lw=2, label=f"{display_name} (AUC={auc:.4f})")
    ax.plot([0, 1], [0, 1], color="#5B9BD5", lw=1, linestyle="--", label="随机分类器 (AUC=0.5)")
    ax.set_xlim([0.0, 1.0])
    ax.set_ylim([0.0, 1.05])
    ax.set_xlabel("假正率 (FPR)")
    ax.set_ylabel("真正率 (TPR)")
    ax.set_title(f"ROC 曲线 - {display_name}")
    ax.legend(loc="lower right")
    ax.grid(True, alpha=0.3)


def _draw_confusion_matrix(data: dict, ax):
    """混淆矩阵热力图

    data 结构：{"confusion_matrix": [[TN, FP], [FN, TP]], "model_name": "xgboost"}
    """
    cm = data.get("confusion_matrix", [[0, 0], [0, 0]])
    model_name = data.get("model_name", "模型")
    display_name = MODEL_DISPLAY.get(model_name, model_name)

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["未购买 (0)", "已购买 (1)"],
        yticklabels=["未购买 (0)", "已购买 (1)"],
        ax=ax,
    )
    ax.set_xlabel("预测值")
    ax.set_ylabel("真实值")
    ax.set_title(f"混淆矩阵 - {display_name}")


def _draw_feature_importance(data: dict, ax):
    """特征重要性柱状图

    data 结构：{"feature_importances": {"gender": 0.1, "age": 0.2, ...}, "model_name": "xgboost"}
    """
    importances = data.get("feature_importances", {})
    model_name = data.get("model_name", "模型")
    display_name = MODEL_DISPLAY.get(model_name, model_name)

    if not importances:
        ax.text(0.5, 0.5, "无特征重要性数据", ha="center", va="center", fontsize=14)
        ax.set_title(f"特征重要性 - {display_name}")
        return

    # 按重要性排序
    sorted_items = sorted(importances.items(), key=lambda x: x[1], reverse=True)
    names = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]

    colors = plt.cm.viridis([i / len(names) for i in range(len(names))])
    ax.barh(names, values, color=colors)
    ax.set_xlabel("重要性")
    ax.set_title(f"特征重要性 - {display_name}")
    ax.invert_yaxis()

    # 在柱子上标注数值
    for i, v in enumerate(values):
        ax.text(v, i, f" {v:.4f}", va="center")


def _draw_metrics_comparison(data: dict, ax):
    """多模型指标对比柱状图

    data 结构：{"all_metrics": {"logistic_regression": {"accuracy": 0.8, ...}, ...}}
    """
    all_metrics = data.get("all_metrics", {})
    if not all_metrics:
        ax.text(0.5, 0.5, "无指标数据", ha="center", va="center", fontsize=14)
        ax.set_title("多模型指标对比")
        return

    # 指标名称（顺序固定）
    metric_names = ["accuracy", "precision", "recall", "f1_score", "roc_auc"]
    metric_labels = ["准确率", "精确率", "召回率", "F1", "ROC-AUC"]

    # 模型名称
    model_names = list(all_metrics.keys())
    display_names = [MODEL_DISPLAY.get(m, m) for m in model_names]

    # 柱状图参数
    n_metrics = len(metric_names)
    n_models = len(model_names)
    bar_width = 0.8 / n_models
    x = range(n_metrics)

    colors = ["#5B9BD5", "#ED7D31", "#70AD47"]

    for i, model_name in enumerate(model_names):
        metrics = all_metrics[model_name]
        values = [metrics.get(m, 0) for m in metric_names]
        offset = (i - n_models / 2 + 0.5) * bar_width
        ax.bar(
            [xi + offset for xi in x],
            values,
            bar_width,
            label=display_names[i],
            color=colors[i % len(colors)],
        )

    ax.set_xticks(list(x))
    ax.set_xticklabels(metric_labels)
    ax.set_ylabel("分数")
    ax.set_title("多模型指标对比")
    ax.set_ylim(0, 1.05)
    ax.legend()
    ax.grid(True, alpha=0.3, axis="y")
