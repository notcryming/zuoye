'''
【程序4】
题目：将一个正整数分解质因数。例如：输入90,打印出90=2*3*3*5。
程序分析：对n进行分解质因数，应先找到一个最小的质数k，然后按下述步骤完成：
(1)如果这个质数恰等于n，则说明分解质因数的过程已经结束，打印出即可。
(2)如果n > k，但n能被k整除，则应打印出k的值，并用n除以k的商,作为新的正整数你n,重复执行第一步。
(3)如果n不能被k整除，则用k+1作为k的值,重复执行第一步。
'''
from math import sqrt

def sushu(n, list_num:list):
    for i in range(5, n+1):
        for j in range(2, int(sqrt(i)+1)):
            if i % j == 0:
                break
            if j == int(sqrt(i)):
                list_num.append(i)

list_num = [2, 3]
flag = 1
print("请输入一个正整数n：", end="")
n = int(input())
sushu(n, list_num)
print(f"{n}=", end="")
while flag:
    for i in list_num:
        if n % i == 0:
            if n == i:
                print(i)
                flag = 0
            else:
                print(f"{i}*", end="")
                n /= i
            break
