# ====================================================================
#  保险精准营销 Flask 项目 —— Docker 镜像构建文件
# ====================================================================
#  基础镜像：python:3.11-slim（精简版，体积约 45MB）
#  分层策略：依赖层(requirements.txt)与代码层分离，改代码不重装依赖
# ====================================================================

FROM python:3.11-slim

# ===== 0. 国内镜像源加速（apt + pip）=====
# 替换 Debian 默认源为阿里云镜像，解决国内 apt 下载慢
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources \
    && sed -i 's|security.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources

# pip 全局指定阿里云 PyPI 镜像
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ \
    && pip config set global.trusted-host mirrors.aliyun.com

# ===== 1. 系统依赖 =====
# gcc/g++：编译 bcrypt / scipy 等 C 扩展
# libglib2.0-0 / libsm6 / libxext6 / libxrender1 / libgl1：matplotlib 运行时依赖
# fonts-noto-cjk：中文字体，避免图表中文乱码（方块/缺字）
# fonts-wqy-zenhei：备选中文字体
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgl1 \
    fonts-noto-cjk \
    fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# ===== 2. 工作目录 =====
WORKDIR /app

# ===== 3. 依赖层（仅 requirements.txt 变化才重建）=====
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ===== 4. 代码层（代码变更只重建此层）=====
COPY . .

# ===== 5. 创建持久化目录 =====
# instance：SQLite 数据库文件
# data/models：训练产出的 .joblib 模型文件
# 即使 docker-compose 挂载卷，目录也需预先存在避免权限问题
RUN mkdir -p instance data/models

# ===== 6. matplotlib 缓存目录 =====
# 容器内 root 用户无法写默认缓存路径，指定到 /tmp 避免报错
ENV MPLCONFIGDIR=/tmp/matplotlib

# ===== 7. 暴露端口 =====
EXPOSE 5000

# ===== 8. 启动命令 =====
# create_app() 内部自动：建表 → 初始化 admin 账号 → 初始化 Prompt 模板
CMD ["python", "run_flask.py"]
