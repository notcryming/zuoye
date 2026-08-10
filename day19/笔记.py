'''
多mcp不如多agent，路由agent更改配置麻烦，
长对话冗余多花token
langchain -> langgraph
langchain是普通链式结构，对于复杂业务流程难以实现，需要写很多判断分支和组合，
十分冗余，且容易出错，不好排查问题。
langgraph：图结构，基于状态机的LLM Agent编排框架，
继承Langchain，用图结构来管理节点、状态、路由分支、并发、循环
langgraph五大核心概念
##状态机state
整个流程图的全局的类，所有节点都可以读取和修改这个状态机里的数据（python使用TypeDict来定义字段）
##节点node
每一个节点函数会接收当前state，返回一个需要更新的字典，自动合并到状态机
##边edge
add_edge(A, B)来创建两个节点之间的关联
START：流程图的入口
END：流程图的出口
##条件边conditional-edge
动态路线，根据函数的返回值决定下一步要去到那一个节点
返回单一字符串 -> 串行跳转；返回字符串列表 ->开启多节点并发执行
##workflow工作流
StateGraph实例，添加节点，配置路线之后compile成可运行对象，
调用.invoke(初始状态)启动智能体
coze/dify：可视化拖拽的低代码平台，快速演示demo
langchain：大模型组件库，适配简单线性业务，快速验证想法
langgraph：可编程状态工作引擎，支撑复杂逻辑和生产级上限
'''