import secrets
from flask import Flask, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
# 配置会话密钥
app.secret_key = secrets.token_hex(16)

# 模拟数据库
user_db = {}

@app.route("/auth/register", methods=["POST"])
def register():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({
            "error": "用户名或密码缺失"
        }), 400
    username = data["username"]
    password = data["password"]
    if username in user_db:
        return jsonify({
            "code": 400,
            "message": "用户名已存在"
        }), 400
    # 核心安全操作：对密码进行哈希加盐存储
    password_hash = generate_password_hash(password)
    user_db[username] = {
        "password_hash": password_hash,
        "role": "user",
        "status": "active"
    }
    print("============", user_db)
    return jsonify({
        "code": 200,
        "msg": "注册成功"
    })

@app.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    if not data or "username" not in data or "password" not in data:
        return jsonify({
            "error": "用户名或密码缺失"
        }), 400
    username = data["username"]
    password = data["password"]
    if username not in user_db:
        return jsonify({
            "code": 401,
            "message": "用户不存在"
        }), 401
    # 核心安全操作：对密码进行哈希加盐存储
    if not check_password_hash(user_db[username]["password_hash"], password):
        return jsonify({"code": 401, "msg": "密码错误"}), 401
    # 登录成功，设置会话，将用户名和其他相关信息存入session
    session["username"] = username
    session["role"] = user_db[username]["role"]
    return jsonify({"code": 200, "msg": "登录成功", "username": username, "role": session["role"]})

@app.route("/auth/profile")
def profile():
    if "username" not in session:
        return jsonify({"code": 401, "msg": "请先登录"}), 401
    print(user_db[session["username"]])
    return jsonify(user_db[session["username"]])

@app.route("/auth/logout", methods=["POST"])
def logout():
    session.clear()
    print("已成功退出")
    return jsonify({"code": 200, "msg": "已成功退出"})



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5003, debug=True)
