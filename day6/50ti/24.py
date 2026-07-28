'''
【程序24】
题目：给一个不多于5位的正整数，要求：一、求它是几位数，二、逆序打印出各位数字。
'''
lst = []
string = input()
for iter in string:
    lst.append(iter)
lst = lst[::-1]
print(f"它是{len(lst)}位数")
for iter in lst:
    print(iter, end="")


