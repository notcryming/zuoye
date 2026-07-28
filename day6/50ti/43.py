'''
【程序43】
题目：求0—7所能组成的奇数个数。
'''
total = 0
for n in range(1, 9):
    if n == 1:
        count = 4
    else:
        count = 7 * (8 ** (n - 2)) * 4
    total += count
    print(f"{n}位奇数的个数: {count}")
print("0-7所能组成的奇数总个数:", total)