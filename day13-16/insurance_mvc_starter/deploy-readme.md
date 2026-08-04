# Docker 部署说明

## 一、环境要求

| 项目 | 最低版本 |
|------|----------|
| Docker | 20.10+ |
| Docker Compose | 2.0+（Docker Desktop 内置） |
| 宿主机可用内存 | 2GB+ |
| 宿主机可用磁盘 | 5GB+（镜像约 1.5GB） |

## 二、目录结构

```
insurance_mvc_starter/
├── Dockerfile              # 镜像构建文件
├── docker-compose.yml      # 容器编排配置
├── .dockerignore           # 构建忽略清单
├── run_flask.py            # 生产启动入口（debug=False）
├── requirements.txt        # Python 依赖清单
├── .env                    # 环境变量配置（需自行编辑）
├── .env.example            # 环境变量模板
├── instance/               # SQLite 数据库（持久化卷）
│   └── starter.db
├── data/
│   └── models/             # 训练模型文件（持久化卷）
│       ├── logistic_regression.joblib
│       ├── random_forest.joblib
│       └── xgboost.joblib
└── app/                    # 业务代码
```

## 三、环境变量配置

部署前编辑项目根目录的 `.env` 文件（参考 `.env.example`）：

```env
# ===== 数据库 =====
DATABASE_URL=sqlite:///./instance/starter.db

# ===== JWT 认证 =====
JWT_SECRET_KEY=your-secret-key-change-me
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# ===== 机器学习 =====
MODEL_DIR=data/models

# ===== 大模型 LLM =====
LLM_API_KEY=your-api-key-here
LLM_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
LLM_MODEL=qwen-flash
```

> `LLM_API_KEY` 留空时邮件生成功能自动降级，其他功能不受影响。

## 四、部署命令

> 以下命令使用 `docker compose`（空格，Docker Compose v2+ 语法）。
> 如果使用旧版 Docker Compose v1，请将 `docker compose` 替换为 `docker-compose`（连字符）。

### 1. 构建并启动

```bash
# 首次部署：构建镜像 + 后台启动
docker compose up -d --build

# 后续启动（代码无变更，跳过构建）
docker compose up -d
```

### 2. 查看状态

```bash
# 查看容器运行状态
docker compose ps

# 查看实时日志
docker compose logs -f

# 查看最近 100 行日志
docker compose logs --tail 100
```

### 3. 停止与删除

```bash
# 停止容器（数据保留在宿主机卷中）
docker compose stop

# 停止并删除容器（数据仍保留在宿主机卷中）
docker compose down

# 停止并删除容器 + 删除镜像
docker compose down --rmi local
```

### 4. 重新构建（代码更新后）

```bash
# 修改代码后重新构建镜像
docker compose up -d --build
```

## 五、验证部署

容器启动后执行以下验证：

| 步骤 | 操作 | 预期结果 |
|------|------|----------|
| 1 | 浏览器访问 `http://127.0.0.1:5000` | 显示前端登录页面 |
| 2 | 使用 `admin` / `admin123` 登录 | 登录成功，进入管理后台 |
| 3 | 上传 Excel 数据文件 | 上传成功，提示导入条数 |
| 4 | 训练模型 | 训练完成，生成 3 个模型 |
| 5 | 查看 `./instance/` 目录 | 存在 `starter.db` 文件 |
| 6 | 查看 `./data/models/` 目录 | 存在 3 个 `.joblib` 文件 |

## 六、数据持久化

| 挂载卷 | 容器路径 | 宿主机路径 | 用途 |
|--------|----------|------------|------|
| 数据库 | `/app/instance` | `./instance` | SQLite 数据库文件 |
| 模型 | `/app/data/models` | `./data/models` | 训练产出的模型文件 |

> 停止、删除容器后重新启动，原有客户数据、模型文件、邮件记录不丢失。

## 七、常见问题

### Q1：端口 5000 被占用

修改 `docker-compose.yml` 端口映射，例如改为 `5001:5000`，然后访问 `http://127.0.0.1:5001`。

### Q2：容器启动后无法访问

```bash
# 检查容器状态
docker compose ps

# 查看启动日志排查错误
docker compose logs --tail 50
```

### Q3：中文字体在图表中显示为方块

镜像已安装 `fonts-noto-cjk` 和 `fonts-wqy-zenhei`。如仍有问题，进入容器检查：

```bash
docker exec -it insurance-ai-web fc-list :lang=zh
```

### Q4：LLM 邮件生成失败

确认 `.env` 文件中 `LLM_API_KEY` 已填写有效的通义千问 API Key。留空时功能降级（返回 failed 状态），不影响其他模块。

### Q5：如何进入容器调试

```bash
docker exec -it insurance-ai-web bash
```
