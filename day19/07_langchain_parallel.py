import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda

# 1. 加载环境变量
load_dotenv()
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

# 环境变量强校验：缺失时给出中文明确提示，避免让用户看到 pydantic 深层报错
_required_env = [("API_KEY", api_key), ("BASE_URL", base_url), ("MODEL_NAME", model_name)]
_missing = [name for name, val in _required_env if not val]
if _missing:
    raise EnvironmentError(
        f"缺少必要的环境变量: {', '.join(_missing)}。请在 day19 目录下创建 .env 文件，"
        f"写入 API_KEY=xxx、BASE_URL=xxx、MODEL_NAME=xxx 三个键值对后重试。"
    )

# 2. 初始化大模型
llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0.7
)

# 临时弄一个低温度的模型给主管用
supervisor_llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0.1
)

# ==========================================
# 第一步：定义各个员工节点 (Chains)
# ==========================================

# 1. 主管节点 (判断问题类型 + 判断部门间是否存在执行依赖)
# 输出格式升级为：部门列表|依赖关系
#   - 依赖关系为 none 表示无依赖，可并发
#   - 写成 backend->database 表示 database 必须等 backend 出结果后才能工作
supervisor_prompt = ChatPromptTemplate.from_template(
    "你是一个IT公司的项目主管。请分析客户的问题：【{question}】。\n"
    "请判断该问题需要哪些部门来回答。请从以下三个部门中选择，可以多选，用逗号分隔（如：frontend,backend）：\n"
    "- frontend (涉及 Vue, React, 界面等)\n"
    "- backend (涉及 Python, Java, 业务逻辑等)\n"
    "- database (涉及 MySQL, 索引, 数据存储等)\n"
    "如果不属于以上任何技术问题，请输出 unknown。\n\n"
    "重要：如果同时涉及多个部门，请判断部门之间是否存在执行依赖。\n"
    "执行依赖是指：某个部门必须等另一个部门完成、拿到其结果后才能开展工作。\n"
    "典型场景：需要先完成后端业务逻辑，后端结果出来后，数据库专家才能据此设计具体的表结构/存储方案。\n"
    "请严格按以下格式输出：\n"
    "部门列表|依赖关系\n"
    "其中依赖关系只能写 none 或 形如 backend->database（表示后者依赖前者）。\n"
    "示例1：frontend,backend,database|backend->database\n"
    "示例2：frontend,backend|none\n"
    "示例3：unknown|none\n"
    "你的输出："
)
supervisor_chain = supervisor_prompt | supervisor_llm | StrOutputParser() | (lambda x: x.strip().lower())

# 2. 前端专家节点
frontend_prompt = ChatPromptTemplate.from_template("你是一个前端开发专家，请从前端的角度，用不超过50个字解答：{question}")
frontend_chain = frontend_prompt | llm | StrOutputParser() | (lambda x: f"【前端专家】 {x}")

# 3. 后端专家节点
backend_prompt = ChatPromptTemplate.from_template("你是一个后端架构师，请从后端的角度，用不超过50个字解答：{question}")
backend_chain = backend_prompt | llm | StrOutputParser() | (lambda x: f"【后端专家】 {x}")

# 新增 3.5 数据库专家节点
database_prompt = ChatPromptTemplate.from_template("你是一个DBA数据库专家，请从数据存储和性能的角度，用不超过50个字解答：{question}")
database_chain = database_prompt | llm | StrOutputParser() | (lambda x: f"【DBA专家】 {x}")

# 4. 客服节点
unknown_chain = (lambda x: "【客服回复】 您好，我们是一家IT技术公司，您的问题超出了我们的服务范围。")

# ==========================================
# 第二步：实现“并发执行”与“合并” (RunnableParallel)
# ==========================================
department_chains = {
    "frontend":frontend_chain,
    "backend":backend_chain,
    "database":database_chain
}

# ==========================================
# 第三步：利用自定义路由函数来实现动态的分支与并发
# ==========================================
def route_department(inputs):
    raw = inputs["department"]
    print(f"👔 [主管] 原始输出: {raw}")
    question = inputs["question"]

    if "unknown" in raw:
        return unknown_chain(inputs)

    # 1. 解析 “部门列表|依赖关系”，例如 “frontend,backend,database|backend->database”
    parts = raw.split("|")
    department_str = parts[0].strip()
    dependency_str = parts[1].strip() if len(parts) > 1 else "none"

    selected_depts = [d.strip() for d in department_str.split(",") if d.strip() in department_chains]

    if not selected_depts:
        return unknown_chain(inputs)

    # 2. 判断是否存在依赖，存在则走“顺序执行 + 上下文传递”，否则走原来的并发逻辑
    has_dependency = (dependency_str != "none") and ("->" in dependency_str)
    src = dst = None

    if has_dependency:
        # 解析 backend->database  =>  src=backend, dst=database
        _pair = [s.strip() for s in dependency_str.split("->")]
        # 容错1：只支持 一端->一端；主管写错格式就降级为并发
        if len(_pair) != 2:
            has_dependency = False
        else:
            src, dst = _pair
            # 容错2：依赖双方都必须在已选部门里，否则降级为并发
            if src not in selected_depts or dst not in selected_depts:
                has_dependency = False

    # 3. 只有依赖校验全部通过，才真正走顺序 + 上下文传递
    if has_dependency:
        print(f"🔗 [路由] 检测到依赖 {src}->{dst}，采用【顺序执行】模式")

        results = {}
        # 3.1 先执行被依赖的源部门（如 backend）
        results[src] = department_chains[src].invoke({"question": question})

        # 3.2 把源部门结果作为“历史对话/参考信息”拼进 dst 的 question，
        #     这样数据库专家就能基于后端业务结果来设计具体存储方案
        context_question = f"{question}\n\n[参考信息·{src}部门结果]\n{results[src]}"
        results[dst] = department_chains[dst].invoke({"question": context_question})

        # 3.3 其余无依赖的部门仍然并发执行，不浪费并行能力
        other_depts = [d for d in selected_depts if d not in (src, dst)]
        if other_depts:
            parallel_dict = {d: department_chains[d] for d in other_depts}
            other_results = RunnableParallel(**parallel_dict).invoke({"question": question})
            results.update(other_results)

        final_parts = ["综合解答（含依赖顺序）"]
        for dept, answer in results.items():
            final_parts.append(answer)
        return "\n".join(final_parts)

    # 3. 无依赖：保持原来的动态 RunnableParallel 并发逻辑
    print(f"⚡ [路由] 无依赖，采用【并发执行】模式")
    parallel_dict = {dept: department_chains[dept] for dept in selected_depts}
    dynamic_parallel_chain = RunnableParallel(**parallel_dict)
    results = dynamic_parallel_chain.invoke({"question": question})

    final_parts = ["综合解答"]
    for dept, answer in results.items():
        final_parts.append(answer)
    return "\n".join(final_parts)

# 将主管的判断和路由合并为最终的流水线
# final_pipeline = {
#     "question": RunnablePassthrough(),
#     "department": supervisor_chain
# } | RunnablePassthrough.assign(
#     # 将路由结果作为一个新字段输出
#     final_answer=route_department
# ) | (lambda x: x["final_answer"]) # 最终只提取答案部分

final_pipeline = {
    "question": RunnablePassthrough(),
    "department": supervisor_chain
} | RunnableLambda(route_department)

if __name__ == "__main__":
    print("🚀 启动纯 LangChain 动态并发路由测试 (RunnableParallel)...\n")
    
    test_questions = [
        # 无依赖：多部门可并发
        "做个网站，需要Vue写页面，Python写接口，还要用MySQL存数据",
        "在 Python 里怎么连接 MySQL 数据库？",
        "只写一个简单的HTML静态页面",
        # 有依赖：必须先完成后端业务，DBA 才能根据后端结果设计存储方案
        "我们要做一个电商订单系统，请先用 Python 设计订单业务逻辑，再让 DBA 根据该业务结果设计对应的数据库表结构"
    ]
    
    for q in test_questions:
        print("="*50)
        print(f"👤 客户提问: {q}\n")
        result = final_pipeline.invoke(q)
        print(f"🎉 最终回复: \n{result}")
        print("="*50)