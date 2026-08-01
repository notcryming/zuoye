# ==============================
# 保险用户响应预测
# 数据预处理 + XGBoost 模型训练
# 严格按数据类型 + 可视化依据 + 业务逻辑处理
# ==============================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score

# ==============================
# 1. 读取原始数据
# ==============================
df = pd.read_excel("data.xlsx")

# ==============================
# 2. 【依据可视化】数据预处理（最科学版本）
# ==============================

# 1. 删除无用列
df = df.drop(columns=["id"], errors="ignore")

# 2. 去重
df = df.drop_duplicates()

# 3. 缺失值填充
df = df.fillna(0)

# --------------------------
# 无序分类特征（0/1 编码）
# --------------------------
df["Gender"] = df["Gender"].map({"Male": 1, "Female": 0})
df["Vehicle_Damage"] = df["Vehicle_Damage"].map({"Yes": 1, "No": 0})

# --------------------------
# 有序分类特征（保留顺序 → 按数值处理）
# --------------------------
df["Vehicle_Age"] = df["Vehicle_Age"].map({
    "< 1 Year": 0,
    "1-2 Year": 1,
    "> 2 Years": 2
})

# --------------------------
# 连续数值 → 分箱（保费右偏）
# --------------------------
bins = [0, 10000, 25000, 50000, np.inf]
labels = [0, 1, 2, 3]
df["Annual_Premium_bin"] = pd.cut(
    df["Annual_Premium"], bins=bins, labels=labels, right=False
)
df = df.drop(columns=["Annual_Premium"])

# --------------------------
# 无序分类 → 必须转 category
# --------------------------
df["Policy_Sales_Channel"] = df["Policy_Sales_Channel"].astype("category")

# --------------------------
# 必须保持数值型的特征（不动）
# --------------------------
# Age, Vintage, Region_Code → 全部保持数值

# ==============================
# 2.5 检查样本不平衡 & 保存预处理数据
# ==============================
print("\n==============================")
print("标签 Response 的分布情况：")
print(df["Response"].value_counts())
print("\n标签 Response 的比例：")
print(df["Response"].value_counts(normalize=True))
print("==============================\n")

# 保存预处理后的数据（将数据保存为csv文件）
df.to_csv("data_preprocessed.csv", index=False, encoding="utf-8-sig")
print("✅ 预处理后的数据已保存至：data_preprocessed.csv\n")

# ==============================
# 3. 数据集划分
# ==============================
X = df.drop(columns=["Response"])
y = df["Response"]

X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

print("~~~~~~~~~~~~~~~~~~~~~~~~~")
print(X_test.shape)

# 计算 scale_pos_weight (负样本数量 / 正样本数量)
neg_count = (y_train == 0).sum()
pos_count = (y_train == 1).sum()
scale_weight = neg_count / pos_count
print(f"\n✅ 已计算 XGBoost 正负样本平衡权重 scale_pos_weight = {scale_weight:.2f}\n")

# ==============================
# 4. XGBoost 模型训练（支持 category）
# ==============================
model = xgb.XGBClassifier(
    n_estimators=200,
    max_depth=6,
    learning_rate=0.1,
    enable_categorical=True,  # 关键：支持分类特征
    scale_pos_weight=scale_weight,  # 关键：解决正负样本不平衡问题
    eval_metric="logloss",
    random_state=42
)

model.fit(X_train, y_train)

# ==============================
# 5. 模型评估
# ==============================
y_pred = model.predict(X_test)
y_prob = model.predict_proba(X_test)[:, 1]

print("=" * 50)
print("模型评估报告")
print("=" * 50)
print(classification_report(y_test, y_pred))
print(f"AUC 得分: {roc_auc_score(y_test, y_prob):.4f}")

# ==============================
# 6. 输出高潜力用户（需要营销）
# ==============================
test_result = X_test.copy()
test_result["Response_pred"] = y_pred
test_result["Response_prob"] = y_prob

high_value_users = test_result[test_result["Response_pred"] == 1].copy()
high_value_users.to_csv("high_value_users.csv", index=False, encoding="utf-8-sig")

print("\n✅ 高潜力营销用户已保存：high_value_users.csv")
print(f"共 {len(high_value_users)} 位用户需要重点营销")