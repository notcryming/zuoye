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
# 配置中文字体,保证图表中文正常显示
# plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
# plt.rcParams["axes.unicode_minus"] = False
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False
'''
任务描述**: 构建一个二分类模型,预测客户是否会流失。

1. 生成模拟客户数据(年龄、消费金额、使用时长、是否流失)
2. 进行数据预处理(标准化、处理类别特征)
3. 使用逻辑回归、SVM、随机森林训练模型
4. 输出分类报告、混淆矩阵、ROC曲线
5. 分析哪个模型效果最好,为什么
'''

# 1 生成模拟客户数据，全是数值型的数据，甚至是否流失都是0和1的结果
np.random.seed(42)
n_samples = 1000
data = pd.DataFrame({
    '年龄': np.random.randint(18, 65, n_samples),
    '月消费金额': np.random.exponential(200, n_samples),
    '使用时长_月': np.random.randint(1, 60, n_samples),
    '投诉次数': np.random.poisson(0.5, n_samples),
    '是否流失': np.zeros(n_samples, dtype=int)
})
data['是否流失'] = ((data['月消费金额'] < 100) | (data['投诉次数'] >= 3)).astype(int)

# 数据预处理，标准化月消费金额
consume_loged = np.log1p(data[['月消费金额']])
scaler_std = StandardScaler()
consume_scaled = scaler_std.fit_transform(consume_loged)
consume_df = pd.DataFrame(consume_scaled, columns=["月消费金额_标准化"])

age_scaled = scaler_std.fit_transform(data[['年龄']])
age_df = pd.DataFrame(age_scaled, columns=["年龄_标准化"])

usetime_scaled = scaler_std.fit_transform(data[['使用时长_月']])
usetime_df = pd.DataFrame(usetime_scaled, columns=["使用时长_月_标准化"])

# 构建二分类模型，划分训练测试集
X = pd.concat([
    age_df,             # 年龄
    consume_df,         # 标准化后的消费
    usetime_df,         # 标准化后的时间
    data[["投诉次数"]]   # 投诉次数原封不动
], axis=1)
y = data['是否流失']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# 使用随机森林训练模型
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

# 线性核SVM
X_train_scaled = scaler_std.fit_transform(X_train)
X_test_scaled = scaler_std.transform(X_test)
svm_linear = SVC(kernel='linear', random_state=42)
svm_linear.fit(X_train_scaled, y_train)
print(f"SVM(线性核)准确率: {accuracy_score(y_test, svm_linear.predict(X_test_scaled)):.2%}")

# RBF核SVM
svm_rbf = SVC(kernel='rbf', random_state=42)
svm_rbf.fit(X_train_scaled, y_train)
print(f"SVM(RBF核)准确率: {accuracy_score(y_test, svm_rbf.predict(X_test_scaled)):.2%}")

# ==================== 逻辑回归 ====================
lr = LogisticRegression(random_state=42, max_iter=1000)
lr.fit(X_train_scaled, y_train)
y_pred_lr = lr.predict(X_test_scaled)
y_prob_lr = lr.predict_proba(X_test_scaled)[:, 1]

print("\n" + "="*50)
print("逻辑回归分类报告")
print("="*50)
print(classification_report(y_test, y_pred_lr))

# 逻辑回归混淆矩阵
cm_lr = confusion_matrix(y_test, y_pred_lr)
plt.figure(figsize=(8, 6))
sns.heatmap(cm_lr, annot=True, fmt='d', cmap='Greens',
            xticklabels=['预测为0', '预测为1'],
            yticklabels=['真实为0', '真实为1'])
plt.title('逻辑回归 - 混淆矩阵')
plt.ylabel('真实标签')
plt.xlabel('预测标签')
plt.savefig('confusion_matrix_lr.png', dpi=100)
plt.close()
print("已保存: confusion_matrix_lr.png")

# 逻辑回归ROC曲线
fpr_lr, tpr_lr, _ = roc_curve(y_test, y_prob_lr)
roc_auc_lr = auc(fpr_lr, tpr_lr)
plt.figure(figsize=(8, 6))
plt.plot(fpr_lr, tpr_lr, color='green', lw=2, label=f'逻辑回归 ROC (AUC = {roc_auc_lr:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlabel('假正率(FPR)')
plt.ylabel('真正率(TPR)')
plt.title('逻辑回归 - ROC曲线')
plt.legend()
plt.savefig('roc_curve_lr.png', dpi=100)
plt.close()
print("已保存: roc_curve_lr.png")

# ==================== 三种模型对比 ====================
print("\n" + "="*60)
print("三种模型对比")
print("="*60)

# 收集各模型指标
models = {
    '随机森林': {
        'y_pred': y_pred,
        'y_prob': y_prob,
    },
    'SVM(线性核)': {
        'y_pred': svm_linear.predict(X_test_scaled),
        'y_prob': svm_linear.decision_function(X_test_scaled),  # SVM无predict_proba，用决策值
    },
    'SVM(RBF核)': {
        'y_pred': svm_rbf.predict(X_test_scaled),
        'y_prob': svm_rbf.decision_function(X_test_scaled),
    },
    '逻辑回归': {
        'y_pred': y_pred_lr,
        'y_prob': y_prob_lr,
    },
}

results = []
for name, m in models.items():
    acc = accuracy_score(y_test, m['y_pred'])
    prec = precision_score(y_test, m['y_pred'], zero_division=0)
    rec = recall_score(y_test, m['y_pred'], zero_division=0)
    f1 = f1_score(y_test, m['y_pred'], zero_division=0)
    fpr_i, tpr_i, _ = roc_curve(y_test, m['y_prob'])
    auc_i = auc(fpr_i, tpr_i)
    results.append({
        '模型': name,
        '准确率': f'{acc:.4f}',
        '精确率': f'{prec:.4f}',
        '召回率': f'{rec:.4f}',
        'F1-score': f'{f1:.4f}',
        'AUC': f'{auc_i:.4f}',
    })

compare_df = pd.DataFrame(results)
print(compare_df.to_string(index=False))

# 绘制多模型ROC对比图
plt.figure(figsize=(10, 8))
colors = ['darkorange', 'blue', 'red', 'green']
for idx, (name, m) in enumerate(models.items()):
    fpr_i, tpr_i, _ = roc_curve(y_test, m['y_prob'])
    auc_i = auc(fpr_i, tpr_i)
    plt.plot(fpr_i, tpr_i, color=colors[idx], lw=2,
             label=f'{name} (AUC = {auc_i:.2f})')
plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
plt.xlabel('假正率(FPR)')
plt.ylabel('真正率(TPR)')
plt.title('三种模型 ROC 曲线对比')
plt.legend(loc='lower right')
plt.savefig('roc_curve_compare.png', dpi=100)
plt.close()
print("\n已保存多模型ROC对比图: roc_curve_compare.png")

# ==================== 分析结论 ====================
print("\n" + "="*60)
print("模型效果分析")
print("="*60)
print("""
分析要点:
1. 随机森林: 作为树模型，天然对非线性关系建模能力强，且对特征缩放不敏感。
   在本数据集中，"是否流失"的标签是根据规则(月消费<100 或 投诉>=3)生成的，
   这是一个非线性决策边界，随机森林通常能很好地捕捉这种规则。

2. SVM(线性核): 通过寻找最大间隔超平面来分类，适合线性可分数据。
   但本数据的决策边界是非线性的(由阈值规则构成)，线性核SVM的表现会稍逊。

3. SVM(RBF核): RBF核可以将数据映射到高维空间，能处理非线性边界，
   表现通常优于线性核，但可解释性不如随机森林和逻辑回归。

4. 逻辑回归: 建模的是特征的线性组合与概率的关系，对本数据集的
   非线性规则边界拟合能力有限，但优势是可解释性最强，
   能直接看到各特征对流失概率的影响方向和大小。

结论: 通常随机森林效果最好，因为它天然适合处理由阈值规则生成的
非线性决策边界，且不需要额外的特征缩放。逻辑回归虽然可解释性强，
但在非线性数据上表现会略逊一筹。
""")