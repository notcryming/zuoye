'''
【程序30】
题目：有一个已经排好序的数组。现输入一个数，要求按原来的规律将它插入数组中。
1.程序分析：首先判断此数是否大于最后一个数，然后再考虑插入中间的数的情况，
插入后此元素之后的数，依次后移一个位置。
'''
lst = [1,3,6,8,11,15,19,22,30]
a = int(input())
print(lst)
if a > lst[-1]:
    lst.insert(-1, a)
else:
    for i in range(0, len(lst)):
        if lst[i] < a < lst[i+1]:
            lst.insert(i+1, a)
print(lst)
