# urllib 模块基础用法
from urllib import request
from urllib import parse

# get请求
url = "http://httpbin.org/get"
response = request.urlopen(url)
print(response.read().decode("utf-8"))

# 带参数的get请求
params = {"name":"张三", "age":"25"}
url_with_params = "http://httpbin.org/get?" + parse.urlencode(params)
print("==========", url_with_params)
response = request.urlopen(url_with_params)
print(response.read().decode("utf-8"))

