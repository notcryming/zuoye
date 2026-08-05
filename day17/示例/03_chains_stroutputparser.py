from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
# 加载环境变量 
load_dotenv()  # 执行此函数后，.env文件中的键值对会被加载到系统环境变量中

# 从环境变量中获取模型所需的配置信息
api_key = os.getenv("API_KEY")  # 获取API密钥
base_url = os.getenv("BASE_URL")  # 获取API请求的基础URL（指向硅基流动等第三方平台的接口）
model_name = os.getenv("MODEL_NAME")  # 获取要调用的具体模型名称（例如qwen-flash等）

# ======================
# 1. Model 模型层（统一调用大模型）
# ======================
llm = ChatOpenAI(
    api_key=api_key,
    base_url=base_url,  # 本地/国内大模型可替换
    model_name=model_name,
    temperature=0.1
)

# ======================
# 2. Prompt 输入层（提示词模板）
# ======================
prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一名人工智能课程讲师，回答简洁通俗，不超过50字"),
    ("human", "请解释：{user_question}")
])

# ======================
# 3. Output Parser 输出解析层
# ======================
parser = StrOutputParser()

# ======================
# LCEL 链式拼接：prompt | model | parser
# ======================
chain = prompt | llm | parser

# 执行调用
res = chain.invoke({"user_question": "LangChain Model I/O是什么"})
print(res)
print(type(res))