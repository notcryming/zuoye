'''
【程序9】
题目：一个数如果恰好等于它的因子之和，这个数就称为 "完数 "。例如6=1＋2＋3.编程找出1000以内的所有完数。
'''
lst = []
for i in range(2,1000):
    list1 = []
    for j in range(1, int(i/2)+1):
        if i % j == 0:
            list1.append(j)
    if i == sum(list1):
        lst.append(i)
print(lst)
