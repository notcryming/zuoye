from langchain_core.prompts import PromptTemplate

prompt = PromptTemplate.from_template("讲一个关于{topic}的笑话")

print(prompt.invoke({"topic":"猫"}))




from langchain_core.prompts import ChatPromptTemplate
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个幽默的助手"),
    ("human", "讲一个关于{topic}的笑话")
])
print(chat_prompt.invoke({"topic": "猫"}))
# 输出：
# ChatPromptValue(messages=[
#   SystemMessage(content='你是一个幽默的助手'),
#   HumanMessage(content='讲一个关于猫的笑话')
# ])






