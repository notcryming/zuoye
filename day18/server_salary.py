# server.py (MCP服务端：扮演“技能专员”，提供本地工具和数据)
from mcp.server.fastmcp import FastMCP

# 1. 实例化MCP服务端，相当于成立一个名为"JobAssistant"的技能工具箱
mcp = FastMCP("JobAssistant3")


# 2. @mcp.tool() 是核心！它像是一个“USB接口”的暴露端
# 挂上这个装饰器，大模型就能通过MCP协议“看”到并调用这个本地函数
@mcp.tool()
def calc_salary(base: int, experience_years: int) -> str:
    """
    根据工作经验的年数，在基础工资的基础上计算最终的工资
    参数base:基础的工资，可以调用别的工具获取
    参数experience_years:工作经验的年数
    """
    salary = base * (1.08 ** experience_years)
    return f"工资水平为:{salary}元"

if __name__ == "__main__":
    # 3. 启动服务端，"stdio"表示通过标准输入输出与客户端(大模型)进行通信对话
    mcp.run(transport="stdio")
