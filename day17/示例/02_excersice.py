from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()
api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")


def call_llm(title, descs, feature):
    """
    提示词模版功能，展示如何使用提示词模版来生成文案
    1. 创建提示词模版
    2. 初始化语言模型
    3. 填充提示词模版的参数
    4. 调用语言模型生成响应
    """

    # 创建提示词模版
    prompt_template_str = """
    你是一个专业的文案编辑者，你的任务是根据用户的需求，生成符合要求的文案。
    需求主题：{title}
    需求描述：{descs}
    需求特点：{feature}
    文案：xxxx
    要求: 语气轻松活泼，字数控制在100字以内
    """
    # 创建提示词模版的对象
    prompt_template = PromptTemplate(
        template=prompt_template_str,
        input_variables=["title", "descs", "feature"]
    )

    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url
    )

    # 填充提示词模版的参数
    prompt = prompt_template.format(title=title, descs=descs, feature=feature)

    # 得到的提示词
    print(prompt)

    # 调用模型
    response = llm.invoke(prompt)
    return response.content


def call_llm2(title, descs, feature):
    """
    提示词模版功能，展示如何使用提示词模版来生成文案
    1. 创建提示词模版
    2. 初始化语言模型
    3. 填充提示词模版的参数
    4. 调用语言模型生成响应
    """

    # 创建提示词模版的对象
    chat_prompt_template = ChatPromptTemplate.from_messages(
        [
            ("system", "你是一个资深的{role}, 拥有10年以上的从业经验"),
            ("human", "请帮我分析一下: {question}。要求字数不超过100字"),
            ("ai", "人工智能，是模拟人类智能行为的计算机系统，具备学习、推理、决策与 任务执行能力。它能理解语言、识别图像、自主优化，与人类自然交互。 从智能家居到医疗诊断，正悄然重塑生活与工作方式，让机器更懂人性， 让未来更有温度。"),
            ("human", "请帮我生成一句slogan。")
        ]
    )

    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url
    )

    question = f"需求主题：{title}\n需求描述：{descs}\n需求特点：{feature}"
    
    # 填充提示词模版的参数
    prompt = chat_prompt_template.format_messages(role="文案编辑", question=question)

    # 得到的提示词
    print(prompt)

    response = llm.invoke(prompt)
    return response.content


if __name__ == "__main__":
    title = "关于人工智能的文案"
    descs = "人工智能是指通过模拟人类智能行为而设计的计算机系统。"
    feature = "它能够学习、推理、决策和执行任务，与人类用户进行交互。"
    
    # response = call_llm(title, descs, feature)
    # print(response)
    response = call_llm2(title, descs, feature)
    print(response)