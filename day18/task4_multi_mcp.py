# client.py (MCP客户端：扮演“项目经理”，连接大模型与本地工具)
import asyncio
import os
from dotenv import load_dotenv

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

load_dotenv()


async def main():
    print("🚀 正在启动智能助手...")

    api_key = os.getenv("API_KEY")
    base_url = os.getenv("BASE_URL")
    model_name = os.getenv("MODEL_NAME")

    if not api_key or not base_url or not model_name:
        print("❌ 配置错误")
        return

    # --- 核心步骤 1: 建立MCP连接，接入“职位专员” ---
    # 相当于把带有工具的“U盘”(server.py) 插到我们的系统中
    mcp_client = MultiServerMCPClient({
        "job_tools": {
            "command": "python",
            "args": ["server_jobs.py"],  # 指定要运行的服务端脚本
            "transport": "stdio"  # 保持与服务端一致的通信频道
        },
        "company_tools": {
            "command": "python",
            "args": ["server_company.py"],  # 指定要运行的服务端脚本
            "transport": "stdio"  # 保持与服务端一致的通信频道
        },
        "salary_tools": {
            "command": "python",
            "args": ["server_salary.py"],  # 指定要运行的服务端脚本
            "transport": "stdio"  # 保持与服务端一致的通信频道
        }
    })

    try:
        tools = await mcp_client.get_tools()  # 扫描并获取服务端暴露出来的所有工具
        print(f"✅ 成功接入本地工具: {[t.name for t in tools]}")
    except Exception as e:
        print(f"❌ 工具接入失败: {e}")
        return

    # --- 核心步骤 2: 唤醒“大模型大脑” ---
    try:
        llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=0.5
        )
        print(f"✅ 大模型大脑已上线: {model_name}")
    except Exception as e:
        print(f"❌ 模型连接失败: {e}")
        return

    # --- 核心步骤 3: 绑定大脑与工具，创建Agent ---
    # Agent(智能体) = 大模型大脑 + MCP提供的本地工具
    agent = create_agent(llm, tools)

    print("\n--- 智能助手已准备就绪 (输入 'exit' 退出) ---")
    while True:
        user_input = input("\n👤 我: ")
        if user_input.lower() == 'exit':
            break
        if not user_input.strip():
            continue

        try:
            # 当用户提问时，Agent会自动思考是否需要调用MCP工具，获取数据后再给出最终回答
            response = await agent.ainvoke({"messages": user_input})
            print(f"🤖 AI: {response['messages'][-1].content}")
        except Exception as e:
            print(f"❌ 运行出错: {e}")


if __name__ == "__main__":
    asyncio.run(main())