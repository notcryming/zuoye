'''
temperature，Top-p，Max Length
prompt engineering
角色设定
任务描述
上下文（约束或要求）
输出格式
langchain
大模型：具有大量参数和复杂结构的神经网络模型，
基于海量数据预训练而来的生成式模型，
能够完成各种复杂的任务，处理各种nlp，cv领域的任务
智能体：大模型+工具+上下文管理，大模型本身只具备思考能力，
不具备行动能力，在大模型的基础上赋予他实际行为能力
json结果->接口，操作。{}数据，api接口调用，帮我完成认证和登录和订票。
langchain：把以上操作对应的底层代码进行封装的第三方库，2022年哈佛研发的一个开源框架，
主要用于开发由大模型驱动的应用程序，比如：搭建智能体，问答系统，对话机器人，文档搜索等
langchain发布比chatgpt还早一个月
版本问题，使用1.0版本最好，里程碑式的更新，比较稳定的状态，统一了api标准，去除了之前杂乱的库
相关框架
Langchain
llamaindex
SpringAI Alibaba
SemanticKernel
简化开发难度，学习成本低，开发人员，现成的链式组装，具体的功能
langchain的使用场景
RAG：检索增强生成
rag能解决什么问题？
幻觉，知识滞后和训练成本高
Agent vs RAG vs SFT(监督微调) vs Prompt Eengineering
langchain核心组件
Model I/O chains RAG Agents
format：通过模板管理大模型的输入，将原始数据格式转化为模型可以处理的形式，插入到模板中，然后送给模型进行处理
predict：调用lllm（instruct/chat）接口，进行预测或者生成回答
parse：规范化大模型的输出，比如大模型的输出格式规定为json格式
chains
链条：将多个组件组合成一个完整的流程，方便链式调用
组件：水管本身
链接：“|”数据的链条式处理
一个链条也可以成为一个单独的组件
统一的组件调用方法：invoke（）
PromptTemplate vs ChatPromptTemplate
PromptTemplate是“纯字符串模板”，将原本的文本补全给原生模型使用；
ChatPromptTemplate是“带角色的消息列表模板”，给chat模型（GPT3.5/Claude等），天然支持多轮对话
instruct类型的模型，只能接受PromptTemplate模板的输入，ChatPromptTemplate输入会报错
chat类型模型（平时用的都是），语法上可以兼容两种，但是为了符合多轮对话管理的特性，更推荐配套使用ChatPromptTemplate
本质与数据结构不同
PromptTemplate-instruct/chat模型
继承：StringPromptTemplate
输出：单一字符串（不会有角色）

'''


