'''
【程序26】
题目：请输入星期几的第一个字母来判断一下是星期几，如果第一个字母一样，则继续判断第二个字母。
1.程序分析：用情况语句比较好，如果第一个字母一样，则判断用情况语句或if语句判断第二个字母。
Monday,Tuesday,Wednesday,Thursday,Friday,Saturday,Sunday
M-周一，T-周二周四，W-周三，F-周五，S-周六周日
'''
lst = []
string = input()
for iter in string:
    lst.append(iter)
if lst[0] == 'M':
    print("星期一")
elif lst[0] == 'W':
    print("星期三")
elif lst[0] == 'F':
    print("星期五")
elif lst[0] == 'T':
    if lst[1] == 'u':
        print("星期二")
    else:
        print("星期四")
else:
    if lst[1] == 'a':
        print("星期六")
    else:
        print("星期天")


