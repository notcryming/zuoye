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
for _font in ["Microsoft YaHei", "Noto Sans CJK SC", "SimHei", "DejaVu Sans"]:
    try:
        matplotlib.font_manager.findfont(_font, fallback_to_default=False)
        plt.rcParams["font.sans-serif"] = [_font]
        break
    except Exception:
        continue
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
