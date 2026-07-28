from flask import Flask, request, jsonify
app = Flask(__name__)
user_db = [{"username": '1'}, {"username": '2'},
           {"username": '3'}, {"username": '4'},
           {"username": '5'}, {"username": '6'},
           {"username": '7'}, {"username": '8'},
           {"username": '9'}, {"username": '10'}]

@app.route('/')   # 127.0.0.1:5001/
def index():
    return "<h1>欢迎进入Flask世界！</h1>"

@app.route("/api/register", methods=["post"])
def register():
    # post从body里面传入参数，用request获取参数
    data = request.get_json()
    username = data.get("username")
    if not username:
        return jsonify({"code": 400, "msg": "用户名不能为空"})
    user_db.append({"username": username})
    return jsonify({
        "code": 200,
        "id": len(user_db),
        "msg": "注册成功！",
    })

@app.route("/api/users")
def get_users():
    # 用户访问/api/users?page=1&limit=5
    page = int(request.args.get("page", 1))  # "2"(默认值
    limit = int(request.args.get("limit", 5))
    lst = user_db[(page-1)*limit:page*limit]
    return jsonify({
        "code": 200,  # 状态码
        "msg": "用户信息获取",  # 提示信息
        "data": lst  # 实际数据
    })


@app.route('/api/submit-form', methods=['POST'])
def submit_form():
    """
    表单提交接口
    Postman: POST http://127.0.0.1:5001/api/submit-form
    Body (form-data): username=test_user, email=test@example.com
    """
    username = request.form.get('username')
    email = request.form.get('email')

    if not username:
        return jsonify({"code": 400, "msg": "用户名不能为空"}), 400

    return jsonify({"code": 200, "msg": f"收到表单数据：用户={username}"})



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)


