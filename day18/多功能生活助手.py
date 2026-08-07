from langchain_core.prompts import ChatPromptTemplate
import asyncio
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent
import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

'''
任务 1：多功能生活助手
**场景**：你要开发一个"生活助手"Agent，它不仅能查天气，还能做更多实用功能。
**需求**：
1. 使用 `@tool` 定义至少 **4 个工具函数**：
  * `get_weather(city)`: 调用免费的天气 API（如 `https://wttr.in/{city}?format=%C+%t`）获取真实天气数据
  * `convert_currency(amount, from_currency, to_currency)`: 调用免费汇率 API 进行货币换算
  * `get_joke()`: 调用免费笑话 API 获取一个笑话
  * `calculate(expression)`: 用 Python 实现一个安全的数学计算器（add）
2. 使用 `create_react_agent` 创建 Agent
3. 实现一个**交互式对话循环**，用户可以连续提问，输入 `exit` 退出
4. 在终端打印每次工具调用的日志
**验收标准**：
* [ ] 4 个工具都能正常被 Agent 调用
* [ ] 能处理不同类型的问题
* [ ] 对话循环正常运行
* [ ] 终端有工具调用日志
'''


llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url,
    temperature=0
)


def add(a: float, b: float) -> float:
    """安全加法，返回a + b"""
    return a + b

# 获取用户所在地信息
@tool
def get_ip() -> str:
    """
    获取用户所在的地点
    """
    print("正在调用ip工具")
    url = "https://v2.xxapi.cn/api/ip"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        inner_data = data.get("data", {})
        address = inner_data.get("address", "未知地址")
        result = f"""
address:{address}
        """
        return result.strip()
    except Exception as e:
        # API出错返回错误文本，Agent会收到这个报错信息
        return f"调用IP查询接口失败，错误信息：{str(e)}"

# 获取真实天气数据
@tool
def get_weather(city: str) -> str:
    """
    查询城市的天气
    参数 city:城市名称
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    print(f"正在调用天气工具，参数city:{city}")
    url = f"https://wttr.in/{city}?format=%C+%t"
    try:
        resp = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        term_div = soup.find(class_="term-container")
        if term_div:
            weather_text = term_div.get_text(strip=True)
            return f"提取结果：{weather_text}"
        else:
            return "未找到天气节点"
    except Exception as e:
        # API出错返回错误文本，Agent会收到这个报错信息
        return f"调用IP查询接口失败，错误信息：{str(e)}"

@tool
def get_current_time() -> str:
    """
    获取当前时间
    """
    print("正在调用时间工具")
    import datetime
    now = datetime.datetime.now()
    return f"当前时间:{now.strftime('%Y-%m-%d %H:%M:%S')}"

@tool
def get_dujitang() -> str:
    """
    获取一份毒鸡汤文案
    """
    print("正在调用毒鸡汤工具")
    url = "https://v2.xxapi.cn/api/dujitang"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        inner_data = data.get("data", "无")
        result = f"""
    文案:{inner_data}
            """
        return result.strip()
    except Exception as e:
        # API出错返回错误文本，Agent会收到这个报错信息
        return f"调用IP查询接口失败，错误信息：{str(e)}"

@tool
def get_jixiong(phone: str) -> str:
    """
    根据用户提供的手机号码判断吉凶
    参数phone:手机号码
    """
    print(f"正在电话号码吉凶工具，参数phone:{15730246173}")
    url = f"https://v2.xxapi.cn/api/phonejixiong?phone={phone}"
    try:
        resp = requests.get(url, timeout=5)
        data = resp.json()
        inner_data = data.get("data", {})
        address = inner_data.get("meaning", "无")
        result = f"""
解释:{address}
        """
        return result.strip()
    except Exception as e:
        # API出错返回错误文本，Agent会收到这个报错信息
        return f"调用IP查询接口失败，错误信息：{str(e)}"

@tool
def calculate(expression: str):
    """
    简单计算器，仅支持 add(x,y) 格式字符串
    example: calculate("add(3,5)") → 8
    """
    # 极简单解析，不eval，字符串解析提取数字
    print("正在调用计算工具")
    if not expression.startswith("add(") or not expression.endswith(")"):
        raise ValueError("仅支持 add(number,number) 格式")
    inner = expression.removeprefix("add(").removesuffix(")")
    parts = inner.split(",")
    if len(parts) !=2:
        raise ValueError("参数格式错误，add(a,b)需要两个数字参数")
    try:
        num1 = float(parts[0].strip())
        num2 = float(parts[1].strip())
    except ValueError:
        raise ValueError("参数必须是数字")
    return add(num1, num2)

tools = [get_ip, get_weather, get_current_time, get_dujitang, get_jixiong, calculate]

agent = create_agent(llm, tools)

async def main(messages):
    response = await agent.ainvoke({"messages": messages})
    print("AI回答：", response["messages"][-1].content)

if __name__ == "__main__":
    while(True):
        print("你:", end="")
        messages = input()
        asyncio.run(main(messages))
