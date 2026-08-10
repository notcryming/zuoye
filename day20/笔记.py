'''
RAG
检索增强生成：检索外部文档信息，结合大模型生成答案，核心解决了大模型的两个痛点：
  知识过时：大模型的训练数据有限，无法获取最新的细腻
  幻觉问题：大模型会编造一些不存在的信息
RAG本质是一条特殊的chain
rag，chain，agent：
RAG vs 微调
RAG分成两大阶段，构建阶段（离线准备）和检索阶段（在线回答），全程固定流水线，对应一条chain
（1）构建阶段：离线准备，只需要做一次
  文档加载（解析）：加载外部文档（如pdf招聘简章，word文档）
  文档拆分chunk：将长文档拆分成短文档片段chunks，避免大模型上下文不足，避免过多无关内容干扰
  Embedding编码：将每个文本片段转化为向量，捕捉文本语义信息（多模态RAG）
  向量存储：将向量存入向量数据库（如Chorma），方便后续检索
（2）检索阶段：在线回答，每次用户提问都会执行
  用户提问：用户输入的问题
  问题编码：将用户问题转为向量
  相似检索：在向量数据库中，检索与问题最相关的top-k文本片段（3,5,10）
  Prompt拼接：将检索的文本片段（上下文）与用户问题，提示词拼接
  模型生成：大模型结合上下文，也就是将拼接好的prompt作为输入生成准确回答（不编造信息）
  输出解析：将回答解析为清晰的格式，返回给用户
构建过程 相当于把参考书拆成知识点卡片，存入大脑（向量数据库）
检索阶段 遇到问题，先提取卡片，再结合问题回答，不瞎编
##RAG的评估指标
评估模块的输入包括以下要素（这些不能直接反应好坏）
输入问题
生成答案
上下文
参考答案
以上要素两两组合，对应一种评估指标
生成答案与上下文的一致性，忠实度，很重要，代U表是否存在幻觉问题
文档解析及拆分
将外部文档转为可处理的文本，Langchain有相关的工具，主要讲解PDF解析
为什么要拆分？大模型上下文限制，片段语义集中
向量化Embedding
Embedding就是把文本转成向量的过程，核心就是捕捉文本的语义信息-语义越相似，向量距离就越近。
embedding模型
  openai Embedding：精度比较高，适合生产环境
  本地化模型（比如bge-small-zh）：无需联网，免费，适合本地开发
Embedding模型到底是什么模型？
bert模型，bert模型为基座的双塔结构，对a，b俩句子处理后算cos-sim相似度

要做一个向量数据库，
第一步先加载数据
第二步分割数据用 固定长度分块 RecursiveCharacterTextSplitter（或 CharacterTextSplitter）
             基于语义的智能分块 SentenceTransformersTokenTextSplitter，SemanticChunker 语义分块
             MarkdownTextSplitter Markdown文档拆分
             PythonCodeTextSplitter 代码文件拆分
             HTMLHeaderTextSplitter HTML 网页分块
第三步向量化Embedding，把文本内容转换为向量
向量数据库
Chroma向量数据库，faiss（学术），milvus（工业）等，专门用来存储/管理/检索向量。
第四步
'''
import torch
print(torch.cuda.is_available())
