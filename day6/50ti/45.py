'''
【程序45】
题目：判断一个素数能被几个9整除
'''

def is_prime(n):
    if n <= 1:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    return True

n = int(input("请输入一个素数: "))
if not is_prime(n):
    print("输入的数不是素数!")
else:
    count = 0
    temp = n
    while temp % 9 == 0:
        count += 1
        temp = temp // 9
    print(f"素数{n}能被{count}个9整除")