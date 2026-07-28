'''
【程序2】
题目：判断101-200之间有多少个素数，并输出所有素数。
1.程序分析：判断素数的方法：用一个数分别去除2到sqrt(这个数)，如果能被整除，
则表明此数不是素数，反之是素数。
'''
from math import sqrt

list_num = []
count = 0   # 计数
for i in range(101, 201):
    for j in range(2, int(sqrt(i)+1)):
        if i % j == 0:
            break
        if j == int(sqrt(i)):
            print(f"{i}是素数")
            list_num.append(i)
            count += 1
print(f"101到200间一共有{count}个素数")
print("他们分别是：")
for i in range(0,len(list_num)):
    print(list_num[i], end=" ")
    if i % 10 == 9:
        print("\n")
