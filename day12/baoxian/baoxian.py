'''
项目一：AI驱动的金融保险智能营销系统
## 项目背景：
有38+条用户数，来自于购买过某公司人寿保险的用户信息，现在要基于这个数据，对用户进行预测，是否会购买该公司的车险，需构建相关的模型训练并预测，拿到预测结果后需要抽取高潜客户的个人信息（表中的信息），接入大模型，进行个性化邮件生成，推送给高潜用户，降低人力成本，提高营销效率。
任务一：用xgboost进行建模和预测高潜客户
id，性别、年龄、是否有驾照、地区编号、是否买过车险、车龄、车是否损坏过、每年保费、获取渠道、参保天数；是否买了本司车险
### 课堂任务：完成模型训练代码
数据清洗
数据可视化
数据预处理（特征工程）-->data_preprocessed.csv
建模
统计指标：存成报告txt
用test数据，预测高潜用户-->high_value_users.csv（显示用户信息和Response_prob预测出的可能性）
'''
from matplotlib import lines
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import os
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (confusion_matrix, accuracy_score, precision_score,
                             recall_score, f1_score, roc_auc_score, roc_curve, auc,
                             precision_recall_curve, classification_report)
# 全局环境配置
import matplotlib
import matplotlib.font_manager as fm

# 设置seaborn样式（注意：这会覆盖matplotlib的字体设置）
sns.set_style("ticks")

# 【重要】在seaborn样式设置之后，重新配置中文字体
plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["font.size"] = 12

# 加载数据
try:
    df = pd.read_excel("data.xlsx", engine="openpyxl")
except FileNotFoundError:
    print("文件不存在，跳过读取")
# 看看数据
# print(df.head())
# print(df.info())
# print(df.describe())
'''
Region_Code和Policy_Sales_Channel数字编码代表的是类型，数字大小不重要
Vehicle_Age需要根据内容做分段转换
Gender和Vehicle_Damage不是数字类型，需要转换
Annual_Premium的保金同样需要按照分段来划分层次
Vintage参保天数需要结合地区来看，做多项式参数？xgboost好像是树模型，可以自动学习到这种交互性，似乎也并不用合并为多项式
看下Age,Vehicle_Age对于Response的影响，是否存在影响
看下Response的分布是否合理
'''

# 先做可视化看看Annual_Premium的分布，用直方图和箱线图
# plt.subplot(2,2,1)
# sns.histplot(data=df, x="Annual_Premium", kde=True, bins=30, alpha=0.5) # kde=True 叠加平滑曲线
# plt.title("保费分布直方图")
# plt.show()
# 存在极端数据，大部分数据还是在低金额区
# 分成0-10000,10001-20000,20001-40000，40001-70000,70001-100000，>100000比较合适

plt.subplot(2,2,2)
sns.violinplot(data=df, x="Region_Code", y="Annual_Premium", split=True)
plt.title("不同地区保费小提琴图")
# 地区特别多，似乎每个地区都有极端值，极端值差别比较大，每个地区的大部分数据差距也不算大

plt.subplot(2,2,3)
sns.boxplot(data=df, x="Age", hue="Response")
# 没买的人分布比较均匀，买保险的人当中35-55的人比较多
plt.title("年龄对于是否买保险影响的箱线图")

plt.subplot(2,2,4)
sns.boxplot(data=df, x="Vehicle_Age", hue="Response")
plt.title("车龄对于是否买保险影响的箱线图")
# 车龄大于2的基本都买了，车龄小于2的基本没买
# plt.show()

# 查看各项原始数据的直方分布（检查数据不平衡）
plt.subplot(2,2,1)
plt.figure(figsize=(16, 12))
cols_to_plot = ['Gender', 'Age', 'Driving_License', 'Region_Code', 'Previously_Insured',
                'Vehicle_Age', 'Vehicle_Damage', 'Annual_Premium', 'Policy_Sales_Channel', 'Vintage', 'Response']
for i, col in enumerate(cols_to_plot, 1):
    plt.subplot(3, 4, i)
    # 对二值/离散型特征用离散直方图，连续型用普通直方图
    if col in ['Gender', 'Driving_License', 'Previously_Insured', 'Vehicle_Damage', 'Response']:
        sns.histplot(data=df, x=col, discrete=True, shrink=0.8)
    else:
        sns.histplot(data=df, x=col, kde=True, bins=30)
    plt.title(f"{col} 分布")
    plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig("output/ex2_data_distribution.png", dpi=300)
# plt.show()

# 数据预处理（特征工程）
# ============================================================
print("\n========== 数据预处理（特征工程）==========")
print(f"原始数据形状: {df.shape}")
print(f"\n原始数据前5行:\n{df.head()}")

# ---------- 1. 特征编码 ----------
print("\n--- 1. 特征编码 ---")

# 1.1 二值特征 Label Encoding
gender_map = {'Male': 1, 'Female': 0}
df['Gender'] = df['Gender'].map(gender_map)
print(f"Gender 编码后取值: {df['Gender'].unique()}")

vehicle_damage_map = {'Yes': 1, 'No': 0}
df['Vehicle_Damage'] = df['Vehicle_Damage'].map(vehicle_damage_map)
print(f"Vehicle_Damage 编码后取值: {df['Vehicle_Damage'].unique()}")

# 1.2 有序特征 Label Encoding
vehicle_age_map = {'< 1 Year': 0, '1-2 Year': 1, '> 2 Years': 2}
df['Vehicle_Age'] = df['Vehicle_Age'].map(vehicle_age_map)
print(f"Vehicle_Age 编码后取值: {df['Vehicle_Age'].unique()}")

df = df.drop(columns=['id'])

# 1.3 保费金额分箱处理
print("\n--- 1.3 保费金额分箱 ---")
# 按业务逻辑分段：0-10000,10001-20000,20001-40000，40001-70000,70001-100000，>100000
bins = [0, 10000, 20000, 40000, 70000, 100000, float('inf')]
labels = [1, 2, 3, 4, 5, 6]
df['Annual_Premium_Bin'] = pd.cut(df['Annual_Premium'], bins=bins, labels=labels, include_lowest=True).astype(int)
print(f"Annual_Premium 分箱后分布:\n{df['Annual_Premium_Bin'].value_counts().sort_index()}")
print(f"Annual_Premium_Bin 数据类型: {df['Annual_Premium_Bin'].dtype}")
print(f"分箱区间映射: 1=[0,10000], 2=[10001,20000], 3=[20001,40000], 4=[40001,70000], 5=[70001,100000], 6=[>100000]")
# 删除原始保费列
df = df.drop(columns=['Annual_Premium'])
print(f"已删除原始 Annual_Premium 列，新增 Annual_Premium_Bin 分箱列")

# 1.4 类别型特征 Region_Code / Policy_Sales_Channel 类别数较多
# XGBoost（树模型）可直接用 Label Encoding，无需 OneHot
print(f"\nRegion_Code 唯一值数量: {df['Region_Code'].nunique()}")
print(f"Policy_Sales_Channel 唯一值数量: {df['Policy_Sales_Channel'].nunique()}")

# 演示 OneHot 用法（实际建模时不用，类别多会维度爆炸）
# encoder_region = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
# region_encoded = encoder_region.fit_transform(df[['Region_Code']])
# region_df = pd.DataFrame(region_encoded, columns=encoder_region.categories_[0].astype(str))
# print(f"Region_Code OneHot 编码后形状: {region_df.shape}")
# print(f"Region_Code OneHot 编码后前3行:\n{region_df.head(3)}")

# # ---------- 2. 特征缩放 ----------
# print("\n--- 2. 特征缩放 ---")
# # 注：XGBoost 是树模型，对特征缩放不敏感，此处仅演示用法
# scaler_std = StandardScaler()
# age_scaled = scaler_std.fit_transform(df[['Age']])
# print(f"标准化后 Age(前5个): {age_scaled[:5].flatten()}")
#
# scaler_minmax = MinMaxScaler()
# age_norm = scaler_minmax.fit_transform(df[['Age']])
# print(f"归一化后 Age(前5个): {age_norm[:5].flatten()}")
#
# # ---------- 3. 多项式特征 ----------
# print("\n--- 3. 多项式特征 ---")
# # 注：XGBoost 是树模型，能自动学习特征交互，构造多项式特征对树模型意义不大
# # 此处仅演示 PolynomialFeatures 的用法
# poly = PolynomialFeatures(degree=2, interaction_only=True)
# X_poly = poly.fit_transform(df[['Age', 'Annual_Premium']])
# print(f"多项式特征名称: {poly.get_feature_names_out(['Age', 'Annual_Premium'])}")
# print(f"特征形状从 ({df.shape[0]}, 2) 变为 ({df.shape[0]}, {X_poly.shape[1]})")

# ---------- 3.5 Response 类别不平衡重采样 ----------
print("\n--- 3.5 Response 类别不平衡重采样 ---")
# 3.5.1 先看原始分布
class_counts_raw = df['Response'].value_counts().sort_index()
print(f"重采样前 Response 分布:")
print(f"  Response=0 (未购买): {class_counts_raw.get(0, 0)} 条 ({class_counts_raw.get(0, 0)/len(df)*100:.2f}%)")
print(f"  Response=1 (购买):   {class_counts_raw.get(1, 0)} 条 ({class_counts_raw.get(1, 0)/len(df)*100:.2f}%)")
print(f"  正负样本比例: 1 : {class_counts_raw.get(0, 1) / max(class_counts_raw.get(1, 1), 1):.2f}")

# 3.5.2 用 SMOTE 对整个 df 做过采样（仅展示特征工程阶段的处理逻辑）
# 先分离 X 和 y
X_all = df.drop(columns=['Response'])
y_all = df['Response']

try:
    # 优先使用 imblearn 的 SMOTE（合成少数类样本，避免随机过采样导致的过拟合）
    from imblearn.over_sampling import SMOTE
    smote = SMOTE(random_state=42)
    X_resampled, y_resampled = smote.fit_resample(X_all, y_all)
    print(f"\n使用 SMOTE 过采样完成")
except ImportError:
    # 如果未安装 imblearn，回退到 sklearn 的简单随机过采样（复制少数类样本）
    print("\n未安装 imblearn，使用 sklearn 随机过采样作为回退方案")
    from sklearn.utils import resample
    df_majority = df[df['Response'] == 0]
    df_minority = df[df['Response'] == 1]
    df_minority_upsampled = resample(
        df_minority,
        replace=True,                  # 有放回抽样
        n_samples=len(df_majority),    # 采样到与多数类一样多
        random_state=42
    )
    df_upsampled = pd.concat([df_majority, df_minority_upsampled])
    X_resampled = df_upsampled.drop(columns=['Response'])
    y_resampled = df_upsampled['Response']

# 3.5.3 重采样后，把 X_resampled + y_resampled 重新合并为新的 df（保留 id 等信息）
df = pd.concat([X_resampled.reset_index(drop=True), y_resampled.reset_index(drop=True)], axis=1)

# 3.5.4 查看重采样后分布
class_counts_new = df['Response'].value_counts().sort_index()
print(f"重采样后 Response 分布:")
print(f"  Response=0 (未购买): {class_counts_new.get(0, 0)} 条 ({class_counts_new.get(0, 0)/len(df)*100:.2f}%)")
print(f"  Response=1 (购买):   {class_counts_new.get(1, 0)} 条 ({class_counts_new.get(1, 0)/len(df)*100:.2f}%)")
print(f"  重采样后数据形状: {df.shape}")

# ---------- 4. 保存预处理数据 ----------
print("\n--- 4. 保存预处理数据 ---")
df.to_csv("data_preprocessed.csv", index=False)
print(f"数据已保存为 data_preprocessed.csv")
print(f"最终数据形状: {df.shape}")
print(f"\n预处理后数据前5行:\n{df.head()}")
print(f"\n预处理后字段类型:\n{df.dtypes}")

# 构建二分类模型，划分训练测试集
X = df.drop(columns=['Response'])
y = df['Response']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# 3. 初始化 XGBoost 分类器
model = xgb.XGBClassifier(
    objective='binary:logistic',    # 二分类任务
    eval_metric='auc',               # 评估指标用 AUC
    n_estimators=200,                # 树的数量
    max_depth=5,                     # 树的最大深度
    learning_rate=0.1,               # 学习率
    scale_pos_weight=len(y[y==0]) / len(y[y==1]),  # 处理类别不平衡（正样本权重）
    random_state=42,
    n_jobs=-1                        # 使用所有 CPU 核心
)

# 4. 训练模型
model.fit(X_train, y_train)

# 5. 预测
y_pred = model.predict(X_test)           # 预测类别（0 或 1）
y_pred_proba = model.predict_proba(X_test)[:, 1]  # 预测为正类的概率（用于找高潜客户）

# 评估指标
print("Accuracy:", accuracy_score(y_test, y_pred))
print("Precision:", precision_score(y_test, y_pred))
print("Recall:", recall_score(y_test, y_pred))
print("F1:", f1_score(y_test, y_pred))
print("AUC:", roc_auc_score(y_test, y_pred_proba))

# 输出高潜客户（这里假设 test 数据就是你要预测的数据）
# 把预测概率拼回到测试集
high_value = X_test.copy()
high_value['Response_prob'] = y_pred_proba
high_value = high_value.sort_values('Response_prob', ascending=False)
high_value.to_csv("high_value_users.csv", index=False)


