# from langchain_core.prompts import PromptTemplate

# prompt = PromptTemplate.from_template("讲一个关于{topic}的笑话")

# print(prompt.invoke({"topic":"猫"}))


# from langchain_core.prompts import ChatPromptTemplate
# chat_prompt = ChatPromptTemplate.from_messages([
#     ("system", "你是一个幽默的助手"),
#     ("human", "讲一个关于{topic}的笑话")
# ])
# print(chat_prompt.invoke({"topic": "猫"}))
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")
base_url = os.getenv("BASE_URL")
model_name = os.getenv("MODEL_NAME")



def call_llm2(title, descs, feature):
    chat_prompt_template = ChatPromptTemplate.from_messages([
        ("system", "你是一位专业的{role}，拥有10年以上从业经验，语气轻松活泼"),
        ("human", "请帮我为产品/话题写推广文案。文案的主题为{title}，具体描述为{descs}，要能体现{feature}等特点，要求不超过100字"),
        ("ai", "人工智能，是模拟人类智能行为的计算机系统，具备学习、推理、决策与 任务执行能力。"),
        ("human", "请帮我生成一句slogan。")
    ])
    llm = ChatOpenAI(
        model=model_name,
        api_key=api_key,
        base_url=base_url
    )
    # chat_prompt_template.invoke({"title": title, "descs": descs, "feature": feature})
    question = f"需求主题：人工智能。\n需求描述：人工智能是指通过模拟人类智能行为而设计的计算机系统。\n需求特点：它能够学习、推理、决策和执行任务，与人类用户进行交互。"
    prompt = chat_prompt_template.format_messages(role="文案编辑", title=title, feature=feature, descs=descs)
    print(prompt)
    response = llm.invoke(prompt)
    return response.content

print(call_llm2('人工智能','人工智能是指通过模拟人类智能行为而设计的计算机系统。','它能够学习、推理、决策和执行任务，与人类用户进行交互'), end="", flush=True)

