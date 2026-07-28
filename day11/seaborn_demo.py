# -*- coding: utf-8 -*-
"""
Seaborn 全套基础绘图演示脚本
依赖安装：pip install seaborn matplotlib numpy pandas
"""
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# ====================== 全局环境配置 ======================
import matplotlib
import matplotlib.font_manager as fm

# 清除字体缓存
fm._load_fontmanager(try_read_cache=False)

# 设置seaborn整体绘图风格（注意：这会覆盖matplotlib的字体设置）
sns.set_style("whitegrid")    # 可选：white / dark / whitegrid / darkgrid / ticks
sns.set_context("notebook")   # 控制字体大小：paper / notebook / talk / poster

# 【重要】在seaborn样式设置之后，重新配置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 12

# 创建保存图片文件夹，避免报错
if not os.path.exists("sns_output"):
    os.mkdir("sns_output")

# ====================== 加载内置测试数据集 ======================
# 先下载保存到本地，再从本地读取（避免网络不佳导致的问题）
# tips = sns.load_dataset("tips")       # 小费数据集（餐饮消费）
# iris = sns.load_dataset("iris")       # 鸢尾花数据集
# flights = sns.load_dataset("flights") # 航班客流时序数据

# 保存到本地CSV文件
# tips.to_csv("tips.csv", index=False)
# # iris.to_csv("iris.csv", index=False)
# # flights.to_csv("flights.csv", index=False)

# print("数据集已保存到本地CSV文件")

print("=== 从本地CSV文件读取数据集 ===")
tips = pd.read_csv("tips.csv")

print("=== tips数据集前5行 ===")
print(tips.head())
print("\n=== 数据集字段类型 ===")
print(tips.dtypes)

# ====================== 1. 单变量分布图：直方图+核密度图 ======================
plt.figure(figsize=(8, 5))
sns.histplot(data=tips, x="total_bill", kde=True, bins=25)
plt.title("账单金额分布直方图", fontsize=13)
plt.xlabel("总账单")
plt.ylabel("频次")
plt.tight_layout()
plt.savefig("sns_output/01_hist.png", dpi=300, bbox_inches="tight")
plt.show()

# ====================== 2. 核密度图（分组对比分布） ======================
plt.figure(figsize=(8, 5))
sns.kdeplot(data=tips, x="total_bill", hue="sex", linewidth=2)
plt.title("男女消费账单分布对比", fontsize=13)
plt.xlabel("总账单")
plt.ylabel("密度")
plt.tight_layout()
plt.savefig("sns_output/02_kde.png", dpi=300, bbox_inches="tight")
plt.show()

# ====================== 3. 箱线图：分类数据分布对比 ======================
plt.figure(figsize=(9, 5))
sns.boxplot(data=tips, x="day", y="total_bill", hue="time", palette="Set2")
plt.title("每周各时段消费账单箱线图", fontsize=13)
plt.xlabel("星期")
plt.ylabel("账单金额")
plt.tight_layout()
plt.savefig("sns_output/03_boxplot.png", dpi=300, bbox_inches="tight")
plt.show()

# ====================== 4. 小提琴图 ======================
plt.figure(figsize=(8, 5))
sns.violinplot(data=tips, x="sex", y="tip", hue="smoker", split=True, palette="RdBu")
plt.title("吸烟/不吸烟男女小费分布小提琴图", fontsize=13)
plt.tight_layout()
plt.savefig("sns_output/04_violin.png", dpi=300, bbox_inches="tight")
plt.show()

# ====================== 5. 柱状图（均值+误差线） ======================
plt.figure(figsize=(7, 5))
sns.barplot(data=tips, x="day", y="tip", palette="Blues_d")
plt.title("每日平均小费金额", fontsize=13)
plt.xlabel("星期")
plt.ylabel("平均小费")
plt.tight_layout()
plt.savefig("sns_output/05_bar.png", dpi=300, bbox_inches="tight")
plt.show()

# ====================== 6. 相关性热力图 ======================
plt.figure(figsize=(6, 5))
# 只提取数值列计算相关系数
corr_matrix = tips.select_dtypes(include=[np.number]).corr()
sns.heatmap(
    corr_matrix,
    annot=True,        # 显示相关系数数字
    cmap="coolwarm",   # 冷暖配色
    vmin=-1, vmax=1,   # 数值区间
    square=True,       # 正方形格子
    linewidths=0.5
)
plt.title("特征相关性热力图", fontsize=13)
plt.tight_layout()
plt.savefig("sns_output/06_heatmap.png", dpi=300, bbox_inches="tight")
plt.show()

# # ====================== 7. 回归拟合图（散点+线性回归线） ======================
# plt.figure(figsize=(8, 5))
# sns.regplot(data=tips, x="total_bill", y="tip", color="#2E86AB")
# plt.title("账单金额与小费线性回归关系", fontsize=13)
# plt.xlabel("总账单")
# plt.ylabel("小费")
# plt.tight_layout()
# plt.savefig("sns_output/07_regplot.png", dpi=300, bbox_inches="tight")
# plt.show()

# # ====================== 8. 多变量配对散点图矩阵 pairplot ======================
# # 会弹出大图，用于探索多维数据关系
# g = sns.pairplot(data=iris, hue="species", height=2)
# g.fig.suptitle("鸢尾花特征两两分布矩阵", y=1.02, fontsize=14)
# g.savefig("sns_output/08_pairplot.png", dpi=300, bbox_inches="tight")
# plt.show()

# # ====================== 9. 多子图布局（2行2列画布） ======================
# fig, axes = plt.subplots(2, 2, figsize=(12, 9))
# # 子图1：直方图
# sns.histplot(data=tips, x="tip", ax=axes[0, 0], color="orange")
# axes[0,0].set_title("小费分布")
# # 子图2：箱线图
# sns.boxplot(data=tips, x="time", y="tip", ax=axes[0, 1])
# axes[0,1].set_title("午晚餐小费对比")
# # 子图3：柱状图
# sns.barplot(data=tips, x="sex", y="tip", ax=axes[1, 0])
# axes[1,0].set_title("男女平均小费")
# # 子图4：密度图
# sns.kdeplot(data=tips, x="total_bill", ax=axes[1, 1], fill=True)
# axes[1,1].set_title("账单密度曲线")

# plt.tight_layout()
# plt.savefig("sns_output/09_subplots.png", dpi=300, bbox_inches="tight")
# plt.show()

# print("\n✅ 所有图表绘制完成，图片保存在 sns_output 文件夹内")