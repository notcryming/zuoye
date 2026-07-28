from matplotlib import lines
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import os

# ====================== 全局环境配置 ======================
import matplotlib
import matplotlib.font_manager as fm

# 设置seaborn样式（注意：这会覆盖matplotlib的字体设置）
sns.set_style("ticks")

# 【重要】在seaborn样式设置之后，重新配置中文字体
plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 12

# 创建图片保存文件夹
save_dir = "exercise_output"
if not os.path.exists(save_dir):
    os.mkdir(save_dir)

tips = sns.load_dataset("tips")       # 餐饮小费数据
iris = sns.load_dataset("iris")       # 鸢尾花数据

# 核密度曲线
sns.kdeplot(data=tips, x="tip", hue="sex", linewidth=2)
# 分布直方图
sns.histplot(data=tips, x="tip", kde=True, bins=30, alpha=0.5) # kde=True 叠加平滑曲线
plt.title("小费分布直方图与核密度曲线")
plt.savefig(f"{save_dir}/ex1.png", dpi=300)
plt.show()

sns.kdeplot(data=tips, x="total_bill", hue="smoker", linewidth=2)
plt.title("是否吸烟对总账单的影响")
plt.savefig(f"{save_dir}/ex2.png", dpi=300)
plt.show()

sns.boxplot(data=tips, x="time", y="tip", hue="sex")
plt.title("男女不同时段用餐小费箱线图")
plt.savefig(f"{save_dir}/ex3.png", dpi=300)
plt.show()

sns.violinplot(data=tips, x="day", y="tip", hue="time", split=True)
plt.title("每天不同时段的小费小提琴图")
plt.savefig(f"{save_dir}/ex4.png", dpi=300)
plt.show()

# errwidth=0 去掉误差线，让图更干净
sns.barplot(data=tips, x="day", y="tip", errwidth=0)
plt.title("每天的小费柱状图")
plt.savefig(f"{save_dir}/ex5.png", dpi=300)
plt.show()

corr_matrix = tips.select_dtypes(include=[np.number]).corr()
sns.heatmap(
    corr_matrix,
    annot=True,        # 显示相关系数数字
    cmap="coolwarm",   # 冷暖配色
    vmin=-1, vmax=1,   # 数值区间
    square=True,       # 正方形格子
    linewidths=0.5
)
plt.title("数值列之间的相关性热力图")
plt.savefig(f"{save_dir}/ex6.png", dpi=300)
plt.show()

# regplot不支持hue，lmplot是更高级的接口
# sns.regplot(data=tips[tips["smoker"] == "Yes"], x="total_bill", y="tip", color="#2E86AB", label="吸烟者")
# sns.regplot(data=tips[tips["smoker"] == "No"], x="total_bill", y="tip", color="#2E86AB", label="非吸烟者")
sns.lmplot(data=tips, x="total_bill", y="tip", hue="smoker")
plt.title("是否吸烟的账单小费回归图")
plt.savefig(f"{save_dir}/ex7.png", dpi=300)
plt.show()

cols = ["sepal_length", "sepal_width", "petal_length"]
df_iris = iris[cols + ["species"]]
g = sns.pairplot(data=df_iris, hue="species", height=2.5)
g.savefig(f"{save_dir}/ex8.png", dpi=300, bbox_inches="tight")
plt.show()

fig, axes = plt.subplots(2, 1, figsize=(8, 7))
sns.kdeplot(data=tips, x="total_bill", fill=True, ax=axes[0])
axes[0].set_title("总账单密度分布")
sns.barplot(data=tips, x="sex", y="tip", ax=axes[1])
axes[1].set_title("男女平均小费")
plt.tight_layout()
plt.savefig(f"{save_dir}/ex9.png", dpi=300)
plt.show()

fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("餐饮消费综合可视化图表", fontsize=16, y=1.02)
sns.violinplot(data=tips, x="sex", y="total_bill", ax=axes[0])
axes[0].set_title("男女消费金额分布")
sns.barplot(data=tips, x="day", y="total_bill", ax=axes[1])
axes[1].set_title("一周每日平均消费")
plt.tight_layout()
plt.savefig(f"{save_dir}/ex10.png", dpi=300)
plt.show()

