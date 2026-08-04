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
Docker是用来部署的
一次构建，随处运行
轻量高效
隔离性强
运维便捷
镜像：只读的环境模板，包括代码运行所需要的所有代码，依赖，库，配置文件
容器：镜像运行后的运行实例，独立可运行的服务进行，一个镜像可以有无数个容器，并且容器之间数据默认隔离
仓库：类似github仓库，存放镜像的远程服务器，用于共享和下载镜像
##核心工作流程##
拉取镜像/构建镜像、基于镜像启动容器--运行容器提供服务--管理容器生命周期
启动一个容器（初尝试）
docker-compose up -d
docker核心命令
docker[命令][参数]
# 查看正在运行的容器
Docker -ps
# 启动（如果代码变动重新构建部署）
docker-compose up -d
# 停止
docker compose down
# 重启
docker compose restart
# 删除容器
docker rm 容器ID/容器名
# 查看容器日志
docker logs -f 容器ID
# 清理终止的容器，无用镜像，缓存
docker system prune -a
自注意力机制
多头注意力机制
'''
import torch
print(torch.__version__)
print(torch.cuda.is_available())

