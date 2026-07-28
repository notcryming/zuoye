import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 解决中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('./database/StudentsPerformance.csv')

# 创建画布
plt.figure(figsize=(18,10))

# 三科成绩分布对比（直方图）.

plt.subplot(2,3,1)
plt.hist(df["math_score"], bins=12, alpha=0.3, edgecolor='black', color='gray', label='数学')
plt.hist(df["reading_score"], bins=12, alpha=0.5, edgecolor='black', color='green', label='阅读')
plt.hist(df["writing_score"], bins=12, alpha=0.5, edgecolor='black', color='orange', label='写作')
# 添加图例
plt.legend(fontsize=10)
# 网格
plt.grid(True, alpha=0.3)
plt.title('三科成绩分布对比')
plt.xlabel('分数')
plt.ylabel('人数')
# plt.show()

# 有无考前辅导成绩对比（分组柱状图Bar）
plt.subplot(2,3,2)00
subjects = ['math_score', 'reading_score', 'writing_score']
grouped = df.groupby('test_preparation_course')[subjects].mean()
x = np.arange(len(subjects))  # [0, 1, 2]
width = 0.35  # 柱子宽度
completed_scores = grouped.loc['completed', subjects].values
none_scores = grouped.loc['none', subjects].values
# 绘制双柱图
plt.bar(x - width/2, completed_scores, width, label='完成辅导', color='steelblue', edgecolor='black')
plt.bar(x + width/2, none_scores, width, label='未参加辅导', color='lightcoral', edgecolor='black')
# 柱子顶部标注
bars1_heights = completed_scores
bars2_heights = none_scores
for i, h in enumerate(bars1_heights):
    plt.text(x[i] - width/2, h + 0.5, f'{h:.1f}', ha='center', va='bottom', fontsize=9)
for i, h in enumerate(bars2_heights):
    plt.text(x[i] + width/2, h + 0.5, f'{h:.1f}', ha='center', va='bottom', fontsize=9)
plt.xticks(x, ['数学', '阅读', '写作'])
plt.xlabel('科目', fontsize=12)
plt.ylabel('平均分', fontsize=12)
plt.ylim(0, 100)
plt.title('有无考前辅导的成绩对比', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, axis='y', alpha=0.3)
# plt.tight_layout(pad=5.0, h_pad=5.0, w_pad=5.0)
# plt.show()

# 阅读与写作相关性（区分性别）（散点图）
plt.subplot(2,3,3)
male = df[df['gender'] == 'male']
female = df[df['gender'] == 'female']
plt.scatter(male['reading_score'], male['writing_score'],
            alpha=0.5, color='blue', label='男生', s=30)
plt.scatter(female['reading_score'], female['writing_score'],
            alpha=0.5, color='red', label='女生', s=30)
# 全局一元线性拟合
x = df['reading_score']
y = df['writing_score']
slope, intercept = np.polyfit(x, y, 1)  # 1次多项式 = 线性
# 计算拟合线 y值
fit_x = np.array([x.min(), x.max()])
fit_y = slope * fit_x + intercept
plt.plot(fit_x, fit_y, color='black', linewidth=2, label='拟合直线')
# 计算相关系数
corr = x.corr(y)
plt.text(0.05, 0.95, f'相关系数 r = {corr:.3f}',
         transform=plt.gca().transAxes,
         fontsize=11, verticalalignment='top',
         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
plt.xlabel('阅读分数', fontsize=12)
plt.ylabel('写作分数', fontsize=12)
plt.title('阅读与写作相关性（区分性别）', fontsize=12)
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.tight_layout(pad=5.0, h_pad=5.0, w_pad=5.0)
plt.show()




