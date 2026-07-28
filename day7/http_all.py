# 用 urllib.request 模块发送http请求
from urllib import request

# 1.建立连接+发送请求
url = "http://httpbin.org/get"

# 创建一个请求对象
req = request.Request(url)
req.add_header("User-Agent","Mozilla/5.0 (Windows NT 10.0;Win64;x64)")

response = request.urlopen(req)

print("===状态码===")
print(response.status)

print("\n===响应头===")
print(type(response.headers))
for key, value in response.headers.items():
    print(f"{key}:{value}")

print("\n===响应内容===")
print(response.read().decode("utf-8")[:200])


