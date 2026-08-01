'''
技术架构方案MVC：model-view-controller
bcrypt哈希加盐加密，jwt角色认证
app/v1：路由端口，后续可迭代多个版本
core：所有项目都需要的操作层，core是基本操作
（下一步构建）service的文件夹：实际的业务层，跟core是平级的，core是基本操作，service是具体的业务操作
models：对接DB的操作层
schemas：基于pydanic的校验层
（后续构建）static：前端
blueprint路由分组
g对象：请求级全局变量
jwt：用于在客户端和服务器之间安全传输信息
Session是服务器存储的通关信息，jwt是浏览器和客户端自己存的通关信息（过期前无法主动失效）
RBAC角色权限控制
role-based access control，基于角色的访问控制，
核心思想：不直接给用户授权，而是给角色授权，用户通过角色的判定来获取权限
pydantic（可以理解为带校验功能的json）的扩展只需要校验类型，另外，加一个field约束
大模型调用，openai兼容接口的大模型
统一响应信封：所有接口都返回同一种结构
业务码的约定：用以给前端或者其他合作的后端开发人员看
蓝图聚合，把各项业务的蓝图放一起
'''



