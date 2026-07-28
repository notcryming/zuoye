'''
【程序49】
题目：计算字符串中子串出现的次数
'''

s = input("请输入主字符串: ")
sub = input("请输入子字符串: ")
count = s.count(sub)
print(f"子串'{sub}'在主字符串中出现了{count}次")
