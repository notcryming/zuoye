'''
【程序36】
题目：有n个整数，使其前面各数顺序向后移m个位置，最后m个数变成最前面的m个数
'''
print("开始输入数组(输入字母停止)：")
lst = []
while 1:
    try:
        a = int(input())
        lst.append(a)
    except Exception as e:
        print("结束输入")
        break
print(lst)
print("m?:", end="")
m = int(input())
n = len(lst)
# 从倒数m个开始取 与 取到倒数m的前一个
lst = lst[-m:] + lst[:-m]
print(lst)




