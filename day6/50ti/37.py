'''
【程序37】
题目：有n个人围成一圈，顺序排号。从第一个人开始报数（从1到3报数），凡报到3的人退出圈子，问最后留下的是原来第几号的那位。
'''
print("请问有几个人？：", end="")
n = int(input())
lst = list(i for i in range(1,n+1))
flag = 0
time = -1
while len(lst)!=1:
    flag += 1
    time += 1
    if flag % 3 == 0:
        lst.pop(time%len(lst))
        time -= 1
    if time+1 == len(lst):
        time -= len(lst)
print(f"留下的是原来的第{lst[0]}位")


