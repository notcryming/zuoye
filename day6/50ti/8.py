'''
【程序8】
题目：求s=a+aa+aaa+aaaa+aa...a的值，其中a是一个数字。例如2+22+222+2222+22222(此时共有5个数相加)，几个数相加有键盘控制。
1.程序分析：关键是计算出每一项的值。
'''
def term(a, i):
    total = 0
    while i:
        total += a * 10 ** (i -1)
        i -= 1
    return total


total = 0
while 1:
    print("确认a的值（1-9）：",end="")
    try:
        a = int(input())
        if a not in range(1, 10):
            print("请输入1-9的整数")
        else:
            break
    except ValueError as e:
        print("请输入数字", e)
while 1:
    print("几个数相加：",end="")
    try:
        i = int(input())
        if i < 0:
            print("请输入大于0的整数")
        else:
            break
    except ValueError as e:
        print("请输入数字", e)
time = i
while i:
    total += term(a, i)
    i -= 1
print(f"a为{a}，{time}个数相加的总和为：{total}")
