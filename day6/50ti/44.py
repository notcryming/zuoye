'''
【程序44】
题目：一个偶数总能表示为两个素数之和。编写程序把一个偶数拆成两个素数。
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

n = int(input("请输入一个偶数: "))
if n % 2 != 0:
    print("请输入偶数!")
else:
    for i in range(2, n // 2 + 1):
        if is_prime(i) and is_prime(n - i):
            print(f"{n} = {i} + {n - i}")
            break