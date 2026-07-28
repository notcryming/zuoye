'''
【程序27】
题目：求100之内的素数
'''
from math import sqrt

list_num = [2,3]
for i in range(2, 100):
    for j in range(2, int(sqrt(i)+1)):
        if i % j == 0:
            break
        if j == int(sqrt(i)):
            print(f"{i}是素数")
            list_num.append(i)
print("素数分别是：")
for i in range(0,len(list_num)):
    print(list_num[i], end=" ")
    if i % 10 == 9:
        print("\n")


