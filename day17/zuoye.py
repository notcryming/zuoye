from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
# 把.env的键值对添加到环境变量
load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")

llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url,
        temperature=0.3
    )



def step3_generate_intro(name, job, skills):
    # 创建提示词模版的对象
    chat_prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个专业的人力资源顾问，擅长帮人写简洁有力的自我介绍"),
            ("human", "请根据以下信息，帮我写一段 50 字以内的自我介绍。姓名：{name}，职位：{job}，技能：{skills}")
        ]
    )
    # LCEL 链式拼接：prompt | model | parser
    chain = chat_prompt_template | llm | StrOutputParser()
    # 执行调用
    return chain.invoke({"name": name, "job": job, "skills": skills})



def step4_generate_slogan(name, job):
    prompt_template_str = """
请根据以下信息，生成一句 15 字以内的个人 slogan，要求朗朗上口。姓名：{name}，职位：{job}
"""
    prompt_template = PromptTemplate(
        template=prompt_template_str,
        input_variables=["name", "job"]
    )
    # 填充提示词模版的参数
    prompt = prompt_template.format(name=name, job=job)
    # 调用模型
    response = llm.invoke(prompt)
    return response.content



class Card(BaseModel):
    name: str = Field(description="姓名")
    job: str = Field(description="职位")
    intro: str = Field(description="自我介绍")
    slogan: str = Field(description="个人 slogan")
    skills: list = Field(description="技能列表")


def step5_generate_card(name, job, skills, intro, slogan):
    # 2. 创建 JsonOutputParser
    parser = JsonOutputParser(pydantic_object=Card)
    # 3. 使用 parser.get_format_instructions() 作为 system 提示词
    messages = [
        SystemMessage(content=parser.get_format_instructions()),
        HumanMessage(content=(
            f"请根据以下信息生成一张结构化的 AI 智能名片。\n"
            f"姓名：{name}\n职位：{job}\n技能：{skills}\n"
            f"自我介绍：{intro}\n个人 slogan：{slogan}\n"
            f"请输出符合格式要求的 JSON。"
        ))
    ]
    # 4. 调用模型生成结构化名片数据
    response = llm.invoke(messages)
    # 5. 解析为 Python 字典
    return parser.invoke(response)


# ======================
# 第 6 步：完整运行
# ======================
if __name__ == "__main__":
    # 测试数据
    name = "张三"
    job = "Python 开发工程师"
    skills = "Python, LangChain, FastAPI"

    # 按顺序执行第 3、4、5 步
    print("【第 3 步：生成自我介绍】")
    intro = step3_generate_intro(name, job, skills)
    print(intro)
    print()

    print("【第 4 步：生成个人 slogan】")
    slogan = step4_generate_slogan(name, job)
    print(slogan)
    print()

    print("【第 5 步：生成结构化名片】")
    card = step5_generate_card(name, job, skills, intro, slogan)
    print("解析后的字典结果：")
    print(card)
    print("类型：", type(card))
    print()

    # 最终打印一张完整的"名片"
    print("============================")
    print("      AI 智能名片")
    print("============================")
    print(f"姓名：{card['name']}")
    print(f"职位：{card['job']}")
    print(f"自我介绍：{card['intro']}")
    print(f"个人 slogan：{card['slogan']}")
    print(f"技能：{', '.join(card['skills'])}")
    print("============================")
