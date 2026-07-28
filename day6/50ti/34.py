'''
【程序34】
题目：输入3个数a,b,c，按大小顺序输出。
1.程序分析：利用指针方法。
'''
print("请输入a,b,c(用空格分割)：", end="")
a, b, c = map(int, input().split())
if a < b:
    a, b = b, a
if a < c:
    a, c = c, a
if b < c:
    b, c = c, b
print(a,b,c)

