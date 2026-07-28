# -*- coding: utf-8 -*-
"""
Seaborn 课后10道练习题 完整可运行代码
自动加载内置数据集，网络不佳会给出提示
"""
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
import os

# ==================== 全局统一配置 ====================
# 清除字体缓存
fm._load_fontmanager(try_read_cache=False)

# 创建图片保存文件夹
save_dir = "exercise_output"
if not os.path.exists(save_dir):
    os.mkdir(save_dir)

# 直接加载数据集（sns内置，自动下载）
try:
    tips = sns.load_dataset("tips")
    iris = sns.load_dataset("iris")
    print("数据集加载成功！")
except Exception as e:
    print(f"数据集下载失败：{e}\n请检查网络，或者使用下方离线加载方式")
    exit()

# 设置seaborn样式（注意：这会覆盖matplotlib的字体设置）
sns.set_style("ticks")

# 【重要】在seaborn样式设置之后，重新配置中文字体
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "SimSun"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 12

# ==================== 习题1 ====================
print("\n===== 正在绘制习题1 =====")
plt.figure(figsize=(7, 4))
sns.histplot(data=tips, x="tip", bins=30, kde=True)
plt.title("小费金额分布直方图")
plt.tight_layout()
plt.savefig(f"{save_dir}/ex1.png", dpi=300)
plt.show()

# ==================== 习题2 ====================
print("===== 正在绘制习题2 =====")
plt.figure(figsize=(8, 4))
sns.kdeplot(data=tips, x="total_bill", hue="smoker", fill=True)
plt.title("吸烟/非吸烟人群账单分布对比")
plt.tight_layout()
plt.savefig(f"{save_dir}/ex2.png", dpi=300)
plt.show()

# ==================== 习题3 ====================
print("===== 正在绘制习题3 =====")
plt.figure(figsize=(9, 5))
sns.boxplot(data=tips, x="time", y="tip", hue="sex", palette="Set1")
plt.title("午晚餐男女小费箱线对比")
plt.tight_layout()
plt.savefig(f"{save_dir}/ex3.png", dpi=300)
plt.show()

# ==================== 习题4 ====================
print("===== 正在绘制习题4 =====")
plt.figure(figsize=(9, 5))
sns.violinplot(data=tips, x="day", y="tip", hue="time", split=True)
plt.title("各星期不同时段小费小提琴图")
plt.tight_layout()
plt.savefig(f"{save_dir}/ex4.png", dpi=300)
plt.show()

# ==================== 习题5 ====================
print("===== 正在绘制习题5 =====")
plt.figure(figsize=(7, 4))
sns.barplot(data=tips, x="day", y="tip", errwidth=0)
plt.title("每日平均小费（无误差线）")
plt.tight_layout()
plt.savefig(f"{save_dir}/ex5.png", dpi=300)
plt.show()

# ==================== 习题6 ====================
print("===== 正在绘制习题6 =====")
plt.figure(figsize=(5, 4))
corr = tips.select_dtypes(include=[np.number]).corr()
sns.heatmap(
    corr,
    annot=True,
    cmap="coolwarm",
    square=True,
    vmin=-0.8,
    vmax=0.8
)
plt.title("特征相关热力图")
plt.tight_layout()
plt.savefig(f"{save_dir}/ex6.png", dpi=300)
plt.show()

# ==================== 习题7 ====================
print("===== 正在绘制习题7 =====")
plt.figure(figsize=(8, 5))
for smoke in ["Yes", "No"]:
    sub_data = tips[tips["smoker"] == smoke]
    sns.regplot(data=sub_data, x="total_bill", y="tip", label=smoke, scatter_kws={"alpha": 0.6})
plt.legend(title="是否吸烟")
plt.title("账单-小费回归对比")
plt.tight_layout()
plt.savefig(f"{save_dir}/ex7.png", dpi=300)
plt.show()

# ==================== 习题8 ====================
print("===== 正在绘制习题8 =====")
cols = ["sepal_length", "sepal_width", "petal_length"]
df_iris = iris[cols + ["species"]]
g = sns.pairplot(data=df_iris, hue="species", height=2.5)
g.savefig(f"{save_dir}/ex8.png", dpi=300, bbox_inches="tight")
plt.show()

# ==================== 习题9 ====================
print("===== 正在绘制习题9 =====")
fig, axes = plt.subplots(2, 1, figsize=(8, 7))
sns.kdeplot(data=tips, x="total_bill", fill=True, ax=axes[0])
axes[0].set_title("总账单密度分布")

sns.barplot(data=tips, x="sex", y="tip", ax=axes[1])
axes[1].set_title("男女平均小费")

plt.tight_layout()
plt.savefig(f"{save_dir}/ex9.png", dpi=300)
plt.show()

# ==================== 习题10 综合题 ====================
print("===== 正在绘制习题10 =====")
fig, axes = plt.subplots(1, 2, figsize=(14, 6))
fig.suptitle("餐饮消费综合可视化图表", fontsize=16, y=1.02)

sns.violinplot(data=tips, x="sex", y="total_bill", ax=axes[0])
axes[0].set_title("男女消费金额分布")

sns.barplot(data=tips, x="day", y="total_bill", ax=axes[1])
axes[1].set_title("一周每日平均消费")

plt.tight_layout()
plt.savefig(f"{save_dir}/ex10.png", dpi=300)
plt.show()

print("\n✅ 所有题目绘图完毕，图片全部保存在 exercise_output 文件夹")