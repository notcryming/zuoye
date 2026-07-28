'''
【程序32】
题目：取一个整数a从右端开始的4～7位。
程序分析：可以这样考虑：
(1)先使a右移4位。
(2)设置一个低4位全为1,其余全为0的数。可用~(~0 < <4)
(3)将上面二者进行&运算。
'''
a = list(input())
a = a[-7:-3]
for i in a:
    print(i, end="")
print("\n")

a = int(input("请输入一个正整数a："))
temp = a >> 4
mask = (1 << 4) - 1
res = temp & mask
print(f"提取出来的4~7位数值：{res}")
print(f"对应二进制：{format(res, '04b')}")
print(f"数字a完整二进制：{format(a, '016b')}")
