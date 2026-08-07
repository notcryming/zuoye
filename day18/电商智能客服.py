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
llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0
)
"""
**场景**：你是一个电商平台的智能客服，能处理订单查询、退款、商品推荐等问题。
**需求**：
1. 使用 `@tool` 定义 **5 个工具函数**：
  * `query_order(order_id)`: 查询订单状态
  * `calculate_refund(original_price, discount, days_since_purchase)`: 计算退款金额
  * `recommend_product(category, budget)`: 根据品类和预算推荐商品
  * `check_coupon(product_price)`: 计算最优优惠券组合（满100减10，满200减30，满500减80）
  * `get_shipping_fee(city)`: 计算运费
2. 使用 `create_agent` 创建 Agent
3. 实现对话循环，支持多轮交互
4. **额外要求**：每个工具函数的 docstring 必须足够详细
**验收标准**：
* [ ] 5 个工具都能正常调用
* [ ] 优惠券计算逻辑正确
* [ ] 多轮对话正常
"""
# ============================
# 【讲师备注】模拟课程数据库
# 教学提示：告诉学生，实际开发中这里会连接 SQL/NoSQL 数据库
# 课堂上用字典模拟是为了让学生专注 Agent 逻辑，不被数据库连接干扰
# ============================
ORDER_DB = {
    "2026080600310257": {"product": "旺旺官方蔬菜味浪味仙多口味组合花式薯卷儿童休闲经典零食小吃", "price": 20.9, "time": "2026年8月6日13:56", "status": "派送中", "discount": 0.85},
    "2026080300260321": {"product": "云南特产山珍菌即食鸡枞菌牛肝松茸香菇菌类菌子解馋小零食", "price": 8.8, "time": "2026年8月3日11:02", "status": "未发货", "discount": 0.9},
    "2026080100105236": {"product": "酸辣粉桶装速食粉丝米线正宗重庆宽粉细粉红薯粉方便面整箱批发", "price": 29.9, "time": "2026年8月1日03:24", "status": "已送达", "discount": 0.75},
    "2026080500287741": {"product": "海盐苏打饼干咸味薄脆饼干办公休闲代餐零食独立小包装整箱", "price": 14.5, "time": "2026年8月5日09:18", "status": "派送中", "discount": 0.88},
    "2026080400196653": {"product": "芒果干厚切蜜饯果脯水果干休闲追剧解馋零食大袋装", "price": 16.8, "time": "2026年8月4日16:42", "status": "已送达", "discount": 0.8},
    "2026073100089127": {"product": "螺蛳粉正宗广西柳州特产袋装速食米粉酸辣爽口夜宵美食", "price": 35.6, "time": "2026年7月31日22:10", "status": "未发货", "discount": 0.7},
    "2026072900421589": {"product": "手撕面包整箱早餐软面包奶香糕点充饥夜宵休闲零食", "price": 22.3, "time": "2026年7月29日10:33", "status": "已送达", "discount": 0.82},
    "2026080200354468": {"product": "香辣小鱼仔即食小鱼干湖南特产麻辣网红解馋小零食混合口味", "price": 12.9, "time": "2026年8月2日14:27", "status": "派送中", "discount": 0.92},
    "2026072800173394": {"product": "核桃仁薄皮纸皮核桃新货坚果炒货孕妇儿童营养零食罐装", "price": 46.0, "time": "2026年7月28日18:05", "status": "已送达", "discount": 0.68}
}


# ============================
# 【客服备注】工具函数 1：订单查询
# 教学提示：强调 docstring 的重要性！
# Agent 靠 docstring 判断什么时候调用这个工具
# 如果 docstring 写得不清楚，Agent 可能选错工具
# ============================
@tool
def query_order(order_id: str) -> str:
    """
    根据订单号查询订单的详细信息和状态(包括产品名称，价格，订单生成时间，物流状态)
    当需要以上信息，且没有订单号时，向用户询问订单号
    参数order_id:订单的编号，用来唯一标识一个订单
    """
    print("🔧 正在调用本工具: query_order")
    results = []
    for key, course in ORDER_DB.items():
        if order_id in key:
            results.append(
                f"product:{course['product']} | price: {course['price']}元 | "
                f"discount: {course['discount']} | time: {course['time']} | status: {course['status']}"
            )
    return "\n".join(results) if results else "未找到相关订单"

@tool
def get_current_time() -> str:
    """
    获取当前时间，包含年月日，时分秒
    """
    print("正在调用时间工具")
    import datetime
    now = datetime.datetime.now()
    return f"当前时间:{now.strftime('%Y-%m-%d %H:%M:%S')}"

# ============================
# 【讲师备注】工具函数 2：计算退款金额
# 教学提示：这是一个纯业务逻辑工具，展示 Agent 不仅能调 API，还能做业务计算
# 让学生注意参数 current 和 target 的类型是字符串
# ============================
@tool
def calculate_refund(original_price: int, discount: int, days_since_purchase: int) -> str:
    """
    计算退款时应该退给客户的金额是多少，退款金额=original_price x discount x percent(由购买至今的时间判定退款比例)
    参数original_price:商品的原价，在订单数据库中是price对应的值
    参数discount:商品购买时享受的折扣，在订单数据库中是discount对应的值，务必要查询到这个参数！
    参数days_since_purchase:商品购买至今的日期，通过订单数据库中的time取到购买时间与今天的时间做差值计算
    """
    print(f"🔧 正在调用本工具: calculate_refund，参数 original_price: {original_price}, discount: {discount}, days_since_purchase: {days_since_purchase}")
    actual_paid = original_price * discount
    if days_since_purchase <= 7:
        refund = actual_paid
        reason = "7天无理由退货，全额退款"
    elif days_since_purchase <= 30:
        refund = actual_paid * 0.8
        reason = "7-30天退货，扣除20%手续费"
    else:
        return "购买已超过30天，不支持退货"
    return reason + f'，退款金额为{refund}'

# ============================
# 【讲师备注】工具函数 3：计划生成
# 教学提示：这个工具展示如何根据输入参数动态生成内容
# 可以和学生互动："你每天想学几小时？想学多少天？"
# ============================
@tool
def recommend_product(category, budget) -> str:
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
tools = [query_order, get_current_time, calculate_refund]

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
    print("🎓 智能客服已上线！(输入 exit 退出)")
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



