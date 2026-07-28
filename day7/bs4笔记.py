from bs4 import BeautifulSoup
# 创建soup对象，第二个空是解析器，还可以放html.parser
soup = BeautifulSoup(html, "lxml")
# find找到第一个匹配目标
p = soup.find("p", class_="text")          # class查找
p = soup.find("p", id="")                  # id查找
h1 = soup.find("h1", title="标题")          # 属性查找
# find_all()找到全部并返回列表
result = soup.find_all("a", href="https://baidu.com", limit=2)     # 多个条件，limit限制返回个数
# select()CSS选择器，返回的都是列表
# 标签选择
soup.select("p")
# class 点 .
soup.select(".text")
# id #
soup.select("#p1")
# 层级查找 空格 后代
soup.select("div .text")
# 直接子标签 >
soup.select("body > div > h1")
# 属性选择器
soup.select('a[href="https://baidu.com"]')


