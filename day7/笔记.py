'''
http是浏览器和服务器之间传递数据的一套通信规则。
http的组成
请求行：告诉服务器，用什么方法进行请求，用什么语言，找谁
请求头：告诉服务器，我是谁，我想要什么格式，其他需求
请求体：给到服务器的具体主题（post等才有）
###请求行###
方法/路径/协议版本
比如：GET/index.html HTTP/1.1
方法：告诉服务器要干什么
路径：我要找哪个资源
协议版本：用什么语言
常用的HTTP请求方法
GET POST PUT(更新内容) DELETE PATCH(修改) HEAD(看看文件信息) OPTIONS
GET和POST的完整区别对比
###请求头###
请求头：客户端（浏览器 / Python 爬虫等）发给服务器，附带的一堆描述信息，放在请求行之后、请求体之前。
作用：告诉服务器「我是谁、我想要什么格式数据、Cookie、编码、设备信息」等
请求行
请求头键值对
（空一行）
请求体
示例：
GET /api/user HTTP/1.1
Host: www.example.com
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0
Accept: text/html,application/json  告诉服务器我想要json数据
Accept-Language: zh-CN,zh;q=0.9     q是质量因子，0-1，越大代表越喜欢
Accept-Encoding: gzip, deflate，br
Connection: keep-alive      这次请求结束后是否需要继续保持连接
Cookie: token=abc123    身份凭证->保持登录状态
Referer: https://www.example.com/home       来源页面，告诉服务器你是用哪个页面跳转过来的
content-Type: 请求体的格式（表单，json，上传文件）
Authorization: 用于API认证，告诉服务器这是通行证
默认python爬虫的user-agent是会被拒绝的，所以要伪装UA
###请求体###
POST/PUT/PATCH方法下请求体：服务器真实的实际数据，GET没有请求体的
三种常见的请求体格式：
1.表单格式（application/x-www-form-urlencoded）
username=admin&password=123456&remember=true
2.json格式（application/json）
字典格式
3. 文件上传（multipart/form-data）
用于上传文件，数据有可能被分割为多个部分，每部分都有自己的Content-Type
http响应的组成
状态行：是否成功，用的什么协议
响应头：数据格式，大小，缓存规则等
响应体：HTML网页，JSON数据，图片，视频等
###状态行###
格式：协议版本 状态码 状态描述
比如：HTTP/1.1 200 OK
协议版本：服务器用的http协议版本（HTTP1.1 或 HTTP2）
content-length:
set-cookie:
Cache-Control: 缓存控制，告诉客户端这个内容可以缓存多久
Server: 告诉客户端用的是什么服务器软件
Content-Encoding: 用什么方法压缩



'''
