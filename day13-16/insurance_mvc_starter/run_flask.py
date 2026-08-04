"""Docker / 生产环境启动入口

【和 run.py 的区别】
  run.py：debug=True，开发热重载，仅本地开发用
  run_flask.py：debug=False，生产模式，Docker 容器启动入口

【为什么单独建文件而非改 run.py？】
  保留 run.py 给开发者本地调试（debug=True 有热重载 + 调试器），
  run_flask.py 专供 Docker / 生产部署，职责分离互不干扰。
"""
import os
import sys

# 确保项目根目录在 Python 路径中（Docker WORKDIR 已是 /app，此行保险）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()

if __name__ == "__main__":
    # host=0.0.0.0：容器内监听所有网卡，外部宿主机可访问
    # debug=False：生产模式，关闭调试器 + 热重载
    app.run(host="0.0.0.0", port=5000, debug=False)
