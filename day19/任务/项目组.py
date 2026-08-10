"""
基于流程图的 LangGraph Agent
=========================================
流程图：
    START
      ↓
    营销部 Agent            (依赖：topic)
      ↓
    UI设计部 Agent          (依赖：topic + 营销方案)
      ↓
    产品经理审核UI  ◄── 扩展1：一票否决，不通过退回UI重做（条件边）
      ↓ 通过
    ┌─────────┐
    前端部 Agent │ 后端部 Agent   (并发，依赖：topic + UI设计)
    └────┬────┘
      ↓
    产品经理审核前端 ◄── 扩展1：一票否决，不通过退回前端重做（条件边）
      ↓ 通过
    测试部 Agent            (依赖：前后端代码) ◄── 扩展2：模拟报错，>3退回前后端重做
      ↓ 报错≤3
    项目经理 Agent          (依赖：所有部门输出)
      ↓
    END

说明：
- 未配置 .env 时自动走"演示模式"，节点返回短句(均<30字)，保证流程随时可运行可展示。
- 配置好 API_KEY/BASE_URL/MODEL_NAME 后，创意类节点改用真实大模型生成。
- 控制类节点(产品经理审核、测试报错)始终用确定性/随机逻辑，便于演示条件边。
"""
import os
import random
from typing import TypedDict, List, Annotated

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, START, END

# ==========================================
# 一、环境与模型初始化
# ==========================================
load_dotenv()
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

# 是否启用真实LLM；未配置则走演示模式，保证代码随时可运行可展示
USE_LLM = bool(api_key and base_url and model_name)
llm = None
if USE_LLM:
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
    )
    print(f"✅ 已启用真实LLM：{model_name}")
else:
    print("⚠️ 未检测到 .env 配置，进入【演示模式】(节点输出短句，流程逻辑完整可展示)")


def _ask(prompt: str, demo: str, variables: dict = None) -> str:
    """统一调用入口：有LLM则真实生成；无LLM则返回演示短句(均<30字)。"""
    if not USE_LLM:
        return demo
    try:
        chain = ChatPromptTemplate.from_template(prompt) | llm | StrOutputParser()
        return chain.invoke(variables or {}).strip()
    except Exception:
        return demo


# 每个环节最大重做次数，防止条件边死循环
MAX_RETRY = 2


# ==========================================
# 二、状态机定义（全局共享，所有节点可读写）
# ==========================================
def _merge_list(a: list, b: list) -> list:
    """日志列表追加合并（LangGraph reducer）"""
    return (a or []) + (b or [])


class AgentState(TypedDict):
    topic: str                              # 项目主题（输入）
    marketing_plan: str                     # 营销方案
    ui_design: str                          # UI设计稿
    frontend_code: str                      # 前端代码
    backend_code: str                       # 后端代码
    test_result: str                        # 测试结果
    test_error_count: int                   # 测试报错数
    pm_ui_decision: str                     # 产品经理对UI的决定：pass/fail
    pm_frontend_decision: str               # 产品经理对前端的决定：pass/fail
    final_report: str                       # 项目经理最终报告
    ui_retry_count: int                     # UI重做计数
    frontend_retry_count: int               # 前端重做计数
    test_retry_count: int                   # 测试重做计数
    log: Annotated[List[str], _merge_list]  # 全流程日志（自动追加）


# ==========================================
# 三、各节点函数（每个节点读取state→返回需更新的字段）
# ==========================================

# 1. 营销部
def marketing_node(state: AgentState) -> dict:
    topic = state["topic"]
    msg = _ask(
        "你是营销专家，为【{topic}】写一句营销方案，不超过30字",
        f"营销方案：{topic}爆款推广",
        {"topic": topic},
    )
    return {"marketing_plan": msg, "log": [f"📢 [营销部] {msg}"]}


# 2. UI设计部
def ui_design_node(state: AgentState) -> dict:
    topic = state["topic"]
    plan = state.get("marketing_plan", "")
    msg = _ask(
        "你是UI设计师，结合营销方案【{plan}】为【{topic}】设计界面，不超过30字",
        f"UI设计：{topic}蓝白扁平首页",
        {"topic": topic, "plan": plan},
    )
    return {"ui_design": msg, "log": [f"🎨 [UI设计部] {msg}"]}


# 3. 产品经理审核UI（扩展1：一票否决）
def pm_review_ui_node(state: AgentState) -> dict:
    retry = state.get("ui_retry_count", 0)
    # 达到重做上限则强制通过，避免死循环；否则30%概率否决
    if retry >= MAX_RETRY:
        decision = "pass"
    else:
        decision = "fail" if random.random() < 0.3 else "pass"
    tag = "通过✅" if decision == "pass" else "否决❌退回UI重做"
    return {
        "pm_ui_decision": decision,
        "ui_retry_count": retry + 1 if decision == "fail" else retry,
        "log": [f"👔 [产品经理·审UI] {tag}(第{retry + 1}次)"],
    }


# 4. 前端部
def frontend_node(state: AgentState) -> dict:
    topic = state["topic"]
    ui = state.get("ui_design", "")
    msg = _ask(
        "你是前端工程师，根据UI【{ui}】为【{topic}】写前端代码摘要，不超过30字",
        f"前端代码：Vue实现{topic}首页",
        {"topic": topic, "ui": ui},
    )
    return {"frontend_code": msg, "log": [f"💻 [前端部] {msg}"]}


# 5. 后端部
def backend_node(state: AgentState) -> dict:
    topic = state["topic"]
    msg = _ask(
        "你是后端工程师，为【{topic}】写后端接口摘要，不超过30字",
        f"后端代码：FastAPI提供{topic}接口",
        {"topic": topic},
    )
    return {"backend_code": msg, "log": [f"⚙️ [后端部] {msg}"]}


# 6. 产品经理审核前端（扩展1：一票否决）
def pm_review_frontend_node(state: AgentState) -> dict:
    retry = state.get("frontend_retry_count", 0)
    if retry >= MAX_RETRY:
        decision = "pass"
    else:
        decision = "fail" if random.random() < 0.3 else "pass"
    tag = "通过✅" if decision == "pass" else "否决❌退回前端重做"
    return {
        "pm_frontend_decision": decision,
        "frontend_retry_count": retry + 1 if decision == "fail" else retry,
        "log": [f"👔 [产品经理·审前端] {tag}(第{retry + 1}次)"],
    }


# 7. 测试部（扩展2：模拟报错，>3退回前后端重做）
def qa_node(state: AgentState) -> dict:
    retry = state.get("test_retry_count", 0)
    # 模拟报错数 0~5
    error_count = random.randint(0, 5)
    # 达到重做上限则强制通过(报错≤3)
    if retry >= MAX_RETRY:
        error_count = min(error_count, 3)
    if error_count > 3:
        result = f"测试发现{error_count}个错误，退回重做"
    else:
        result = f"测试通过，仅{error_count}个小问题"
    return {
        "test_result": result,
        "test_error_count": error_count,
        "test_retry_count": retry + 1 if error_count > 3 else retry,
        "log": [f"🧪 [测试部] {result}"],
    }


# 8. 项目经理
def project_manager_node(state: AgentState) -> dict:
    topic = state["topic"]
    report = f"{topic}项目交付完成，各部门协同验收通过"
    return {"final_report": report, "log": [f"📋 [项目经理] {report}"]}


# ==========================================
# 四、条件边路由函数（不传path_map时，返回值即为目标节点名）
#   - 返回字符串 → 串行跳转
#   - 返回字符串列表 → 开启多节点并发
# ==========================================
# 产品经理审UI后：通过→并发前后端；否决→退回UI
def route_after_pm_ui(state: AgentState):
    if state.get("pm_ui_decision") == "pass":
        return ["frontend", "backend"]   # 列表→并发执行
    return "ui_design"                   # 字符串→退回重做


# 产品经理审前端后：通过→测试；否决→退回前后端重做
def route_after_pm_fe(state: AgentState):
    if state.get("pm_frontend_decision") == "pass":
        return "qa"
    return ["frontend", "backend"]       # 退回并发重做


# 测试后：报错>3→退回前后端重做；否则→项目经理
def route_after_test(state: AgentState):
    if state.get("test_error_count", 0) > 3:
        return ["frontend", "backend"]   # 退回并发重做
    return "project_manager"


# ==========================================
# 五、构建工作流图
# ==========================================
workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("marketing", marketing_node)
workflow.add_node("ui_design", ui_design_node)
workflow.add_node("pm_review_ui", pm_review_ui_node)          # 扩展1
workflow.add_node("frontend", frontend_node)
workflow.add_node("backend", backend_node)
workflow.add_node("pm_review_fe", pm_review_frontend_node)    # 扩展1
workflow.add_node("qa", qa_node)                          # 扩展2
workflow.add_node("project_manager", project_manager_node)

# 主线边
workflow.add_edge(START, "marketing")
workflow.add_edge("marketing", "ui_design")
workflow.add_edge("ui_design", "pm_review_ui")

# 条件边1：产品经理审UI —— 通过则并发到[前端,后端]，否决退回UI设计
workflow.add_conditional_edges("pm_review_ui", route_after_pm_ui)

# 前端、后端并发完成后，fan-in 到产品经理审前端
workflow.add_edge("frontend", "pm_review_fe")
workflow.add_edge("backend", "pm_review_fe")

# 条件边2：产品经理审前端 —— 通过→测试，否决→退回前后端重做
workflow.add_conditional_edges("pm_review_fe", route_after_pm_fe)

# 条件边3：测试 —— 报错>3退回前后端重做，否则→项目经理
workflow.add_conditional_edges("qa", route_after_test)

# 项目经理 → END
workflow.add_edge("project_manager", END)

# 编译成可运行对象
app = workflow.compile()


# ==========================================
# 六、运行与展示
# ==========================================
def run_once(topic: str):
    """跑一次完整流程并打印日志"""
    print("=" * 60)
    print(f"👤 项目主题: {topic}")
    print("-" * 60)
    init_state = {
        "topic": topic,
        "marketing_plan": "",
        "ui_design": "",
        "frontend_code": "",
        "backend_code": "",
        "test_result": "",
        "test_error_count": 0,
        "pm_ui_decision": "",
        "pm_frontend_decision": "",
        "final_report": "",
        "ui_retry_count": 0,
        "frontend_retry_count": 0,
        "test_retry_count": 0,
        "log": [],
    }
    final_state = app.invoke(init_state, config={"recursion_limit": 50})
    print("📜 执行流程：")
    for line in final_state["log"]:
        print("  " + line)
    print("-" * 60)
    print(f"🎉 最终结论: {final_state['final_report']}")
    print(f"   UI重做{final_state['ui_retry_count']}次 | "
          f"前端重做{final_state['frontend_retry_count']}次 | "
          f"测试重做{final_state['test_retry_count']}次")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    random.seed()  # 随机演示否决/报错
    print("🚀 启动 LangGraph 流程图 Agent...\n")
    run_once("在线教育App")
    run_once("外卖小程序")
