from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 加载环境变量 
load_dotenv()  # 执行此函数后，.env文件中的键值对会被加载到系统环境变量中

# 从环境变量中获取模型所需的配置信息
api_key = os.getenv("API_KEY")  # 获取API密钥
base_url = os.getenv("BASE_URL")  # 获取API请求的基础URL（指向硅基流动等第三方平台的接口）
model_name = os.getenv("MODEL_NAME")  # 获取要调用的具体模型名称（例如qwen-flash等）

#构建一个Pydantic类
class People(BaseModel):
    name: str = Field(description="姓名")
    age: int = Field(description="年龄")
    sex: str = Field(description="性别")
    address: str = Field(description="地址")

def call_llm():
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url
    )
    json_parser = JsonOutputParser(pydantic_object=People)    
    messages = [
    SystemMessage(content=json_parser.get_format_instructions()),  # 生成响应 JSON 的系统提示词
    HumanMessage(content="给我生成1个人的数据")
    ]
    print("============================")
    print(messages)
    # 调用模型
    response = llm.invoke(messages)
    resp = json_parser.invoke(response)
    print("000000000000000000000000000000")
    print(resp)


def call_llm2():
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url
    )
    json_schema = {
        "name": "AnimalList",
        "schema": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "animal": {
                        "type": "string",
                        "description": "动物名称"
                    },
                    "age": {
                        "type": "integer",
                        "description": "动物年龄"
                    }
                },
                "required": ["animal", "age"],
                "additionalProperties": False
            }
        }
    }

    messages = [
        HumanMessage(content="给我生成1种动物的名称以及对应的年龄")
    ] 
    response = llm.with_structured_output(
        schema=json_schema,
        method="json_schema",
        include_raw=True
    ).invoke(messages)       

    print("=============================================")
    print(response["raw"])
    print("000000000000000000000000000000000000000000000000")
    print(response["parsed"])



if __name__ == "__main__":
    # call_llm()    
    call_llm2() 