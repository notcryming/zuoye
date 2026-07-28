# -*- coding: utf-8 -*-
"""
课程代码 08: 分类模型评估指标详解
说明: 直接运行即可,会生成 evaluation_混淆矩阵.png、evaluation_ROC曲线.png、evaluation_PR曲线.png
对应讲义章节: Day1 下午 - 评估标准详解

本文件逐步演示:
  1. 混淆矩阵的四个基本量(TP/FP/TN/FN)
  2. 由混淆矩阵推导出的各项指标(准确率/精确率/召回率/F1/特异性)
  3. ROC 曲线与 AUC
  4. PR 曲线(精确率-召回率曲线),在不平衡数据上比 ROC 更敏感
  5. 不同业务场景下应优先关注哪个指标
"""
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
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

print("=" * 60)
print("分类模型评估指标详解")
print("=" * 60)

# ============= 1. 准备数据与模型 =============
# 生成一个略带噪声的二分类数据
X, y = make_classification(n_samples=1000, n_features=8, n_informative=5,
                           n_redundant=2, weights=[0.7, 0.3],  # 7:3 的类别比例
                           flip_y=0.1, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

model = LogisticRegression(max_iter=1000, random_state=42)
model.fit(X_train, y_train)
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]  # 预测为正类的概率

# ============= 2. 混淆矩阵:一切的起点 =============
# 混淆矩阵是理解所有分类指标的基础
#        预测正   预测负
# 真实正   TP      FN   (真实正=TP+FN)
# 真实负   FP      TN   (真实负=FP+TN)
cm = confusion_matrix(y_test, y_pred)
tn, fp, fn, tp = cm.ravel()  # 按顺序解包: TN, FP, FN, TP

print("\n--- 1. 混淆矩阵的四个基本量 ---")
print(f"TP(真正例, 正确预测为正): {tp}")
print(f"FP(假正例, 误报):       {fp}")
print(f"FN(假负例, 漏报):       {fn}")
print(f"TN(真负例, 正确预测为负): {tn}")

# 可视化混淆矩阵
plt.figure(figsize=(7, 5))
sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
            xticklabels=['预测为负', '预测为正'],
            yticklabels=['真实为负', '真实为正'])
plt.title('评估 - 混淆矩阵')
plt.ylabel('真实标签')
plt.xlabel('预测标签')
plt.tight_layout()
plt.savefig('evaluation_混淆矩阵.png', dpi=100)
plt.close()

# ============= 3. 由混淆矩阵推导各项指标 =============
print("\n--- 2. 各项指标(手工计算 vs sklearn计算) ---")

# 准确率 Accuracy: 预测正确的占总数。平衡数据时好用,不平衡时会骗人
acc_manual = (tp + tn) / (tp + tn + fp + fn)
print(f"准确率 Accuracy   = (TP+TN)/全部 = {acc_manual:.4f}  (sklearn: {accuracy_score(y_test, y_pred):.4f})")

# 精确率 Precision: 预测为正的样本里,真正是正的比例。关注"误报"
prec_manual = tp / (tp + fp)
print(f"精确率 Precision  = TP/(TP+FP)    = {prec_manual:.4f}  (sklearn: {precision_score(y_test, y_pred):.4f})")

# 召回率 Recall(灵敏度/真正率 TPR): 真实为正的样本里,被找出来的比例。关注"漏报"
rec_manual = tp / (tp + fn)
print(f"召回率 Recall     = TP/(TP+FN)    = {rec_manual:.4f}  (sklearn: {recall_score(y_test, y_pred):.4f})")

# 特异性 Specificity(真负率 TNR): 真实为负的样本里,被正确判负的比例
spec_manual = tn / (tn + fp)
print(f"特异性 Specificity= TN/(TN+FP)    = {spec_manual:.4f}")

# F1-Score: 精确率和召回率的调和平均,综合两者
f1_manual = 2 * prec_manual * rec_manual / (prec_manual + rec_manual)
print(f"F1-Score          = 2PR/(P+R)     = {f1_manual:.4f}  (sklearn: {f1_score(y_test, y_pred):.4f})")

print("\n完整分类报告:")
print(classification_report(y_test, y_pred, target_names=['负类(0)', '正类(1)']))

# ============= 4. ROC 曲线与 AUC =============
# ROC: 横轴假正率 FPR=FP/(FP+TN), 纵轴真正率 TPR=TP/(TP+FN)=Recall
# 沿不同阈值绘制。AUC 是曲线下面积,越接近1越好,0.5表示随机猜测
print("\n--- 3. ROC 曲线与 AUC ---")
fpr, tpr, thresholds = roc_curve(y_test, y_prob)
roc_auc = auc(fpr, tpr)
print(f"AUC = {roc_auc:.4f}  (越接近1越好, 0.5=随机猜测)")

# ============= 5. PR 曲线 =============
# PR曲线: 横轴召回率, 纵轴精确率。在数据极度不平衡时,PR曲线比ROC更能反映问题
# 因为ROC的FPR分母(TN)很大,少数类变动对FPR影响小,显得过于乐观
print("\n--- 4. PR 曲线(精确率-召回率曲线) ---")
precision_arr, recall_arr, pr_thresholds = precision_recall_curve(y_test, y_prob)

# 可视化 ROC 和 PR 曲线
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# ROC 曲线
axes[0].plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC (AUC={roc_auc:.3f})')
axes[0].plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--', label='随机猜测')
axes[0].set_xlabel('假正率 FPR = FP/(FP+TN)')
axes[0].set_ylabel('真正率 TPR = TP/(TP+FN) = Recall')
axes[0].set_title('评估 - ROC 曲线')
axes[0].legend()
axes[0].grid(alpha=0.3)

# PR 曲线
axes[1].plot(recall_arr, precision_arr, color='green', lw=2, label='PR 曲线')
baseline = y_test.mean()  # 正类比例作为基线
axes[1].axhline(baseline, color='gray', linestyle='--', label=f'基线(正类占比={baseline:.2f})')
axes[1].set_xlabel('召回率 Recall')
axes[1].set_ylabel('精确率 Precision')
axes[1].set_title('评估 - PR 曲线')
axes[1].legend()
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.savefig('evaluation_曲线对比.png', dpi=100)
plt.close()

# ============= 6. 业务场景:该看哪个指标? =============
print("\n--- 5. 不同业务场景下应优先关注的指标 ---")
print("""
┌──────────────────────┬──────────────────┬──────────────────────────────────┐
│ 业务场景             │ 优先指标          │ 原因                             │
├──────────────────────┼──────────────────┼──────────────────────────────────┤
│ 癌症/疾病筛查        │ Recall 召回率    │ 宁可误诊也不能漏诊(漏报代价大)  │
│ 信用卡欺诈检测       │ Recall / PR-AUC  │ 漏掉一笔欺诈损失大,正样本极稀少 │
│ 垃圾邮件过滤         │ Precision 精确率 │ 不能把重要邮件判成垃圾(误报代价)│
│ 推荐系统点击预测     │ Precision 精确率 │ 推错的会打扰用户                 │
│ 类别平衡的普通分类   │ Accuracy 准确率  │ 各类样本相当,准确率可信         │
│ 综合考虑且不平衡     │ F1 / AUC         │ 平衡精确与召回,不受阈值影响     │
└──────────────────────┴──────────────────┴──────────────────────────────────┘
""")

print("已保存图像: evaluation_混淆矩阵.png, evaluation_曲线对比.png")
