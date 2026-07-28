# -*- coding: utf-8 -*-
"""
课程代码 05: 特征工程与模型评估实战
说明: 直接运行即可,会生成 confusion_matrix.png 和 roc_curve.png
对应讲义章节: Day1 下午 - 特征工程与模型评估
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, PolynomialFeatures
from sklearn.model_selection import cross_val_score, learning_curve, validation_curve
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import confusion_matrix, roc_curve, auc, classification_report
from sklearn.datasets import make_classification
import seaborn as sns

# 配置中文字体,保证图表中文正常显示
# plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
# plt.rcParams["axes.unicode_minus"] = False
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 创建示例数据
np.random.seed(42)
data = pd.DataFrame({
    '年龄': np.random.randint(18, 70, 100),
    '收入': np.random.randint(3000, 50000, 100),
    '城市': np.random.choice(['北京', '上海', '广州', '深圳'], 100),
    '学历': np.random.choice(['高中', '本科', '硕士', '博士'], 100),
    '是否购买': np.random.randint(0, 2, 100)
})

print("="*50)
print("特征工程实战")
print("="*50)
print("\n原始数据:")
print(data.head())

# 1. 特征编码
print("\n--- 1. 特征编码 ---")
encoder = OneHotEncoder(sparse_output=False)
city_encoded = encoder.fit_transform(data[['城市']])
city_df = pd.DataFrame(city_encoded, columns=encoder.categories_[0])
print(f"编码后的城市特征:\n{city_df.head()}")

# 2. 特征缩放
print("\n--- 2. 特征缩放 ---")
scaler_std = StandardScaler()
income_scaled = scaler_std.fit_transform(data[['收入']])
print(f"标准化后收入(前5个): {income_scaled[:5].flatten()}")

scaler_minmax = MinMaxScaler()
income_norm = scaler_minmax.fit_transform(data[['收入']])
print(f"归一化后收入(前5个): {income_norm[:5].flatten()}")

# 3. 多项式特征
print("\n--- 3. 多项式特征 ---")
poly = PolynomialFeatures(degree=2, interaction_only=True)
X_poly = poly.fit_transform(data[['年龄', '收入']])
print(f"多项式特征名称: {poly.get_feature_names_out(['年龄', '收入'])}")
print(f"特征形状从 (100, 2) 变为 (100, {X_poly.shape[1]})")

# 4. 模型评估指标
print("\n--- 4. 模型评估 ---")
X, y = make_classification(n_samples=500, n_features=10, n_informative=5,
                           random_state=42, flip_y=0.1)

from sklearn.model_selection import train_test_split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

rf = RandomForestClassifier(n_estimators=50, random_state=42)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)
y_prob = rf.predict_proba(X_test)[:, 1]

print(f"\n分类报告:\n{classification_report(y_test, y_pred)}")

# 混淆矩阵
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(8, 6))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['预测为0', '预测为1'],
            yticklabels=['真实为0', '真实为1'])
plt.title('混淆矩阵')
plt.ylabel('真实标签')
plt.xlabel('预测标签')
plt.savefig('confusion_matrix.png', dpi=100)
plt.close()
print("已保存混淆矩阵: confusion_matrix.png")

# ROC曲线
fpr, tpr, thresholds = roc_curve(y_test, y_prob)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(8, 6))
plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC曲线 (AUC = {roc_auc:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlabel('假正率(FPR)')
plt.ylabel('真正率(TPR)')
plt.title('ROC曲线')
plt.legend()
plt.savefig('roc_curve.png', dpi=100)
plt.close()
print("已保存ROC曲线: roc_curve.png")
