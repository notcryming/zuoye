# 旅行计划生成器.py (基于 LangChain 条件路由，支持单顾问/多顾问并发)
import os
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

# ==========================================
# 第零步：初始化大模型
# ==========================================
load_dotenv()
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

if not api_key or not base_url or not model_name:
    raise RuntimeError("请在 .env 中配置 API_KEY / BASE_URL / MODEL_NAME")

# 普通顾问使用中等温度，更具创造力
llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0.7
)

# 主管使用低温度，保证输出稳定严格
supervisor_llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0.05
)

# 汇总器使用中低温度，保证结构清晰
aggregator_llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0.3
)


# ==========================================
# 第一步：定义 5 个顾问 Chain
# ==========================================
# 顾问注册字典：键是顾问编号，值是(显示名, Chain构造函数)
CONSULTANTS = {}


def build_destination_chain():
    """目的地顾问：介绍旅游亮点、最佳季节、景点推荐"""
    prompt = ChatPromptTemplate.from_template(
        "你是一位资深旅行目的地顾问。请针对【{context}】\n"
        "从以下几个方面给出专业建议（用中文，条理清晰分点）：\n"
        "1. 目的地的旅游亮点与独特之处（2-3句话概括）\n"
        "2. 必去的 3-5 个景点（简要说明）\n"
        "3. 最佳旅游季节与游玩天数建议\n"
        "4. 注意事项（签证、语言、治安等）\n"
        "请直接输出正文，不要加客套话。"
    )
    return prompt | llm | StrOutputParser()


def build_budget_chain():
    """预算规划师：按天数分配预算"""
    prompt = ChatPromptTemplate.from_template(
        "你是一位精打细算的预算规划师。请针对【{context}】\n"
        "给出一份详细的预算分配方案（用中文，条理清晰分点）：\n"
        "1. 预算总览（是否充裕/紧张，并说明理由）\n"
        "2. 按项目拆分（交通/住宿/餐饮/门票/购物/应急储备）\n"
        "3. 按天拆分（每天大概花费）\n"
        "4. 省钱建议（至少 3 条）\n"
        "请直接输出正文，不要加客套话。"
    )
    return prompt | llm | StrOutputParser()


def build_transportation_chain():
    """交通顾问：往返交通+市内交通"""
    prompt = ChatPromptTemplate.from_template(
        "你是一位精通交通的旅行顾问。请针对【{context}】\n"
        "给出专业的交通方案（用中文，条理清晰分点）：\n"
        "1. 往返交通建议（飞机/高铁/自驾，含大致票价范围）\n"
        "2. 机场/车站到市区的接驳方式（公交/地铁/出租车，价格）\n"
        "3. 市内交通方式与推荐购买的交通卡/通票\n"
        "4. 需要注意的交通规则或小技巧（至少 3 条）\n"
        "请直接输出正文，不要加客套话。"
    )
    return prompt | llm | StrOutputParser()


def build_food_chain():
    """美食顾问：特色美食推荐"""
    prompt = ChatPromptTemplate.from_template(
        "你是一位资深美食顾问。请针对【{context}】\n"
        "给出一份地道的美食攻略（用中文，条理清晰分点）：\n"
        "1. 必尝的 5-8 道特色菜肴/小吃（每道 1-2 句介绍）\n"
        "2. 推荐的餐厅/美食街区（3-4 个，含大致人均）\n"
        "3. 饮食文化小知识或吃的讲究\n"
        "4. 适合带走的特产/伴手礼（3-5 种）\n"
        "请直接输出正文，不要加客套话。"
    )
    return prompt | llm | StrOutputParser()


def build_culture_chain():
    """文化顾问：当地文化、风俗、禁忌"""
    prompt = ChatPromptTemplate.from_template(
        "你是一位文化人类学背景的文化顾问。请针对【{context}】\n"
        "给出一份详尽的文化指南（用中文，条理清晰分点）：\n"
        "1. 当地的历史文化背景（2-3 句话概括）\n"
        "2. 民俗风情（节日、服饰、艺术、宗教等）\n"
        "3. 礼仪与禁忌（至少 5 条，避免踩坑）\n"
        "4. 推荐体验的文化活动（比如看演出、逛博物馆等 2-3 项）\n"
        "请直接输出正文，不要加客套话。"
    )
    return prompt | llm | StrOutputParser()


# 把 5 个顾问注册到统一的注册表中，方便循环调用
CONSULTANTS["destination"] = {
    "name": "目的地顾问",
    "build": build_destination_chain,
    "chain": None,
}
CONSULTANTS["budget"] = {
    "name": "预算规划师",
    "build": build_budget_chain,
    "chain": None,
}
CONSULTANTS["transportation"] = {
    "name": "交通顾问",
    "build": build_transportation_chain,
    "chain": None,
}
CONSULTANTS["food"] = {
    "name": "美食顾问",
    "build": build_food_chain,
    "chain": None,
}
CONSULTANTS["culture"] = {
    "name": "文化顾问",
    "build": build_culture_chain,
    "chain": None,
}

# 懒加载：首次访问时初始化所有顾问 Chain
for key in CONSULTANTS:
    CONSULTANTS[key]["chain"] = CONSULTANTS[key]["build"]()


# ==========================================
# 第二步：定义主管节点（输出顾问列表）
# ==========================================
supervisor_prompt = ChatPromptTemplate.from_template(
    "你是一个旅行 APP 的智能主管。请分析用户的旅游问题：【{question}】\n"
    "判断需要让哪些顾问参与回答。可选顾问及职责如下：\n"
    "- destination（目的地顾问）：判断目的地亮点、景点、最佳季节、签证等\n"
    "- budget（预算规划师）：预算分配、省钱建议、花费拆分\n"
    "- transportation（交通顾问）：往返交通、市内交通、交通卡\n"
    "- food（美食顾问）：美食推荐、餐厅、特产\n"
    "- culture（文化顾问）：历史文化、民俗、禁忌、文化活动\n\n"
    "请严格输出一个 JSON 对象，格式为：{{\"consultants\": [顾问编号列表]}}\n"
    "例如：如果需要目的地+美食顾问，就输出 {{\"consultants\": [\"destination\", \"food\"]}}\n"
    "注意：\n"
    "1. 只输出 JSON，不要任何解释或额外字符\n"
    "2. 如果问题和旅行完全无关，输出 {{\"consultants\": []}}\n"
    "3. 如果用户提到了钱/花费/预算 → 必须包含 budget\n"
    "4. 如果用户提到了吃/美食/餐厅 → 必须包含 food\n"
    "5. 如果用户提到了交通/飞机/高铁/打车 → 必须包含 transportation"
)

# 主管 chain：prompt → LLM → 解析出顾问列表
supervisor_chain = supervisor_prompt | supervisor_llm | StrOutputParser()


def parse_consultant_list(raw_text: str) -> list:
    """
    把主管的输出解析成顾问编号列表。
    优先用 JSON 解析，解析失败时用正则兜底，保证健壮性。
    """
    text = raw_text.strip()
    # 尝试 JSON 解析
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "consultants" in data:
            lst = data["consultants"]
            if isinstance(lst, list):
                return [x for x in lst if x in CONSULTANTS]
    except Exception:
        pass

    # JSON 解析失败：用正则兜底，提取所有在 CONSULTANTS 中出现过的键
    found = []
    for key in CONSULTANTS:
        if re.search(r"\b" + re.escape(key) + r"\b", text):
            found.append(key)
    # 去重，保持原有顺序
    seen = set()
    unique = []
    for k in found:
        if k not in seen:
            seen.add(k)
            unique.append(k)
    return unique


# ==========================================
# 第三步：定义分发与并发调用逻辑
# ==========================================
def invoke_consultant(key: str, context: str) -> tuple:
    """
    调用单个顾问，返回 (顾问编号, 显示名, 回答)
    出现异常时返回错误信息而不是抛出，保证其他顾问不受影响。
    """
    info = CONSULTANTS[key]
    try:
        answer = info["chain"].invoke({"context": context})
        return (key, info["name"], answer.strip())
    except Exception as e:
        return (key, info["name"], f"[该顾问暂时不可用: {e}]")


def dispatch_question(question: str, verbose: bool = True) -> dict:
    """
    主路由函数：让主管分析 → 分发到需要的顾问 → 并发调用 → 汇总结果
    返回 {"question": ..., "decision": [...], "answers": {顾问编号: (显示名, 内容)}, "summary": ...}
    """
    # 1. 主管做出分发决策
    raw_decision = supervisor_chain.invoke({"question": question})
    consultant_keys = parse_consultant_list(raw_decision)

    if verbose:
        print(f"📋 主管分发决策: 选召 {len(consultant_keys)} 位顾问 → "
              f"{[CONSULTANTS[k]['name'] for k in consultant_keys]}")
        if not consultant_keys:
            print("  (主管判断：该问题与旅行无关，无人处理)")

    # 2. 没有合适顾问：返回兜底回答
    if not consultant_keys:
        return {
            "question": question,
            "decision": [],
            "answers": {},
            "summary": "您好，我是旅行顾问，专长是回答旅游相关的问题（目的地、预算、交通、美食、文化等）。您的问题似乎超出了我的服务范围~",
        }

    # 3. 单顾问直接调用，多顾问使用线程池并发
    answers = {}
    if len(consultant_keys) == 1:
        key = consultant_keys[0]
        _, cname, ans = invoke_consultant(key, question)
        answers[key] = (cname, ans)
        if verbose:
            print(f"✅ {cname} 回答完成")
    else:
        if verbose:
            print(f"⚡ 并发调用 {len(consultant_keys)} 位顾问中...")
        with ThreadPoolExecutor(max_workers=len(consultant_keys)) as pool:
            future_map = {
                pool.submit(invoke_consultant, k, question): k
                for k in consultant_keys
            }
            for future in as_completed(future_map):
                k, cname, ans = future.result()
                answers[k] = (cname, ans)
                if verbose:
                    print(f"  ✅ {cname} 回答完成")

    # 4. 汇总所有顾问的回答，形成完整最终答复
    summary = aggregate_answers(question, answers, consultant_keys)

    return {
        "question": question,
        "decision": consultant_keys,
        "answers": answers,
        "summary": summary,
    }


# ==========================================
# 第四步：汇总器（把多顾问回答整合成一段连贯回复）
# ==========================================
aggregate_prompt = ChatPromptTemplate.from_template(
    "你是一位旅行杂志的主编。请把以下多位旅行顾问关于用户问题【{question}】的回答，\n"
    "整理成一份结构清晰、易于阅读的完整旅行建议。\n"
    "要求：\n"
    "1. 用「## 标题」的方式分块，保留每个顾问的核心内容\n"
    "2. 开头加一段简短总览（1-2 句话），结尾加一段温馨提示\n"
    "3. 用中文，段落与分点清晰，不要出现任何原始 JSON 或代码\n"
    "4. 不要编造原始回答里没有的信息\n\n"
    "原始顾问回答（按顾问分开）：\n{raw_answers}\n"
)


def aggregate_answers(question: str, answers: dict, consultant_keys: list) -> str:
    """把顾问回答按顺序拼接成给汇总器的文本"""
    raw_parts = []
    for k in consultant_keys:
        if k in answers:
            cname, ans = answers[k]
            raw_parts.append(f"【{cname}】\n{ans}")
    raw_answers_text = "\n\n".join(raw_parts)

    # 单顾问时就不汇总了，直接返回原始回答
    if len(consultant_keys) == 1:
        k = consultant_keys[0]
        cname, ans = answers[k]
        return f"## {cname} 为您解答\n\n{ans}"

    # 多顾问时调用汇总器 LLM 整合
    try:
        chain = aggregate_prompt | aggregator_llm | StrOutputParser()
        return chain.invoke({"question": question, "raw_answers": raw_answers_text})
    except Exception as e:
        # LLM 汇总失败，退回手动拼接
        manual = f"## 旅行综合建议\n\n> 针对您的问题：{question}\n\n"
        for k in consultant_keys:
            if k in answers:
                cname, ans = answers[k]
                manual += f"### {cname}\n{ans}\n\n"
        manual += f"\n*(汇总 LLM 暂时不可用，以上为原始回答: {e})*"
        return manual


# ==========================================
# 第五步：旅行计划生成器（目的地+天数+预算 → 自动全流程）
# ==========================================
def build_travel_plan(destination: str, days: int, budget: float) -> dict:
    """
    旅行计划生成器：用户输入目的地 + 天数 + 预算，
    自动把所有 5 位顾问都召唤出来，生成一份完整的旅行计划书。
    """
    # 1. 组装上下文，让每个顾问拿到完整信息
    full_context = (
        f"目的地：{destination} | 旅行天数：{days}天 | 总预算：{budget}元人民币"
    )

    all_keys = list(CONSULTANTS.keys())
    print(f"\n🌏 旅行计划生成器启动！")
    print(f"  目的地: {destination}  |  天数: {days}天  |  预算: {budget}元")
    print(f"  召唤全部 {len(all_keys)} 位顾问并发工作中...\n")

    # 2. 并发调用所有 5 个顾问
    answers = {}
    with ThreadPoolExecutor(max_workers=len(all_keys)) as pool:
        future_map = {
            pool.submit(invoke_consultant, k, full_context): k
            for k in all_keys
        }
        for i, future in enumerate(as_completed(future_map), 1):
            k, cname, ans = future.result()
            answers[k] = (cname, ans)
            print(f"  [{i}/{len(all_keys)}] ✅ {cname} 完成")

    # 3. 汇总为完整计划书
    print("\n📑 主编正在整理计划书...")
    plan_question = f"去{destination}旅行{days}天，预算{budget}元，生成一份完整旅行计划"
    plan = aggregate_answers(plan_question, answers, all_keys)

    # 4. 额外生成每日行程骨架（基于天数，简单规则，不调用 LLM）
    daily_skeleton = build_daily_skeleton(destination, days, answers)

    return {
        "destination": destination,
        "days": days,
        "budget": budget,
        "decision": all_keys,
        "answers": answers,
        "daily_skeleton": daily_skeleton,
        "plan": plan,
    }


def build_daily_skeleton(destination: str, days: int, answers: dict) -> str:
    """
    构建按天的行程骨架（Day 1 ... Day N）。
    这里用规则生成：把顾问信息分散到各天，结构清晰。
    """
    # 从顾问回答中摘取简短信息用于每日提示
    dest_hint = ""
    if "destination" in answers:
        lines = answers["destination"][1].splitlines()[:3]
        dest_hint = "；".join(lines)[:80]

    food_hint = ""
    if "food" in answers:
        lines = [l.strip() for l in answers["food"][1].splitlines() if l.strip()]
        if lines:
            food_hint = lines[0][:80]

    culture_hint = ""
    if "culture" in answers:
        lines = [l.strip() for l in answers["culture"][1].splitlines() if l.strip()]
        if lines:
            culture_hint = lines[0][:80]

    # 规则生成：按天数分段
    skeleton_parts = [f"### 📅 每日行程骨架（共 {days} 天）"]
    if days >= 1:
        skeleton_parts.append(f"- **Day 1 抵达日**: 抵达{destination}，入住酒店，附近熟悉环境；交通提示可参考「交通顾问」")
    if days >= 2:
        skeleton_parts.append(f"- **Day 2 主景点日**: 安排 1-2 个核心景点深度游览；景点建议可参考「目的地顾问」")
    for d in range(3, max(days, 2)):
        skeleton_parts.append(f"- **Day {d} 主题体验日**: 可自由搭配次要景点、购物、或文化活动；文化活动可参考「文化顾问」")
    if days >= 3:
        skeleton_parts.append(f"- **Day {days} 返程日**: 上午再吃一顿地道美食，购买特产伴手礼，前往机场/车站；美食可参考「美食顾问」")
    if days == 1:
        skeleton_parts[-1] = f"- **Day 1 一日游**: 选 1-2 个核心景点 + 1 顿特色餐，下午交通返程"

    if dest_hint:
        skeleton_parts.append(f"\n💡 目的地亮点：{dest_hint}")
    if food_hint:
        skeleton_parts.append(f"🍜 美食提示：{food_hint}")
    if culture_hint:
        skeleton_parts.append(f"🎭 文化提示：{culture_hint}")

    return "\n".join(skeleton_parts)


# ==========================================
# 第六步：打印与交互入口
# ==========================================
def print_result(result: dict):
    """美化输出路由/分发结果"""
    print("\n" + "=" * 70)
    print(f"👤 用户提问: {result['question']}")
    print("-" * 70)
    print(f"📋 主管分发决策:")
    if result["decision"]:
        for key in result["decision"]:
            print(f"   ↳ {CONSULTANTS[key]['name']} ({key})")
    else:
        print("   ↳ （无顾问匹配，转交通用客服）")
    print("-" * 70)
    print(result["summary"])
    print("=" * 70 + "\n")


def print_travel_plan(plan: dict):
    """美化输出完整旅行计划"""
    print("\n" + "=" * 70)
    print(f"🌏 【{plan['destination']} · {plan['days']}天 · 预算{plan['budget']}元】 完整旅行计划书")
    print("-" * 70)
    print(f"📋 参与顾问 ({len(plan['decision'])} 位): "
          f"{' / '.join(CONSULTANTS[k]['name'] for k in plan['decision'])}")
    print("-" * 70)
    print(plan["plan"])
    print("-" * 70)
    print(plan["daily_skeleton"])
    print("=" * 70 + "\n")


def interactive_qa():
    """问答模式：用户任意提问，主管自动分发"""
    print("\n🤖 旅行智能问答系统启动！")
    print("   问任意旅行相关问题，我会自动分发给适合的顾问")
    print("   输入 plan 进入旅行计划生成器；输入 exit 退出\n")
    while True:
        try:
            user = input("👤 请提问: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见！")
            break
        if not user:
            continue
        if user.lower() == "exit":
            print("👋 再见！")
            break
        if user.lower() == "plan":
            try:
                dest = input("  🌏 目的地: ").strip()
                days = int(input("  📅 天数: ").strip())
                budget = float(input("  💰 预算(元): ").strip())
            except Exception:
                print("❌ 输入不合法，已返回问答模式")
                continue
            plan = build_travel_plan(dest, days, budget)
            print_travel_plan(plan)
            continue
        result = dispatch_question(user, verbose=True)
        print_result(result)


if __name__ == "__main__":
    # ==========================================
    # 自测：单顾问、复合问题、旅行计划生成器
    # ==========================================
    tests = [
        "去成都玩有什么必去的景点？",                    # 单顾问：目的地
        "两个人去泰国玩一周，带 12000 元够吗？该怎么花？",  # 复合：预算+目的地+可能美食
        "北京有什么好吃的？推荐几家餐厅。",                # 单顾问：美食
        "去巴黎坐飞机还是高铁？地铁怎么坐？",              # 单顾问：交通
        "去日本玩要注意什么文化禁忌？",                    # 单顾问：文化
        "我想去云南大理 5 天，预算 5000，吃的住的交通和玩什么全帮我看看",  # 多顾问全招
        "帮我推荐一款笔记本电脑",                          # 无关，无顾问
    ]

    print("🚀 运行【单/多顾问路由】测试案例：")
    for q in tests:
        print("\n" + "#" * 70)
        result = dispatch_question(q, verbose=True)
        print_result(result)

    # 旅行计划生成器测试
    print("\n" + "🎯" * 30)
    print("🎯 现在运行【旅行计划生成器】测试案例：")
    plan = build_travel_plan(destination="东京", days=5, budget=8000)
    print_travel_plan(plan)

    # 最后进入交互式问答
    interactive_qa()
