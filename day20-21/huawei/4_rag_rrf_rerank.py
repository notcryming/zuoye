import os
import torch
import jieba
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.retrievers import BM25Retriever
from dotenv import load_dotenv

load_dotenv()

# ===================== 配置 =====================
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

# 模型路径
local_embed_path = r"C:\Users\ASUS\Desktop\shixun1\day20-21\model\bge-large-zh-v1.5"
# bge-reranker-base 来自 GitHub 开源项目 BAAI/bge-reranker-base，已下载到本地
local_rerank_path = r"C:\Users\ASUS\Desktop\shixun1\day20-21\model\bge-reranker-base"

# 检索参数
TOP_K = 8            # 每路粗排召回数量
RRF_K = 60           # RRF 倒数排名融合常数（经验值 60）
FINAL_TOP_K = 5      # 融合后保留多少条进入精排
RERANK_TOP_K = 3     # 精排后最终送入 LLM 的文档数


# ===================== 本地 Reranker（BAAI/bge-reranker-base）=====================
class LocalReranker:
    """
    基于 BAAI/bge-reranker-base 的本地重排序器。
    该模型采用 Cross-Encoder 架构，将 (query, doc) 拼接后输入模型，
    输出一个相关性分数，比双塔 Embedding 更精准，适合作为精排。
    项目地址：https://github.com/FlagOpen/FlagEmbedding
    """

    def __init__(self, model_path):
        print(f"▶ 正在加载本地 Reranker 模型: {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def rank(self, query, docs):
        """对召回的文档按与 query 的相关性重新打分排序"""
        if not docs:
            return []

        pairs = [[query, doc.page_content] for doc in docs]
        with torch.no_grad():
            inputs = self.tokenizer(
                pairs,
                padding=True,
                truncation=True,
                return_tensors="pt",
                max_length=512,
            )
            scores = self.model(**inputs, return_dict=True).logits.view(-1).float()
            scores = scores.tolist()

        # 按相关性分数从高到低排序
        ranked = sorted(zip(docs, scores), key=lambda x: x[1], reverse=True)
        return [doc for doc, _ in ranked]


# 全局只加载一次，避免重复加载模型
reranker = LocalReranker(local_rerank_path)


# ===================== 工具函数 =====================
def get_all_docs(vectorstore):
    """从 Chroma 中取出全部文档（供 BM25 使用）"""
    data = vectorstore.get(include=["documents", "metadatas"])
    return [
        Document(page_content=d, metadata=m if m else {})
        for d, m in zip(data["documents"], data["metadatas"])
    ]


def format_docs(docs):
    return "\n".join(d.page_content for d in docs)


def jieba_tokenize(text):
    return jieba.lcut(text)


def _preview(docs, n=60):
    for i, d in enumerate(docs):
        text = d.page_content.replace("\n", " ")
        print(f"  {i+1}. {text[:n]}{'...' if len(text) > n else ''}")


# ===================== RRF 倒数排名融合 =====================
def fuse_rrf(bm25_docs, vector_docs, k=RRF_K, top_n=FINAL_TOP_K):
    """
    Reciprocal Rank Fusion（RRF）倒数排名融合。
    公式: score(d) = Σ 1 / (k + rank_i(d))
    优点：无需归一化两路检索的分数，直接用排名即可融合，
         对不同分布的分数鲁棒，常用于混合稀疏+稠密检索。
    """
    rrf_scores = {}
    doc_map = {}

    # BM25 排名贡献
    for rank, doc in enumerate(bm25_docs):
        score = 1.0 / (k + rank + 1)
        key = doc.page_content
        rrf_scores[key] = rrf_scores.get(key, 0) + score
        doc_map[key] = doc

    # 向量检索排名贡献
    for rank, doc in enumerate(vector_docs):
        score = 1.0 / (k + rank + 1)
        key = doc.page_content
        rrf_scores[key] = rrf_scores.get(key, 0) + score
        doc_map[key] = doc

    sorted_items = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_map[content] for content, _ in sorted_items[:top_n]]


# ===================== 粗排（双路召回 + RRF 融合）+ 精排（Reranker）=====================
def hybrid_retrieve(query, vectorstore):
    all_docs = get_all_docs(vectorstore)

    # ---------- 粗排：双路召回 ----------
    # 1. BM25 稀疏检索（基于关键词）
    bm25_retriever = BM25Retriever.from_documents(
        all_docs,
        preprocess_func=jieba_tokenize,  # 中文需用 jieba 分词
    )
    bm25_retriever.k = TOP_K
    bm25_docs = bm25_retriever.invoke(query)

    # 2. 向量稠密检索（基于语义）
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": TOP_K})
    vector_docs = vector_retriever.invoke(query)

    print("\n" + "=" * 60)
    print(f"🔎 粗排·双路召回（每路 Top-{TOP_K}）")
    print("=" * 60)
    print(f"\n【BM25 稀疏检索】召回 {len(bm25_docs)} 条：")
    _preview(bm25_docs)
    print(f"\n【向量稠密检索】召回 {len(vector_docs)} 条：")
    _preview(vector_docs)

    # ---------- RRF 融合 ----------
    fused_docs = fuse_rrf(bm25_docs, vector_docs)
    print(f"\n【RRF 倒数排名融合 (k={RRF_K})】融合后保留 {len(fused_docs)} 条（进入精排）：")
    _preview(fused_docs)

    # ---------- 精排：本地 Reranker 重排序 ----------
    reranked_docs = reranker.rank(query, fused_docs)

    print("\n" + "=" * 60)
    print(f"✅ 精排·Reranker(bge-reranker-base) 重排完成，最终输出 Top-{RERANK_TOP_K}")
    print("=" * 60)
    _preview(reranked_docs[:RERANK_TOP_K])

    return reranked_docs[:RERANK_TOP_K]


# ===================== RAG 主流程 =====================
def run_rag_qa(query, persist_directory="./chroma_db"):
    if not os.path.exists(persist_directory):
        print(f"❌ 找不到向量数据库目录 '{persist_directory}'，请先运行 2_vector_builder.py。")
        return

    print("▶ 正在加载嵌入模型...")
    embeddings = HuggingFaceEmbeddings(
        model_name=local_embed_path,
        model_kwargs={"device": "cuda"},
        encode_kwargs={"normalize_embeddings": True},
    )

    print("▶ 正在加载本地向量数据库...")
    vectorstore = Chroma(
        persist_directory=persist_directory,
        embedding_function=embeddings,
    )

    # 混合检索 + Reranker 精排
    final_docs = hybrid_retrieve(query, vectorstore)

    print("\n" + "=" * 60)
    print(f"📄 最终用于回答的文档数量：{len(final_docs)}")
    print("=" * 60)
    for i, d in enumerate(final_docs):
        print(f"\n--- 文档 {i+1} ---\n{d.page_content}")
    print("\n" + "=" * 60)

    # LLM
    llm = ChatOpenAI(model=model_name, temperature=0, api_key=api_key, base_url=base_url)

    system_prompt = (
        "你是华为有限公司的内部智能助手。\n"
        "请严格基于以下提供的公司内部文档内容回答用户问题。\n"
        "如果你在文档中找不到答案，请直接说“根据提供的文档，我无法回答该问题”，绝不能凭空编造信息。\n\n"
        "【参考文档内容】\n"
        "{context}"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "{input}"),
    ])

    rag_chain = (
        {"context": lambda x: format_docs(final_docs), "input": lambda x: x["input"]}
        | prompt
        | llm
        | StrOutputParser()
    )

    print(f"\n================ 问答测试 ================")
    print(f"👤 用户提问: {query}")
    print("🤖 正在生成答案，请稍候...\n")

    answer = rag_chain.invoke({"input": query})

    print("💡 回答:")
    print(answer)
    print("\n==========================================")


if __name__ == "__main__":
    test_query = "华为今年赚了多少"
    run_rag_qa(test_query)
