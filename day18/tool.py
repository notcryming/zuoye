from langchain_core.prompts import ChatPromptTemplate
import asyncio
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent
import os
from dotenv import load_dotenv

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

# 1.自己手写一个工具
@tool
def get_weather(city: str) -> str:
    """
    查询城市的天气
    参数 city:城市名称
    """

    # 模拟数据
    weather_data = {
        "北京": "晴天，25℃",
        "上海": "多云，0℃",
        "广州": "小雨，28℃"
    }
    print(f"正在调用本工具，参数city:{city}")
    return weather_data.get(city, "暂无该城市的天气")


@tool
def get_current_time() -> str:
    """
    获取当前时间
    """
    import datetime
    now = datetime.datetime.now()
    print("~~~~~你在调用本工具")
    return f"当前时间:{now.strftime('%Y-%m-%d %H:%M:%S')}"

tools = [get_weather, get_current_time]

agent = create_agent(llm, tools)

async def main():
    response = await agent.ainvoke({"messages": "北京天气怎么样？"})
    print("AI回答：", response["messages"][-1].content)

if __name__ == "__main__":
    asyncio.run(main())
