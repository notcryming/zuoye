'''
【程序6】
题目：输入两个正整数m和n，求其最大公约数和最小公倍数。
1.程序分析：利用辗除法。
'''

def change(a, b):
    if a < b:
        return b, a
    return a, b

# 循环实现
def min1(a, b):
    while b != 0:
        mid = b
        b = a % b
        a = mid
    return a

# 递归实现
def min2(a, b):
    if b != 0:
        a = a % b
        return min2(b, a)
    else:
        return a

# m, n = input("请输入两个数字，空格分隔：").split()
print("请输入两个数m和n，我将返回两者的最大公约数与最小公倍数")
print("m=", end="")
m = int(input())
print("n=", end="")
n = int(input())
m, n = change(m, n)
min = min2(m, n)
max = m*n//min
print(f"最大公约数：{min} 最小公倍数：{max}")
