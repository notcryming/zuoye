from flask import Flask, request, jsonify, session

# 创建Flask引用实例，Flask()是flask提供的朱磊，是整个应用的大脑
# app是变量名，可以改成任意的名字，如“my_server”，之后的路由和配置都要通过这个变量
# __name__内置变量，代表当前模块的名字，告诉Flask从哪里加载静态文件（css/js）和末班（html）
app = Flask(__name__)

@app.route('/')   # 127.0.0.1:5000/
def index():
    return "<h1>欢迎进入Flask世界！</h1>"

@app.route("/greet/<name>")
def greet(name):
    return f"你好，{name}！欢迎来到空间站。"

@app.route("/search")
def search():
    # 用户访问 /search?keyword=python&page=2
    keyword = request.args.get("keyword")   # "python"
    page = request.args.get("page", 1)      # "2"(默认值为1)
    return f"搜索关键词：{keyword}，第{page}页"

@app.route("/api/user")
def get_user():
    user = {
        "id": 1,
        "name": "张三",
        "email": "张三@example.com"
    }
    return jsonify(user)

    '''
    return jsonify({
        "code": 200,           # 状态码
        "msg": "用户信息获取",   # 提示信息
        "data": {...}          # 实际数据
    })
    '''


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)


