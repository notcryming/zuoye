import os
from typing import TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
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

# ==========================================
# 第一步：定义状态 (State) - 公司的公文包（高级扩展版）
# ==========================================
class AgentState(TypedDict):
    topic: str             # 客户原始需求
    
    marketing_plan: str    # 营销Slogan
    marketing_retries: int # 营销方案修改次数（新增：用于控制循环）
    review_feedback: str   # 合规审核意见（新增：用于跨部门沟通）
    
    ui_design: str         # UI设计（依赖营销）
    frontend_code: str     # 前端技术
    backend_code: str      # 后端技术
    test_case: str         # 测试方案（依赖前后端合并）
    final_report: str      # 最终交付文档

# ==========================================
# 第二步：定义各个部门 (Nodes)
# ==========================================

# 1. 营销部（故意写激进文案以触发打回）
def marketing_agent(state: AgentState):
    retries = state.get("marketing_retries", 0)
    feedback = state.get("review_feedback", "")
    
    print(f"\n📢 [营销部] 第 {retries + 1} 次构思卖点...")
    
    if feedback:
        print(f"   😭 收到打回意见：{feedback}")
        prompt = ChatPromptTemplate.from_template(
            "你是一个营销专家，请为【{topic}】写一句Slogan（不超过20字）。\n"
            "注意！之前被合规部打回，意见是：【{feedback}】\n"
            "请务必修正，去掉绝对化词汇，重新生成一个合规的！"
        )
        response = (prompt | llm).invoke({"topic": state["topic"], "feedback": feedback})
    else:
        # 第一次故意诱导违规，为了给学生演示条件边和打回流程
        prompt = ChatPromptTemplate.from_template(
            "你是一个激进的营销专家，请为【{topic}】写一句响亮的Slogan（不超过20字）。\n"
            "为了吸引眼球，请务必在Slogan中包含“全网第一”、“最强”或“天下无敌”等夸张词汇！"
        )
        response = (prompt | llm).invoke({"topic": state["topic"]})
        
    plan = response.content
    print(f"   📝 产出方案: {plan}")
    return {
        "marketing_plan": plan,
        "marketing_retries": retries + 1
    }

# 2. 合规审核部（新增：利用结构化输出审查违规词）
class ReviewResult(BaseModel):
    status: str = Field(description="审核结果，必须是 PASS 或 REJECT")
    feedback: str = Field(description="如果不通过，给出修改建议；如果通过，写'无'")

def reviewer_agent(state: AgentState):
    print("\n🧐 [合规部] 正在审查营销方案，严查广告法违规词...")
    parser = JsonOutputParser(pydantic_object=ReviewResult)
    prompt = ChatPromptTemplate.from_template(
        "你是一个严格的合规审核员。请审查以下营销Slogan：\n【{plan}】\n"
        "规则：如果Slogan中包含'最'、'第一'、'无敌'、'极'等绝对化夸大词汇，必须返回 REJECT 并指出违规词。\n"
        "如果没有违规词，返回 PASS。\n\n{format_instructions}"
    )
    
    chain = prompt | llm | parser
    result = chain.invoke({
        "plan": state["marketing_plan"],
        "format_instructions": parser.get_format_instructions()
    })
    
    print(f"   ⚖️ 审查结果: [{result.get('status', 'ERROR')}] 意见: {result.get('feedback', '')}")
    return {"review_feedback": f"[{result.get('status', 'ERROR')}] {result.get('feedback', '')}"}

# 3. 兜底方案部（新增：重试超限后的替补）
def fallback_marketing(state: AgentState):
    print("\n🛡️ [风控主管] 营销部重试3次均失败，强制启用默认安全方案！")
    safe_plan = f"【{state['topic']}】—— 您的安心之选，值得信赖！"
    return {
        "marketing_plan": safe_plan,
        "review_feedback": "[PASS] 强制兜底通过"
    }

# 4. UI设计部
def ui_agent(state: AgentState):
    print("\n🎨 [UI设计部] 看到最终版合规营销方案了，开始配合设计UI...")
    prompt = ChatPromptTemplate.from_template(
        "我们要开发【{topic}】，营销口号是：【{marketing_plan}】\n"
        "请推荐一个最契合的主色调及原因（不超过30字）。"
    )
    response = (prompt | llm).invoke({
        "topic": state["topic"], 
        "marketing_plan": state["marketing_plan"]
    })
    return {"ui_design": response.content}

# 5. 前端部
def frontend_agent(state: AgentState):
    print("💻 [前端部] 开始选型前端框架...")
    prompt = ChatPromptTemplate.from_template("为【{topic}】推荐核心前端技术（不超过30字）。")
    response = (prompt | llm).invoke({"topic": state["topic"]})
    return {"frontend_code": response.content}

# 6. 后端部
def backend_agent(state: AgentState):
    print("⚙️  [后端部] 开始设计数据库架构...")
    prompt = ChatPromptTemplate.from_template("为【{topic}】推荐一款数据库及原因（不超过30字）。")
    response = (prompt | llm).invoke({"topic": state["topic"]})
    return {"backend_code": response.content}

# 7. 测试部
def test_agent(state: AgentState):
    print("\n🐛 [测试部] 制定联调测试方案...")
    prompt = ChatPromptTemplate.from_template(
        "前端：【{frontend_code}】，后端：【{backend_code}】\n"
        "请提出一个最重要的联调安全测试点（不超过30字）。"
    )
    response = (prompt | llm).invoke({
        "frontend_code": state["frontend_code"],
        "backend_code": state["backend_code"]
    })
    return {"test_case": response.content}

# 8. 项目经理合并
def summarizer_agent(state: AgentState):
    print("\n📝 [项目经理] 所有流程走完，正在整理最终交付文档...")
    parts = [
        "================ 核心方案 ===============",
        f"【修改次数】：{state.get('marketing_retries')} 次",
        f"【营销策划】：{state.get('marketing_plan')}",
        f"【UI设计】：{state.get('ui_design')}",
        f"【前端技术】：{state.get('frontend_code')}",
        f"【后端架构】：{state.get('backend_code')}",
        f"【测试重点】：{state.get('test_case')}",
        "========================================="
    ]
    return {"final_report": "\n".join(parts)}

# ==========================================
# 第三步：定义条件路由函数 (Conditional Edges Router)
# ==========================================
def review_router(state: AgentState) -> str:
    """
    根据审核结果决定下一步去哪：
    - PASS -> 去UI部
    - REJECT 且 重试<3 -> 回营销部重做
    - REJECT 且 重试>=3 -> 去兜底方案
    """
    feedback = state.get("review_feedback", "")
    retries = state.get("marketing_retries", 0)
    
    if "PASS" in feedback:
        return "to_ui"
    elif retries >= 3:
        return "to_fallback"
    else:
        return "to_marketing"

# ==========================================
# 第四步：组装高级依赖网络图 (LangGraph)
# ==========================================
def build_advanced_graph():
    workflow = StateGraph(AgentState)

    # 1. 注册所有节点 (包含新增的审核部和风控兜底部)
    workflow.add_node("marketing", marketing_agent)
    workflow.add_node("reviewer", reviewer_agent)
    workflow.add_node("fallback", fallback_marketing)
    workflow.add_node("ui", ui_agent)
    workflow.add_node("frontend", frontend_agent)
    workflow.add_node("backend", backend_agent)
    workflow.add_node("test", test_agent)
    workflow.add_node("summarizer", summarizer_agent)

    # 2. 编排带循环和分支的网状流程
    
    # 开始 -> 营销部
    workflow.add_edge(START, "marketing")
    
    # 营销部写完 -> 必须交由合规部审核
    workflow.add_edge("marketing", "reviewer")
    
    # 【核心扩展】：合规部 -> 根据结果动态路由 (条件边)
    workflow.add_conditional_edges(
        "reviewer",
        review_router,
        {
            "to_ui": "ui",               # 审核通过：流转给下游UI
            "to_fallback": "fallback",   # 烂泥扶不上墙：流转给兜底
            "to_marketing": "marketing"  # 审核打回：退回重做（形成循环）
        }
    )
    
    # 兜底方案 -> UI部 (强行推进流程)
    workflow.add_edge("fallback", "ui")
    
    # UI设计完 -> 并发给前端和后端 (并行)
    workflow.add_edge("ui", "frontend")
    workflow.add_edge("ui", "backend")
    
    # 前后端 -> 测试部 (汇聚等待)
    workflow.add_edge("frontend", "test")
    workflow.add_edge("backend", "test")
    
    # 测试部 -> 项目经理
    workflow.add_edge("test", "summarizer")
    
    # 项目经理 -> 结束
    workflow.add_edge("summarizer", END)

    return workflow.compile()

# ==========================================
# 第五步：运行测试
# ==========================================
if __name__ == "__main__":
    app = build_advanced_graph()
    print("🚀 启动 LangGraph 高级条件路由与兜底机制测试...\n")
    
    topic = "校园二手书交易微信小程序"
    print("="*60)
    print(f"👤 客户下单: {topic}")
    
    # 初始化状态包
    initial_state = {
        "topic": topic,
        "marketing_plan": "", 
        "marketing_retries": 0,
        "review_feedback": "",
        "ui_design": "",
        "frontend_code": "", "backend_code": "",
        "test_case": "", "final_report": ""
    }
    
    # 执行图 (配置最大递归次数防止无限死循环)
    config = {"recursion_limit": 20}
    result = app.invoke(initial_state, config=config)
    
    print(f"\n🎉 最终项目交付件: \n{result['final_report']}")
    print("="*60)
