'''
【程序20】
题目：有一分数序列：2/1，3/2，5/3，8/5，13/8，21/13...求出这个数列的前20项之和。
1.程序分析：请抓住分子与分母的变化规律。
'''
fib = {1: 1, 2: 1}
def Fib(n:int):
    if n <= 0:
        raise ValueError("项数必须大于0！")
    if n in fib:
        return fib[n]
    res = Fib(n - 1) + Fib(n - 2)
    fib[n] = res
    return res
def sum(n):
    total = 0
    while n != 0:
        total += Fib(n+2)/Fib(n+1)
        n -= 1
    return total

print(sum(20))

