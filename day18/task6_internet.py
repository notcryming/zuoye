# task6_internet.py (万能查询助手客户端：连接大模型与互联网工具MCP服务端)
import asyncio
import os
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

load_dotenv()


async def main():
    print("🚀 正在启动万能查询助手...")

    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL_NAME")

    if not api_key or not base_url or not model_name:
        print("❌ 配置错误：请检查 .env 中的 API_KEY / BASE_URL / MODEL_NAME")
        return

    # --- 核心步骤 1: 建立MCP连接，接入"互联网工具专员" ---
    # 把 server_internet.py 这个带工具的"U盘"插到系统中
    mcp_client = MultiServerMCPClient({
        "internet_tools": {
            "command": "python",
            "args": ["server_internet.py"],  # 指定要运行的互联网工具服务端
            "transport": "stdio"  # 保持与服务端一致的通信频道
        }
    })

    try:
        tools = await mcp_client.get_tools()  # 扫描并获取服务端暴露的所有工具
        print(f"✅ 成功接入互联网工具: {[t.name for t in tools]}")
    except Exception as e:
        print(f"❌ 工具接入失败: {e}")
        return

    # --- 核心步骤 2: 唤醒"大模型大脑" ---
    try:
        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.3
        )
        print(f"✅ 大模型大脑已上线: {model_name}")
    except Exception as e:
        print(f"❌ 模型连接失败: {e}")
        return

    # --- 核心步骤 3: 绑定大脑与工具，创建Agent ---
    agent = create_agent(llm, tools)

    print("\n--- 万能查询助手已准备就绪 (输入 'exit' 退出) ---")
    print("💡 可问：IP归属地 / 毒鸡汤 / 维基百科 / 世界各地时间 / 域名信息")
    while True:
        user_input = input("\n👤 我: ")
        if user_input.lower() == "exit":
            break
        if not user_input.strip():
            continue

        try:
            # Agent会自动判断是否需要调用MCP工具，获取数据后再给出最终回答
            response = await agent.ainvoke({"messages": user_input})
            print(f"🤖 AI: {response['messages'][-1].content}")
        except Exception as e:
            print(f"❌ 运行出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())
