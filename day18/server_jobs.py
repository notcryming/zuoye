# server.py (MCP服务端：扮演“技能专员”，提供本地工具和数据)
from mcp.server.fastmcp import FastMCP

# 1. 实例化MCP服务端，相当于成立一个名为"JobAssistant"的技能工具箱
mcp = FastMCP("JobAssistant1")


# 2. @mcp.tool() 是核心！它像是一个“USB接口”的暴露端
# 挂上这个装饰器，大模型就能通过MCP协议“看”到并调用这个本地函数
@mcp.tool()
def search_jobs(keyword: str) -> str:
    """
    根据关键词搜索职位信息
    参数keyword:和职位相关的关键词
    """
    mock_db = {
        "python工程师": "Python工程师 - 薪资20k - 要求：熟练使用LangChain和FastAPI",
        "java工程师": "Java工程师 - 薪资18k - 要求：Spring Cloud, MySQL",
        "前端工程师": "前端工程师 - 薪资15k - 要求：Vue3, React, TypeScript",
        "销售": "销售人员 - 薪资15k - 要求：语言表达能力强",
        "AI算法开发工程师": "AI算法开发工程师 - 薪资25k - 要求：懂大模型原理，有B端经验"
    }

    try:
        result = [info for key, info in mock_db.items() if keyword in key]
    except Exception as e:
        return f"搜索出错: {str(e)}"

    if result:
        return "找到以下职位:\n" + "\n".join(result)
    else:
        return "暂未找到相关职位，请尝试其他关键词。"

if __name__ == "__main__":
    # 3. 启动服务端，"stdio"表示通过标准输入输出与客户端(大模型)进行通信对话
    mcp.run(transport="stdio")
