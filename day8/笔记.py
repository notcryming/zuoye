'''
常用的python的后端开发框架：Flask->fastapi(ai主流)->tronado->Django
什么是web服务器与flask？
web服务器的本质：
web服务器是互联网的接待员，负责接受浏览器的请求（比如一个网址），并返回对应的html网页或者数据（json）
浏览器-请求->服务器-响应->浏览器-请求->服务器
整个过程就是http请求-响应循环，flask是把整个过程快速搭建起来的工具
flask的定义：
python轻量级的web框架，微框架
核心极简，只提供最基础的路由和请求处理功能
扩展插件来进行扩充
相对django，更灵活
适用场景：pandas、pytorch、openai，快速开发原型，api服务，ai应用后端
flask基础语法
环境搭建和构建实例
from flask import Flask
app = Flask(__name__)
模板文件都放在template/文件夹里
静态文件（CSS/JS/图片）默认放在static/文件里
路由装饰器@app.route('/')
@app.route('/')   # 127.0.0.1:5000/
def index():
    return "<h1>欢迎进入Flask世界！</h1>"
@app.route('/')：当前用户访问首页的，执行以下函数
def index()：随便取，如果是首页一般默认写index
return函数返回的内容会直接显示在浏览器里面
动态路由：@app.route("greet/<name>")
最实用和最常用的功能：让url的一部分可以变成一个变量
<name>：一个占位符，用户访问时取用户的name填入实际的值
默认是字符串可以用<int:name><float:name><path:name><uuid:name>来指定接收类型
启动服务器，必须写在程序入口里，确保必须只能在这个文件里启动，避免在import时意外启动
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000,debug=True)
模块二：路由配置与请求响应处理：
http请求方法
GET POST PUT(更新内容) DELETE PATCH(修改) HEAD(看看文件信息) OPTIONS
Flask选择接受的http请求方法，默认只接受GET
@app.route("/users", methods=["post"])   # 只接受POST
请求与响应对象
Flask提供几个内置对象来处理请求和生成响应
request.args.get("关键字", 默认值)
当用户访问你的网站时，`request` 对象里包含了**所有用户发来的信息**：
request.method,request.args,request.form,request.get_json(),request.headers,request.cookies
jsonify对象：返回json数据
web开发中，前后端分离，后端通常返回的都是json数据，前端JavaScript做渲染
flask获取参数的方式，
request.args.get()
路由（url）<变量名>
request.form.get()
request.get_json()
用户认证系统（注册/登录/登出）
密码安全：绝对不能明文存储！
user_db = {"admin": "123456"}
用哈希算法单向加密
Session保持登录状态？
Session是什么？
http协议无状态的，session记住用户的身份的一种机制
flask用session，其工作原理：
用户登录以后，服务器会自动生成一个Session数据（比如{“username”: "admin"}）
服务器用secret_key对这个数据进行加密签名，生成一个cookie给到浏览器
浏览器之后的每次请求都会自动带上这个cookie
服务器解密cookie，放行，数据互通
app.secret_key = secrets.token_hex(16)  # 生成一个32位的随机密钥





'''



