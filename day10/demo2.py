import pandas as pd
import matplotlib.pyplot as plt

# 解决中文
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取数据
df = pd.read_csv('./database/StudentsPerformance.csv')

# 创建画布
plt.figure(figsize=(12,10))

# 数学成绩分布
plt.subplot(2,2,1)
plt.hist(df['math_score'], bins=10, color='skyblue', alpha=0.7)
plt.title('数学成绩分布')
plt.xlabel('分数')
plt.ylabel('人数')
# plt.show()

# 三科平均分柱状图
mean_scores = [df['math_score'].mean(), df['reading_score'].mean(), df['writing_score'].mean()]
subjects = ['数学', '阅读', '写作']
plt.subplot(2,2,2)
plt.bar(subjects, mean_scores, color=['red', 'blue', 'green'])
plt.title('三科平均分')
plt.ylim(0,100)
# plt.xlabel('科目')
# plt.ylabel('平均分')
# plt.show()

# 阅读与写作相关性
plt.subplot(2,2,3)
plt.scatter(df['reading_score'], df['writing_score'], alpha=0.5)
plt.title('阅读与写作相关性')
# plt.show()

# 成绩等级饼图
A = len(df[df['math_score']>=85])
B = len(df[(df['math_score']>=70) & (df['math_score']<85)])
C = len(df[(df['math_score']>=60) & (df['math_score']<70)])
D = len(df[df['math_score']<60])

plt.subplot(2,2,4)
plt.pie([A,B,C,D], labels=['优秀','良好','及格','不及格'], autopct='%1.1f%%')
plt.title('数学成绩等级占比')
# plt.show()

plt.tight_layout()
plt.savefig('学生成绩分析报告.png', dpi=300)
plt.show()





