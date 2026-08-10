import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

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

class AgentState(TypedDict):
    topic: str
    
    marketing_plan: str
    ui_agent: str

    frontend_code: str
    backend_code: str

    test_case: str
    final_report: str

def marketing_agent(state: AgentState):
    print("📢 [营销部] 收到需求，最先开工，构思卖点...")
    prompt = ChatPromptTemplate.from_template("你是一个营销专家，请为【{topic}】写一句响亮的Slogan（不超过20字）。")
    response = (prompt | llm).invoke({"topic": state["topic"]})
    return {"marketing_plan": response.content}

# 2. UI设计部（必须等营销部写完）
def ui_agent(state: AgentState):
    print("🎨 [UI设计部] 看到营销方案了，开始配合设计UI...")
    prompt = ChatPromptTemplate.from_template(
        "你是一个UI设计师。我们要开发【{topic}】，\n"
        "营销部的口号是：【{marketing_plan}】\n"
        "请根据这个口号，推荐一个最契合的主色调及原因（不超过30字）。"
    )
    response = (prompt | llm).invoke({
        "topic": state["topic"], 
        "marketing_plan": state["marketing_plan"] # 读取营销产出
    })
    return {"ui_design": response.content}

# 3. 前端部（和后端并行开工）
def frontend_agent(state: AgentState):
    print("💻 [前端部] 拿到UI图了，开始选型前端框架...")
    prompt = ChatPromptTemplate.from_template("你是一个前端架构师，请为【{topic}】推荐核心前端技术（不超过30字）。")
    response = (prompt | llm).invoke({"topic": state["topic"]})
    return {"frontend_code": response.content}

# 4. 后端部（和前端并行开工）
def backend_agent(state: AgentState):
    print("⚙️  [后端部] 拿到需求了，开始设计数据库架构...")
    prompt = ChatPromptTemplate.from_template("你是一个后端架构师，请为【{topic}】推荐一款数据库及原因（不超过30字）。")
    response = (prompt | llm).invoke({"topic": state["topic"]})
    return {"backend_code": response.content}

# 5. 测试部（必须等前后端都搞完才能测）
def test_agent(state: AgentState):
    print("🐛 [测试部] 前后端终于都交接了！开始制定联调测试方案...")
    prompt = ChatPromptTemplate.from_template(
        "你是一个高级测试工程师。我们要测试【{topic}】，\n"
        "前端技术：【{frontend_code}】\n"
        "后端技术：【{backend_code}】\n"
        "请结合前后端架构，提出一个最重要的联调安全测试点（不超过30字）。"
    )
    response = (prompt | llm).invoke({
        "topic": state["topic"],
        "frontend_code": state["frontend_code"], # 读取前端产出
        "backend_code": state["backend_code"]    # 读取后端产出
    })
    return {"test_case": response.content}

# 6. 项目经理合并
def summarizer_agent(state: AgentState):
    print("📝 [项目经理] 所有流程走完，正在整理最终交付文档...")
    parts = [
        "================ 核心方案 ===============",
        f"【营销策划】：{state.get('marketing_plan')}",
        f"【UI设计】：{state.get('ui_design')}",
        f"【前端技术】：{state.get('frontend_code')}",
        f"【后端架构】：{state.get('backend_code')}",
        f"【测试重点】：{state.get('test_case')}",
        "========================================="
    ]
    return {"final_report": "\n".join(parts)}    

def build_complex_dependency_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("marketing", marketing_agent)
    workflow.add_node("ui", ui_agent)
    workflow.add_node("frontend", frontend_agent)
    workflow.add_node("backend", backend_agent)
    workflow.add_node("test", test_agent)
    workflow.add_node("summarizer", summarizer_agent)

    workflow.add_edge(START, "marketing")
    workflow.add_edge("marketing", "ui")
    workflow.add_edge("ui", "frontend")
    workflow.add_edge("ui", "backend")

    workflow.add_edge("frontend", "test")
    workflow.add_edge("backend", "test")    

    workflow.add_edge("test", "summarizer")

    workflow.add_edge("summarizer", END)

    return workflow.compile()

if __name__ == "__main__":
    app = build_complex_dependency_graph()
    topic = "校园二手书交易微信小程序"

    initial_state = {
        "topic": topic,
        "marketing_plan": "", "ui_design": "",
        "frontend_code": "", "backend_code": "",
        "test_case": "", "final_report": ""
    }

    # 执行图
    result = app.invoke(initial_state)
    print(f"\n🎉 最终项目方案: \n{result['final_report']}")       
        

