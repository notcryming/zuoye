"""
Day 3 - 12 学生随堂实战任务 (高难度)
===================================
目标: 将 Prompt 工程与 Python 编程结合，掌握构建鲁棒性 LLM 应用的基础能力。
难度: ⭐⭐⭐ (需要结合字符串处理、函数构造和 JSON 操作)

背景: 在接下来的 LangChain 课程中，我们将不再手写字符串拼接，而是使用组件。
但理解这些“底层脏活”对于排查 LangChain 错误至关重要。
"""

import json
import re

# ---------------------------------------------------------
# 任务 1: 鲁棒性 JSON 提取 (清洗模型输出)
# ---------------------------------------------------------
def extract_json_from_llm(raw_text):
    """
    从 LLM 的原始回复中提取合法的 JSON 对象。
    
    背景: 模型经常会在 JSON 前后加废话，或者把 JSON 包裹在 Markdown 代码块中 (```json ... ```)。
    直接 json.loads(raw_text) 会报错。
    
    参数:
        raw_text (str): 模型的原始回复字符串
    
    返回:
        dict: 解析后的字典
    """
    # TODO: 请补全代码
    # 提示:
    # 1. 尝试寻找并去除 ```json 和 ``` 标记。
    # 2. 寻找第一个 '{' 和最后一个 '}' 之间的内容。
    # 3. 使用 json.loads 尝试解析。
    # 4. 如果解析失败，打印错误并返回 None。
    text = raw_text.strip()
    start_mark = "```json"
    end_mark = "```"
    idx_code_start = text.find(start_mark)
    if idx_code_start != -1:
        # 找到 ```json 之后的位置
        text = text[idx_code_start + len(start_mark):]
        idx_code_end = text.find(end_mark)
        if idx_code_end != -1:
            text = text[:idx_code_end]
    text = text.strip()
    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace == -1 or last_brace == -1 or last_brace < first_brace:
        print("错误：未找到有效的 {} JSON 边界")
        return None
    json_candidate = text[first_brace:last_brace + 1]
    try:
        dict = json.loads(json_candidate)
        return dict
    except json.JSONDecodeError as e:
        # 4. 如果解析失败，打印错误并返回 None
        print(f"JSON解析失败: {e}")
        print(f"待解析片段: {json_candidate}")
        return None



# ---------------------------------------------------------
# 任务 2: 基于意图的路由分发 (Router Logic)
# ---------------------------------------------------------
class SimpleRouter:
    """
    模拟一个基于 LLM 意图识别的路由分发器。
    """
    def __init__(self):
        self.intents = {
            "weather": "调用天气 API",
            "code": "执行代码解释器",
            "chat": "进行闲聊回复"
        }

    def get_prompt_template(self, user_query):
        """
        生成用于意图分类的 Prompt
        """
        # TODO: 补全 Prompt，要求模型输出 JSON，包含 {"intent": "...", "reason": "..."}
        return f"""
你是一个意图识别助手。请分析用户的输入，判断其属于以下哪个意图类别:
intent = {list(self.intents.keys())}

用户输入: {user_query}

请严格输出 JSON 格式，不要输出其他内容。
JSON:{"intent": "weather", "reason": "..."}
"""

    def route(self, llm_output_json):
        """
        解析 LLM 返回的 JSON，并执行对应的 Mock 动作
        """
        # TODO: 补全代码
        # 1. 解析 JSON
        # 2. 获取 intent 字段
        # 3. 如果 intent 在 self.intents 中，打印 "正在执行: {action}..."
        # 4. 如果不在，打印 "未知意图"
        jso = json.loads(llm_output_json)
        if jso["intent"] in self.intents.keys():
            action = self.intents[jso["intent"]]
            print(f"正在执行：{action}")
        else:
            print("未知意图")


# =========================================================
# 测试入口 (请勿修改下方的测试代码，用于验证你的实现)
# =========================================================

if __name__ == "__main__":

    # --- 测试任务 1 ---
    print("📝 任务 1: 鲁棒性 JSON 提取")
    dirty_responses = [
        '{"name": "Alice", "age": 25}',  # 干净数据
        'Here is the JSON: ```json\n{"name": "Bob", "age": 30}\n```',  # Markdown 包裹
        'Sure! \n {\n "name": "Charlie",\n "age": 35 \n }\n Hope this helps!' # 废话 + 换行
    ]
    for dirty in dirty_responses:
        result = extract_json_from_llm(dirty)
        print(f"原始数据: {dirty[:20]}... -> 解析结果: {result}")

    print("\n📝 任务 2: 基于意图的路由分发")
    router = SimpleRouter()
    # 模拟 LLM 返回的 JSON 字符串
    mock_llm_response_1 = '{"intent": "weather", "reason": "User asked about rain"}'
    mock_llm_response_2 = '{"intent": "unknown", "reason": "Gibberish"}'
    
    print("测试用例 1:")
    router.route(mock_llm_response_1)
    print("测试用例 2:")
    router.route(mock_llm_response_2)

    print("\n🎉 任务完成!")
