#创建.env文件，填入你的大模型API key
'''
API_KEY=
BASE_URL=
MODEL_NAME=
'''
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

llm = ChatOpenAI(
    model=model_name,
    api_key=api_key,
    base_url=base_url
)

response = llm.invoke("你好")
print(response.content)

for chunk in llm.stream("怎么打好王者荣耀"):
    print(chunk.content,end="", flush=True)

