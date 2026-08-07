'''
Agent
定义：具备自主思考、步骤规划、工具调用能力的智能系统。基于Model I/O开发，会比chains更高级，
不需要预设固定流程，能根据用户需求，自主判断“要不要调用工具”，“要调用哪个工具”，“按什么顺序调用工具”，
“工具调用失败如何处理”（重试，换一个工具）
Agent的核心组成
LLM（大语言模型）
工具
提示词
Agent Excutor：Agent的执行器，总体架构，负责运行Agent的思考流程、调用工具、处理工具返回结果。
最终给出答案“你查一下公司java岗位的薪资和要求？”
需要查数据库->调用数据库工具->提取岗位信息->整理成回答

Function Calling和MCP
工具调用是agent的核心，两种核心调用工具方式：Function Calling和MCP
Function Calling（Tool Calling）
是大模型调用外部工具/函数的标准方式，本质是大模型需要识别到当前的问题需要去调用哪个函数，传入哪些参数，
然后执行函数，获取返回结果，再结合结果生成最终回答
Function Calling（Tool Calling）进阶
支持多轮对话，核心思想：将message做一个拼接
上下文管理策略：
* 固定轮数保留
* 固定max-length，压缩前文
* 根据问题类型，差异化处理
* 根据业务场景而定
MCP
(1)概念：
是多工具并行调用方式，并行处理多个任务，把所有工具的返回结果合并后再生成回答，提高效率。
类似于前后端分离的概念，agent和tool是分离的，所有工具放在一个或者多个服务，起了服务，就可以去调用工具，复合项目开发的高解耦和可扩展维护。
(2)实例
server.py
client.py
mcp.run(transport='stdio')transport参数详解
stdio：客户端拉起一个本地的MCP-Server子进程，通过进程进行管理和通信
优点：零网络配置，本地调用最简单，适合本地工具服务
缺点：只能启动本地服务，无法远程服务
sse：HTTP单向流式
通信：客户端发送HTTP请求，服务端持续SSE事件推送，这个请求走POST
适合：部署在后端http服务、远程mcp服务
需要额外传url参数
websocket
双向实时通信，适合频繁双向交互
tcp
内网自定义TCP服务，很少用
in-memory：服务端和客户端需要在同一个python进程里面，这个用来做测试


'''
from langchain_core.prompts import ChatPromptTemplate
import asyncio
from langchain_openai import ChatOpenAI
from langchain.tools import tool
from langchain.agents import create_agent
import os
import requests
from urllib.parse import quote
from pypinyin import lazy_pinyin
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")
headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
city = "成都市"

url = f"https://wttr.in/{city}?format=%C+%t"
try:
    resp = requests.get(url, headers=headers, timeout=5)
    soup = BeautifulSoup(resp.text, "html.parser")
    term_div = soup.find(class_="term-container")
    if term_div:
        weather_text = term_div.get_text(strip=True)
        print(f"提取结果：{weather_text}")
    else:
        print("未找到天气节点")
except Exception as e:
    # API出错返回错误文本，Agent会收到这个报错信息
    print("调用IP查询接口失败，错误信息：{str(e)}")

