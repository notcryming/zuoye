# ==============================
# 1. 数据可视化 —— 作为预处理的依据
# ==============================
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 读取原始数据
df = pd.read_excel("data.xlsx")
print(df.shape)
print(df.head())

# 创建大图：观察所有关键特征分布
plt.figure(figsize=(16, 12))

# 1. 年龄分布
plt.subplot(3, 3, 1)
df['Age'].hist(bins=20, color='#4472C4', edgecolor='white')
plt.title('Age 年龄分布')
# plt.show()

# 2. 保单持有天数 Vintage
plt.subplot(3, 3, 2)
df['Vintage'].hist(bins=20, color='#5B9BD5', edgecolor='white')
plt.title('Vintage 保单持有天数')

# 3. 年度保费（严重右偏！）
plt.subplot(3, 3, 3)
df['Annual_Premium'].hist(bins=50, color='#ED7D31', edgecolor='white')
plt.title('Annual_Premium 保费分布（右偏 → 需要分箱）')
'''
这是一个非常典型且经常容易被误解的问题！我们把这个问题拆成两部分来解答：

### 1. 为什么你看图片觉得是“左偏”，但代码里叫“右偏”？
这是统计学中一个最容易让人混淆的命名规则： 偏度（Skewness）是根据“尾巴”的方向命名的，而不是根据“山峰（数据集中处）”命名的。

- 视觉感受 ：在你的图片中，绝大多数人的保费金额较低，所以直方图的“高山”都集中在左边。
- 统计学定义 ：因为大部分人保费低，只有极少数人交了非常高的保费（比如豪车），导致图形的 右侧拖了一条长长的尾巴 。因为 尾巴在右边 ，所以这在统计学上被称为**右偏（Right-skewed）**或正偏态。 总结口诀 ：尾巴朝哪边，就叫什么偏。山峰在左边，长尾在右边 = 右偏 。
### 2. 为什么保费分布右偏（有长尾）就需要“分箱”？
在 preprogress_xgboost.py 中，我们通过 pd.cut 把保费划分为不同的区间（分箱），主要有以下几个原因：

- 消除极端值（土豪）的干扰 ：
  右偏意味着数据中有少部分极大的值（天价保费）。如果直接把连续数值丢给机器学习模型，这些巨大的数值会产生过大的权重，把模型“带偏”。分箱后，不管是 5 万还是 10 万的保费，都会被统一归入“高保费”类别（比如标签 3 ），削弱了极端异常值的影响力。
- 更符合真实的业务逻辑 ：
  在保险业务中，保费的“绝对差值”往往不如“区间”有意义。比如，保费从 3000 元变成 5000 元（跨越了消费阶层），比保费从 53000 元变成 55000 元（都是高端客户）对预测结果的影响大得多。通过人为划定边界（如 [0, 10000, 25000, 50000, np.inf] ），实际上是帮模型做了一次 用户群体分层 。
- 增加模型的鲁棒性（稳定性） ：
  把连续变动的数值变成几个固定的类别（0, 1, 2, 3），可以过滤掉一些无关紧要的微小波动，让模型去学习“保费水平高低”与“是否响应”之间的宏观规律，而不是死记硬背具体的金额数字。
'''


# 4. 区域编码（连续数值，非无序分类）
plt.subplot(3, 3, 4)
df['Region_Code'].hist(bins=30, color='#70AD47', edgecolor='white')
plt.title('Region_Code 区域编码 → 保留数值')

# 5. 销售渠道（离散编号 → 必须转分类）
plt.subplot(3, 3, 5)
df['Policy_Sales_Channel'].value_counts().head(15).plot(kind='bar', color='#FFC000')
plt.title('Policy_Sales_Channel 渠道 → 转分类特征')

# 6. 车龄分布（有序分类）
plt.subplot(3, 3, 6)
df['Vehicle_Age'].value_counts().plot(kind='bar', color='#A5A5A5')
plt.title('Vehicle_Age 车龄 → 有序编码')

# 7. 性别分布
plt.subplot(3, 3, 7)
df['Gender'].value_counts().plot(kind='bar', color='#8B008B')
plt.title('Gender 性别 → 二分类')

# 8. 车辆是否损坏
plt.subplot(3, 3, 8)
df['Vehicle_Damage'].value_counts().plot(kind='bar', color='#C00000')
plt.title('Vehicle_Damage 车辆损坏 → 二分类')

# 9. 标签分布（是否响应）
plt.subplot(3, 3, 9)
df['Response'].value_counts().plot(kind='bar', color='#008080')
plt.title('Response 标签分布')

plt.tight_layout()
plt.savefig("01_数据分布可视化_预处理依据.png", dpi=300)
plt.show()

# ==============================
# 可视化结论（直接写进作业）
# ==============================
# 1. Annual_Premium 严重右偏，存在大额异常值 → 必须分箱
# 2. Policy_Sales_Channel 是离散编号，无大小意义 → 转为category
# 3. Age、Vintage 分布合理 → 保留数值型
# 4. Region_Code 代表区域经济水平 → 保留数值
# 5. Vehicle_Age 是有序类别 → 做有序编码
# 6. Gender、Vehicle_Damage 是二分类 → 映射为0/1
# 7. Vintage 保单天数连续有意义 → 保持数值
