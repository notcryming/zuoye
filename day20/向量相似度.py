import os
import numpy as np
from langchain_huggingface import HuggingFaceEmbeddings
from sklearn.metrics.pairwise import cosine_similarity

# 配置 HuggingFace 国内镜像加速下载，避免网络超时导致模型加载失败
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

local_model_path = "./model/bge-large-zh-v1.5"

# 加载本地 BGE 嵌入模型（bge-large-zh）
print("▶ 正在加载 HuggingFace BGE 嵌入模型 (本地路径)...")
embeddings = HuggingFaceEmbeddings(
    model_name=local_model_path,
    model_kwargs={"device": "cuda"},  # 无 GPU 可改为 'cpu'
    encode_kwargs={"normalize_embeddings": True}  # BGE 模型必须开启标准化
)
print("✅ 嵌入模型加载完成！\n")

# ==================== 待编码的 5 个句子 ====================
sentences = [
    "Java开发工程师要求3年以上经验",      # 0
    "Python岗位要求熟悉Django框架",      # 1
    "公司节日福利包括购物卡和电影票",     # 2
    "员工享受带薪年假和五险一金",         # 3
    "Java高级工程师需精通JVM调优"         # 4
]


# ==================== 任务1：测试不同文本的向量表示 ====================
print("=" * 60)
print("任务1：测试不同文本的向量表示")
print("=" * 60)

# embed_documents 接收字符串列表，返回向量列表（list of list[float]）
vectors = embeddings.embed_documents(sentences)
vectors = np.array(vectors)  # 转为 numpy 数组方便后续运算

print(f"\n向量维度（每个句子被编码为 {vectors.shape[1]} 维向量）")
print(f"句子数量：{vectors.shape[0]}\n")

for i, sent in enumerate(sentences):
    print(f"句子{i+1}: {sent}")
    print(f"  向量维度: {vectors[i].shape[0]}")
    print(f"  前5个数值: {vectors[i][:5]}")
    print()

# ==================== 任务2：计算语义相似度 ====================
print("=" * 60)
print("任务2：计算 5 个句子两两之间的余弦相似度")
print("=" * 60)

# cosine_similarity 输入 shape: (n_samples, n_features)，输出 (n, n) 相似度矩阵
sim_matrix = cosine_similarity(vectors)

# 打印相似度矩阵（保留4位小数）
print("\n相似度矩阵 (5x5)：\n")
# 表头
header = "          " + "  ".join([f" 句{i+1} " for i in range(len(sentences))])
print(header)
for i in range(len(sentences)):
    row = "  ".join([f"{sim_matrix[i][j]:6.4f}" for j in range(len(sentences))])
    print(f"句{i+1}  |  {row}")

# 找出最相似的句子对（排除自己与自己，即 i == j）
print("\n最相似的句子对（排除自身）：")
max_sim = -1.0
max_pair = (0, 0)
n = len(sentences)
for i in range(n):
    for j in range(i + 1, n):  # 只看上三角，避免重复
        if sim_matrix[i][j] > max_sim:
            max_sim = sim_matrix[i][j]
            max_pair = (i, j)

i, j = max_pair
print(f"  句子{i+1}: {sentences[i]}")
print(f"  句子{j+1}: {sentences[j]}")
print(f"  余弦相似度: {max_sim:.4f}\n")

# ==================== 任务3：实战问答 ====================
print("=" * 60)
print("任务3：实战问答 —— 检索与用户问题最相似的 Top 2")
print("=" * 60)

query = "Java岗位有什么要求？"
print(f"\n用户提问: {query}\n")

# 将用户问题编码为向量
query_vec = embeddings.embed_query(query)  # 返回 list[float]
query_vec = np.array(query_vec).reshape(1, -1)  # reshape 成 (1, dim) 供 cosine_similarity 使用

# 计算问题与 5 个句子的相似度
sims = cosine_similarity(query_vec, vectors)[0]  # 取出长度为 5 的一维数组

# 打印每个句子的相似度
print("问题与各句子的相似度：")
for idx, sent in enumerate(sentences):
    print(f"  句子{idx+1}: {sent}  ->  相似度: {sims[idx]:.4f}")

# 按相似度降序排序，取 Top 2
top2_idx = np.argsort(sims)[::-1][:2]

print("\n最相似的 Top 2 句子：")
for rank, idx in enumerate(top2_idx, start=1):
    print(f"  Top{rank}: {sentences[idx]}  (相似度: {sims[idx]:.4f})")
