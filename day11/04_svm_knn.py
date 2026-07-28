# -*- coding: utf-8 -*-
"""
课程代码 04: 支持向量机(SVM)与K近邻(KNN)实战
说明: 直接运行即可,会生成 SVM_RBF核决策边界.png 和 KNN_K=5决策边界.png
对应讲义章节: Day1 下午 - SVM 与 KNN
"""
import numpy as np
import matplotlib.pyplot as plt
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.datasets import make_moons
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.preprocessing import StandardScaler

# 配置中文字体,保证图表中文正常显示
# plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei", "WenQuanYi Micro Hei", "Heiti TC"]
# plt.rcParams["axes.unicode_minus"] = False
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 生成非线性可分数据
X, y = make_moons(n_samples=300, noise=0.3, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# 标准化特征(对SVM和KNN很重要)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 可视化函数
def plot_decision_boundary(clf, X, y, title):
    x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
    y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
    xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02),
                         np.arange(y_min, y_max, 0.02))
    Z = clf.predict(np.c_[xx.ravel(), yy.ravel()])
    Z = Z.reshape(xx.shape)

    plt.figure(figsize=(10, 6))
    plt.contourf(xx, yy, Z, alpha=0.3, cmap='coolwarm')
    plt.scatter(X[:, 0], X[:, 1], c=y, edgecolors='k', cmap='coolwarm')
    plt.title(title)
    plt.xlabel('特征1')
    plt.ylabel('特征2')
    plt.savefig(f'{title}.png', dpi=100)
    plt.close()

# ============= SVM =============
print("="*50)
print("支持向量机(SVM)")
print("="*50)

# 线性核SVM
svm_linear = SVC(kernel='linear', random_state=42)
svm_linear.fit(X_train_scaled, y_train)
print(f"SVM(线性核)准确率: {accuracy_score(y_test, svm_linear.predict(X_test_scaled)):.2%}")

# RBF核SVM
svm_rbf = SVC(kernel='rbf', random_state=42)
svm_rbf.fit(X_train_scaled, y_train)
print(f"SVM(RBF核)准确率: {accuracy_score(y_test, svm_rbf.predict(X_test_scaled)):.2%}")

plot_decision_boundary(svm_rbf, X_test_scaled, y_test, 'SVM_RBF核决策边界')

# ============= KNN =============
print(f"\n{'='*50}")
print("K近邻(KNN)")
print(f"{'='*50}")

# 尝试不同的K值
for k in [1, 3, 5, 7, 15]:
    knn = KNeighborsClassifier(n_neighbors=k)
    knn.fit(X_train_scaled, y_train)
    acc = accuracy_score(y_test, knn.predict(X_test_scaled))
    print(f"K={k}: 准确率 = {acc:.2%}")

# 使用最优K=5可视化
knn_best = KNeighborsClassifier(n_neighbors=5)
knn_best.fit(X_train_scaled, y_train)
plot_decision_boundary(knn_best, X_test_scaled, y_test, 'KNN_K=5决策边界')
print("\n已保存决策边界图: SVM_RBF核决策边界.png, KNN_K=5决策边界.png")
