"""
任务2：AI 学习规划师
使用 @tool 定义课程查询、水平评估、计划生成工具

【讲师备注 - 教学重点】
1. 本案例展示如何用 @tool 把业务逻辑封装成 Agent 可调用的工具
2. 多轮对话机制：messages 列表维护完整上下文，Agent 能记住之前的对话
3. 复合问题处理：学生可以先问课程，再问学习规划，Agent 自动组合调用工具
4. 工具日志打印：方便课堂上观察 Agent 的调用链和决策过程
"""
import asyncio
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.tools import tool
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

# ============================
# 【讲师备注】模拟课程数据库
# 教学提示：告诉学生，实际开发中这里会连接 SQL/NoSQL 数据库
# 课堂上用字典模拟是为了让学生专注 Agent 逻辑，不被数据库连接干扰
# ============================
COURSE_DB = {
    "python": {"name": "Python 入门到精通", "price": 299, "difficulty": "入门", "hours": 40},
    "java": {"name": "Java 核心编程", "price": 399, "difficulty": "进阶", "hours": 60},
    "前端": {"name": "前端开发全栈课", "price": 349, "difficulty": "入门", "hours": 50},
    "ai": {"name": "AI 智能体开发", "price": 499, "difficulty": "高级", "hours": 80},
    "langchain": {"name": "LangChain 实战", "price": 199, "difficulty": "进阶", "hours": 30},
}


# ============================
# 【讲师备注】工具函数 1：课程查询
# 教学提示：强调 docstring 的重要性！
# Agent 靠 docstring 判断什么时候调用这个工具
# 如果 docstring 写得不清楚，Agent 可能选错工具
# ============================
@tool
def get_course_info(keyword: str) -> str:
    """根据关键词查询课程信息，返回课程名、价格、难度和学习时长"""
    print("🔧 正在调用本工具: get_course_info")  # 【讲师备注】课堂演示时让学生看终端，观察工具调用时机
    results = []
    for key, course in COURSE_DB.items():
        if keyword.lower() in key or keyword in course["name"]:
            results.append(
                f"{course['name']} | 价格: {course['price']}元 | "
                f"难度: {course['difficulty']} | 课时: {course['hours']}小时"
            )
    return "\n".join(results) if results else "未找到相关课程"


# ============================
# 【讲师备注】工具函数 2：水平评估
# 教学提示：这是一个纯业务逻辑工具，展示 Agent 不仅能调 API，还能做业务计算
# 让学生注意参数 current 和 target 的类型是字符串
# ============================
@tool
def assess_level(current: str, target: str) -> str:
    """评估从当前水平到目标水平的学习差距，current为当前水平，target为目标水平"""
    print(f"🔧 正在调用本工具: assess_level，参数 current: {current}, target: {target}")  # 【讲师备注】打印参数，方便学生观察 Agent 传递的参数是否正确
    level_map = {"零基础": 0, "入门": 1, "进阶": 2, "高级": 3}
    gap = level_map.get(target, 0) - level_map.get(current, 0)
    if gap <= 0:
        return f"您已经是{current}水平，无需额外学习"
    hours_needed = gap * 30
    return f"从{current}到{target}，建议学习{hours_needed}小时，每周5小时约需{hours_needed // 5}周"


# ============================
# 【讲师备注】工具函数 3：计划生成
# 教学提示：这个工具展示如何根据输入参数动态生成内容
# 可以和学生互动："你每天想学几小时？想学多少天？"
# ============================
@tool
def generate_study_plan(hours_per_day: int, total_days: int) -> str:
    """根据每日学习时长和总天数生成学习计划"""
    print(f"🔧 正在调用本工具: generate_study_plan，参数 hours_per_day: {hours_per_day}, total_days: {total_days}")  # 【讲师备注】打印参数
    total_hours = hours_per_day * total_days
    phases = total_hours // 10
    plan = f"📅 {total_days}天学习计划（每天{hours_per_day}小时，共{total_hours}小时）\n"
    for i in range(1, phases + 1):
        plan += f"第{i}阶段（{i * 10}小时）：掌握核心知识点，完成练习\n"
    plan += "最后阶段：综合实战项目"
    return plan


# ============================
# 【讲师备注】工具注册
# 告诉学生：这里把 3 个工具放进列表，后面 Agent 会自动根据用户意图选择调用
# ============================
tools = [get_course_info, assess_level, generate_study_plan]

# 【讲师备注】初始化模型，temperature=0.5 表示有一定创意性，适合规划类任务
llm = ChatOpenAI(model=model_name, api_key=api_key, base_url=base_url, temperature=0.5)
agent = create_agent(llm, tools)  # 【讲师备注】创建 Agent，绑定大模型和工具列表


# ============================
# 【讲师备注】多轮对话主循环
# 教学提示：重点讲解 messages 列表的作用！
# 1. messages 维护完整对话历史，让 Agent 有"记忆"
# 2. 每次用户提问和 AI 回复都追加进去
# 3. 这样 Agent 就能参考之前的上下文，回答复合问题
# 对比：如果不维护 messages，Agent 就是"失忆"的，只能回答单轮问题
# ============================
async def main():
    print("🎓 AI 学习规划师已上线！(输入 exit 退出)")
    messages = []  # 【讲师备注】维护对话历史，实现多轮上下文记忆
    while True:
        user_input = input("\n👤 你: ")
        if user_input.lower() == 'exit':
            break
        if not user_input.strip():
            continue
        messages.append({"role": "user", "content": user_input})  # 【讲师备注】用户提问加入历史
        response = await agent.ainvoke({"messages": messages})
        ai_reply = response['messages'][-1].content
        print(f"🎓 AI: {ai_reply}")
        messages.append({"role": "assistant", "content": ai_reply})  # 【讲师备注】AI回复也加入历史，保持上下文完整


if __name__ == "__main__":
    asyncio.run(main())
