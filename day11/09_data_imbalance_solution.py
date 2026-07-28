# -*- coding: utf-8 -*-
"""
课程代码 09: 数据不平衡问题与解决方案
说明: 直接运行即可,会生成 imbalance_*.png
      需要安装: pip install imbalanced-learn xgboost
对应讲义章节: Day1 下午 - 数据不平衡的解决方案

本文件演示:
  1. 构造一个严重不平衡的数据集(正类仅占 5%)
  2. 不做任何处理直接训练 -> 看准确率"虚高"的陷阱
  3. 方案一:重采样(随机欠采样 + SMOTE 过采样)
  4. 方案二:类别权重加权
        ✅ 逻辑回归：class_weight='balanced'
        ✅ XGBoost两种实现：
           ① scale_pos_weight：二分类首选，最简全局类别加权（等价LR balanced）
           ② sample_weight：逐样本自定义权重，灵活性更高
  5. 方案三:阈值调整
  6. 对比各方案在 Recall / F1 / AUC 上的效果
"""
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (classification_report, confusion_matrix,
                             recall_score, f1_score, roc_auc_score, accuracy_score)
# 导入XGBoost
import xgboost as xgb

# 配置中文字体,保证图表中文正常显示
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


print("=" * 60)
print("数据不平衡问题与解决方案【LR + XGBoost双模型对比】")
print("=" * 60)

# ============= 1. 构造严重不平衡数据(正类5%) =============
X, y = make_classification(n_samples=2000, n_features=6, n_informative=4,
                           n_redundant=1, weights=[0.95, 0.05],  # 95:5 正负样本比例
                           flip_y=0.02, random_state=42)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

print(f"\n训练集样本数: {len(y_train)}, 正类占比: {y_train.mean():.2%}")
print(f"测试集样本数: {len(y_test)}, 正类占比: {y_test.mean():.2%}")

# 统计训练集正负样本数量（给XGB加权使用）
num_neg = np.sum(y_train == 0)
num_pos = np.sum(y_train == 1)
print(f"训练集负类(多数类)数量：{num_neg}，正类(少数类)数量：{num_pos}\n")


# 评估辅助函数:打印关键指标并返回字典
def evaluate(name, y_true, y_pred, y_prob):
    acc = accuracy_score(y_true, y_pred)
    rec = recall_score(y_true, y_pred)         # 召回率:少数类被找出来的比例
    f1 = f1_score(y_true, y_pred)
    auc = roc_auc_score(y_true, y_prob)
    print(f"\n--- {name} ---")
    print(f"准确率 Accuracy: {acc:.4f}   召回率 Recall: {rec:.4f}   F1: {f1:.4f}   AUC: {auc:.4f}")
    return {'方案': name, 'Accuracy': acc, 'Recall': rec, 'F1': f1, 'AUC': auc}


results = []

# ============= 2. 基线:不做任何处理(逻辑回归) =============
print("\n" + "=" * 60)
print("基线:不做任何处理直接训练(准确率陷阱)")
print("=" * 60)
# 模型会偏向多数类,把几乎所有样本预测为负类,准确率依然很高但召回率极低
base_model = LogisticRegression(max_iter=1000, random_state=42)
base_model.fit(X_train, y_train)
results.append(evaluate('基线-LR(不处理)',
                        y_test, base_model.predict(X_test),
                        base_model.predict_proba(X_test)[:, 1]))
print("混淆矩阵:\n", confusion_matrix(y_test, base_model.predict(X_test)))

# ============= 3. 方案一:重采样(随机欠采样 + SMOTE 过采样)【LR训练】 =============
print("\n" + "=" * 60)
print("方案一:重采样(随机欠采样 + SMOTE 过采样)")
print("=" * 60)

try:
    from imblearn.over_sampling import SMOTE
    from imblearn.under_sampling import RandomUnderSampler

    # 3.1 随机欠采样:从多数类随机抽取,使两类数量相等
    rus = RandomUnderSampler(random_state=42)
    X_train_rus, y_train_rus = rus.fit_resample(X_train, y_train)
    print(f"\n欠采样后训练集正类占比: {y_train_rus.mean():.2%} (样本数={len(y_train_rus)})")

    model_rus = LogisticRegression(max_iter=1000, random_state=42)
    model_rus.fit(X_train_rus, y_train_rus)
    results.append(evaluate('随机欠采样-LR',
                            y_test, model_rus.predict(X_test),
                            model_rus.predict_proba(X_test)[:, 1]))

    # 3.2 SMOTE 过采样:插值生成少数类样本
    smote = SMOTE(random_state=42)
    X_train_smote, y_train_smote = smote.fit_resample(X_train, y_train)
    print(f"\nSMOTE过采样后训练集正类占比: {y_train_smote.mean():.2%} (样本数={len(y_train_smote)})")

    model_smote = LogisticRegression(max_iter=1000, random_state=42)
    model_smote.fit(X_train_smote, y_train_smote)
    results.append(evaluate('SMOTE过采样-LR',
                            y_test, model_smote.predict(X_test),
                            model_smote.predict_proba(X_test)[:, 1]))
    imb_available = True

except ImportError:
    print("\n⚠️ imbalanced-learn 未安装,跳过重采样方案。请运行: pip install imbalanced-learn")
    imb_available = False

# ============= 4. 方案二:类别权重加权 【LR + XGBoost三种方式对照】 =============
print("\n" + "=" * 60)
print("方案二：类别加权（不修改原始数据，仅调整损失梯度惩罚）")
print("=" * 60)

# ---------------------- 4.1 逻辑回归：class_weight='balanced' ----------------------
print("\n【1】逻辑回归 class_weight='balanced'")
model_cw = LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42)
model_cw.fit(X_train, y_train)
results.append(evaluate("LR-class_weight-balanced",
                        y_test, model_cw.predict(X_test),
                        model_cw.predict_proba(X_test)[:, 1]))

# ---------------------- 4.2 XGBoost 方式1：scale_pos_weight（二分类首选、最简单） ----------------------
"""
核心说明：
XGBoost没有class_weight参数，二分类不平衡专用参数
计算公式：scale_pos_weight = 负类样本总数 / 正类样本总数
作用：训练时放大少数类正样本的梯度权重，错分正样本损失惩罚更大
完全等价LR class_weight='balanced'思路，工业界二分类不平衡最常用方案
优点：一行参数搞定、速度快、无数据丢失、不生成噪声样本
"""
print("\n【2】XGBoost scale_pos_weight 全局类别加权（推荐）")
scale_pos = num_neg / num_pos
xgb_scale = xgb.XGBClassifier(
    scale_pos_weight=scale_pos,
    n_estimators=100,
    max_depth=3,
    random_state=42,
    use_label_encoder=False,
    eval_metric="logloss"
)
xgb_scale.fit(X_train, y_train)
results.append(evaluate("XGB-scale_pos_weight",
                        y_test, xgb_scale.predict(X_test),
                        xgb_scale.predict_proba(X_test)[:, 1]))

# ---------------------- 4.3 XGBoost 方式2：sample_weight 逐样本自定义权重（最灵活） ----------------------
"""
核心说明：
给训练集每一条样本单独设置权重数组，传入fit的sample_weight参数
规则：负类权重=1，正类权重=正负样本比值；和scale_pos_weight效果一致，但扩展性更强
适用场景：
1. 多分类不平衡（无法使用scale_pos_weight）
2. 业务需要给不同样本设置差异化重要度（风控坏账优先级、客户分层权重）
"""
print("\n【3】XGBoost sample_weight 逐样本自定义权重")
# 构建样本权重数组：正样本赋予更高权重
sample_weights = np.where(y_train == 1, num_neg / num_pos, 1)
xgb_sample_w = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=3,
    random_state=42,
    use_label_encoder=False,
    eval_metric="logloss"
)
# 传入逐样本权重
xgb_sample_w.fit(X_train, y_train, sample_weight=sample_weights)
results.append(evaluate("XGB-sample_weight自定义",
                        y_test, xgb_sample_w.predict(X_test),
                        xgb_sample_w.predict_proba(X_test)[:, 1]))

# ============= 5. 方案三:阈值调整（基于基线模型下调阈值提升召回） =============
print("\n" + "=" * 60)
print("方案三:阈值调整(默认0.5 → 调低到0.3)")
print("=" * 60)
# 模型输出概率,默认 ≥0.5 判为正类。把阈值调低,更愿意判正,提高召回率
y_prob = base_model.predict_proba(X_test)[:, 1]
y_pred_low_thr = (y_prob >= 0.3).astype(int)
results.append(evaluate('阈值调整0.3-LR基线',
                        y_test, y_pred_low_thr, y_prob))

# ============= 6. 方案对比可视化 =============
print("\n" + "=" * 60)
print("各方案效果对比汇总表")
print("=" * 60)

import pandas as pd
df_results = pd.DataFrame(results)
print("\n", df_results.to_string(index=False))

# 画对比柱状图:关注 Recall 和 F1(不平衡数据的重点指标),而非 Accuracy
metrics = ['Recall', 'F1', 'AUC']
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#FFA07A', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9']
for ax, metric in zip(axes, metrics):
    ax.bar(df_results['方案'], df_results[metric], color=colors)
    ax.set_title(f'各方案 {metric} 对比', fontsize=12)
    ax.set_ylabel(metric, fontsize=11)
    ax.tick_params(axis='x', rotation=35)
    ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig('imbalance_LR_XGB方案对比.png', dpi=100)
plt.close()

# ============= 7. 总结结论 =============
print("\n" + "=" * 60)
print("关键结论：LR 与 XGBoost 处理数据不平衡差异")
print("=" * 60)
print("1、准确率不能衡量不平衡数据效果，优先看 Recall、F1、AUC")
print("2、逻辑回归：线性模型拟合能力弱，极度依赖SMOTE过采样+class_weight加权")
print("3、XGBoost树模型天然抗不平衡能力更强：")
print("   ✅ scale_pos_weight：二分类场景首选，最简高效，替代LR balanced")
print("   ✅ sample_weight：灵活自定义权重，多用于多分类、个性化样本加权场景")
print("4、重采样会改动原始数据分布；类别加权全程保留全部样本，泛化效果更稳定")
print("5、阈值调优属于预测后处理，所有模型通用，用来权衡精确率/召回率业务需求")
print("\n图片已保存：imbalance_LR_XGB方案对比.png")
