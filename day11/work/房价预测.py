import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.preprocessing import StandardScaler, MinMaxScaler, OneHotEncoder, PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (confusion_matrix, accuracy_score, precision_score,
                             recall_score, f1_score, roc_curve, auc,
                             precision_recall_curve, classification_report)
from sklearn.datasets import fetch_california_housing

# 配置中文字体,保证图表中文正常显示
# plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
# plt.rcParams["axes.unicode_minus"] = False
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
'''
练习任务1: 房价预测

**任务描述**: 使用加州房价数据集,完成以下任务:

1. 加载数据并进行探索性分析
2. 进行特征工程(标准化、特征选择)
3. 使用线性回归、决策树、随机森林分别训练模型
4. 比较三种模型的性能(MSE、R²)
5. 输出特征重要性排序
'''
# 加载数据
housing = fetch_california_housing()
X = pd.DataFrame(housing.data, columns=housing.feature_names)
y = housing.target  # 房价中位数（单位：十万美元）

print("="*60)
print("加州房价数据集")
print("="*60)
print(f"数据形状: {X.shape}")
print(f"特征名称: {housing.feature_names}")
print(f"\n前5行数据:")
print(X.head())
print(f"\n数据统计描述:")
print(X.describe())
print(f"\n目标值(房价)统计:")
print(f"  最小值: {y.min():.2f}, 最大值: {y.max():.2f}, 均值: {y.mean():.2f}, 中位数: {np.median(y):.2f}")

# 探索性分析：特征分布直方图
fig, axes = plt.subplots(2, 4, figsize=(20, 10))
for idx, col in enumerate(X.columns):
    ax = axes[idx // 4, idx % 4]
    ax.hist(X[col], bins=50, color='steelblue', edgecolor='white', alpha=0.7)
    ax.set_title(f'{col} 分布', fontsize=12)
    ax.set_xlabel(col)
    ax.set_ylabel('频数')
plt.suptitle('加州房价数据集 - 特征分布', fontsize=16)
plt.tight_layout()
plt.savefig('feature_distributions.png', dpi=100)
plt.close()
print("\n已保存特征分布图: feature_distributions.png")

# 探索性分析：特征与房价的相关性热力图
df_full = X.copy()
df_full['房价'] = y
corr = df_full.corr()
plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdBu_r', center=0, square=True)
plt.title('特征相关性热力图')
plt.tight_layout()
plt.savefig('correlation_heatmap.png', dpi=100)
plt.close()
print("已保存相关性热力图: correlation_heatmap.png")

# ==================== 2. 特征工程 ====================
print("\n" + "="*60)
print("特征工程")
print("="*60)

# 标准化
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_scaled = pd.DataFrame(X_scaled, columns=X.columns)
print("标准化完成，前5行:")
print(X_scaled.head())

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(
    X_scaled, y, test_size=0.3, random_state=42
)
print(f"\n训练集: {X_train.shape[0]} 样本, 测试集: {X_test.shape[0]} 样本")

# ==================== 3. 训练三种模型 ====================
print("\n" + "="*60)
print("模型训练")
print("="*60)

from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 3.1 线性回归
lr = LinearRegression()
lr.fit(X_train, y_train)
y_pred_lr = lr.predict(X_test)

# 3.2 决策树
dt = DecisionTreeRegressor(random_state=42, max_depth=10)
dt.fit(X_train, y_train)
y_pred_dt = dt.predict(X_test)

# 3.3 随机森林
rf = RandomForestRegressor(n_estimators=100, random_state=42, max_depth=15)
rf.fit(X_train, y_train)
y_pred_rf = rf.predict(X_test)

# ==================== 4. 比较模型性能 ====================
print("\n" + "="*60)
print("模型性能对比 (MSE、R²)")
print("="*60)

models = {
    '线性回归': y_pred_lr,
    '决策树': y_pred_dt,
    '随机森林': y_pred_rf,
}

results = []
for name, y_pred in models.items():
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mse)
    results.append({
        '模型': name,
        'MSE': f'{mse:.4f}',
        'RMSE': f'{rmse:.4f}',
        'R²': f'{r2:.4f}',
    })

compare_df = pd.DataFrame(results)
print(compare_df.to_string(index=False))

# 绘制预测值 vs 真实值散点图
fig, axes = plt.subplots(1, 3, figsize=(20, 6))
for idx, (name, y_pred) in enumerate(models.items()):
    ax = axes[idx]
    ax.scatter(y_test, y_pred, alpha=0.3, s=10)
    ax.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()],
            'r--', lw=2)
    ax.set_xlabel('真实房价')
    ax.set_ylabel('预测房价')
    ax.set_title(f'{name}\nMSE={mean_squared_error(y_test, y_pred):.4f}, R²={r2_score(y_test, y_pred):.4f}')
plt.suptitle('三种模型预测值 vs 真实值', fontsize=16)
plt.tight_layout()
plt.savefig('prediction_comparison.png', dpi=100)
plt.close()
print("\n已保存预测对比图: prediction_comparison.png")

# ==================== 5. 特征重要性排序 ====================
print("\n" + "="*60)
print("特征重要性排序")
print("="*60)

# 随机森林的特征重要性
rf_importance = pd.DataFrame({
    '特征': X.columns,
    '随机森林重要性': rf.feature_importances_,
}).sort_values('随机森林重要性', ascending=False)

# 线性回归的系数绝对值（标准化后可比）
lr_importance = pd.DataFrame({
    '特征': X.columns,
    '线性回归系数': lr.coef_,
})
lr_importance['线性回归|系数|'] = lr_importance['线性回归系数'].abs()
lr_importance = lr_importance.sort_values('线性回归|系数|', ascending=False)

# 决策树的特征重要性
dt_importance = pd.DataFrame({
    '特征': X.columns,
    '决策树重要性': dt.feature_importances_,
}).sort_values('决策树重要性', ascending=False)

print("\n随机森林特征重要性:")
print(rf_importance.to_string(index=False))
print(f"\n线性回归系数(按绝对值排序):")
print(lr_importance[['特征', '线性回归系数', '线性回归|系数|']].to_string(index=False))
print(f"\n决策树特征重要性:")
print(dt_importance.to_string(index=False))

# 绘制特征重要性对比图
fig, axes = plt.subplots(1, 3, figsize=(20, 6))

for idx, (title, df_imp, col) in enumerate([
    ('随机森林', rf_importance, '随机森林重要性'),
    ('决策树', dt_importance, '决策树重要性'),
    ('线性回归(|系数|)', lr_importance, '线性回归|系数|'),
]):
    ax = axes[idx]
    ax.barh(df_imp['特征'], df_imp[col], color='steelblue')
    ax.set_xlabel('重要性' if idx < 2 else '|系数|')
    ax.set_title(f'{title} 特征重要性')
    ax.invert_yaxis()

plt.suptitle('三种模型特征重要性对比', fontsize=16)
plt.tight_layout()
plt.savefig('feature_importance.png', dpi=100)
plt.close()
print("\n已保存特征重要性图: feature_importance.png")

# ==================== 分析结论 ====================
print("\n" + "="*60)
print("分析结论")
print("="*60)
print(f"""
1. 模型性能:
   - 随机森林表现最好 (R²最高, MSE最低)，因为它能捕捉特征间的非线性关系
   - 决策树次之，单棵树容易过拟合，泛化能力不如随机森林
   - 线性回归表现相对较弱，因为房价与特征间存在非线性关系

2. 特征重要性:
   - 随机森林和决策树通常认为 MedInc(地区收入中位数) 是最重要的特征
   - 线性回归的系数反映的是线性影响方向和大小，标准化后可直接比较
   - 三种模型对特征重要性的排序可能略有不同，但收入中位数通常排名靠前

3. 改进方向:
   - 可尝试网格搜索调参优化随机森林
   - 可对特征做多项式变换或交互特征提升线性回归表现
   - 可尝试梯度提升树(GBDT/XGBoost)进一步提升性能
""")






