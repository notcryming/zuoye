import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableBranch

# 1. 加载环境变量
load_dotenv()
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

# 2. 初始化大模型
llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0.7
)

# 临时弄一个低温度的模型给主管用，保证他回答严谨
supervisor_llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0.1
)

# ==========================================
# 第一步：定义各个员工节点 (Chains)
# ==========================================

# 1. 主管节点 (分发任务)
# 注意：我们要求主管只输出 frontend、backend 或 unknown
supervisor_prompt = ChatPromptTemplate.from_template(
    "你是一个IT公司的项目主管。请根据客户的问题：【{question}】，决定由哪个部门来回答。\n"
    "你只能从以下三个词中选择一个输出：\n"
    "1. frontend (如果问题关于Vue, React, HTML, CSS等前端技术)\n"
    "2. backend (如果问题关于Java, Python, 数据库等后端技术)\n"
    "3. unknown (如果不属于以上技术问题)\n\n"
    "你的输出："
)
# 这里用 lower() 确保输出一定是小写，方便后面做判断
supervisor_chain = supervisor_prompt | supervisor_llm | StrOutputParser() | (lambda x: x.strip().lower())

# 2. 前端专家节点
frontend_prompt = ChatPromptTemplate.from_template("你是一个前端开发专家，请用不超过50个字解答：{question}")
frontend_chain = frontend_prompt | llm | StrOutputParser() | (lambda x: f"【前端专家回复】 {x}")

# 3. 后端专家节点
backend_prompt = ChatPromptTemplate.from_template("你是一个后端架构师，请用不超过50个字解答：{question}")
backend_chain = backend_prompt | llm | StrOutputParser() | (lambda x: f"【后端专家回复】 {x}")

# 4. 客服节点 (处理未知问题)
unknown_chain = (lambda x: "【客服回复】 您好，我们是一家IT技术公司，您的问题超出了我们的服务范围。")

# ==========================================
# 第二步：组装纯 LangChain 的条件路由 (RunnableBranch)
# ==========================================
# 教学比喻：这就像是一个“铁轨分道器”。火车开过来，看车头挂着什么牌子，就把它引到哪条铁轨上。

# 我们先把问题打包，同时让主管做出决定
# 输入是 {"question": "..."}
# 输出会变成 {"question": "...", "department": "frontend" / "backend" / "unknown"}
context_chain = {
    "question": RunnablePassthrough(), # 原封不动保留问题
    "department": supervisor_chain     # 让主管算出该去哪个部门
}

# RunnableBranch 是 LangChain 实现“条件分支”的核心语法
# 格式是：(判断条件函数, 对应的执行链) 的无限堆叠，最后一个参数是“默认执行链”（兜底）
routing_branch = RunnableBranch(
    # 如果 department 是 frontend，就把问题传给前端专家
    (lambda x: "frontend" in x["department"], lambda x: frontend_chain.invoke({"question": x["question"]})),
    
    # 如果 department 是 backend，就把问题传给后端专家
    (lambda x: "backend" in x["department"], lambda x: backend_chain.invoke({"question": x["question"]})),
    
    # 默认兜底：交给客服
    (lambda x: unknown_chain(x))
)

# 最终把这两截拼在一起
final_pipeline = context_chain | routing_branch

# ==========================================
# 第三步：运行测试
# ==========================================
if __name__ == "__main__":
    print("🚀 启动纯 LangChain 条件路由测试 (RunnableBranch)...\n")
    
    test_questions = [
        "Vue3 里的 ref 和 reactive 有什么区别？",
        "在 Python 里怎么连接 MySQL 数据库？",
        "明天的天气怎么样？"
    ]
    
    for q in test_questions:
        print("="*50)
        print(f"👤 客户提问: {q}\n")
        
        # 注意：使用纯 LangChain 路由时，中间过程（比如主管怎么分发的）是静默的，
        # 我们只能拿到最终的结果。这也是它不如 LangGraph 直观的原因。
        result = final_pipeline.invoke(q)
        
        print(f"🎉 最终回复: \n{result}")
        print("="*50)