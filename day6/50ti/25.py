'''
【程序25】
题目：一个5位数，判断它是不是回文数。即12321是回文数，个位与万位相同，十位与千位相同。
'''
lst = []
string = input()
for iter in string:
    lst.append(iter)
lst1 = lst[::-1]
if lst1==lst:
    print(f"{string}是回文数")
else:
    print(f"{string}不是回文数")
