'''
【程序28】
题目：对10个数进行排序
1.程序分析：可以利用选择法，即从后9个比较过程中，选择一个最小的与第一个元素交换，
下次类推，即用第二个元素与后8个进行比较，并进行交换。
'''
lst = list(map(int, input().split()))
for i in range(0, len(lst)-1):
    for j in range(i+1, len(lst)):
        if lst[i] > lst[j]:
            lst[i],lst[j] = lst[j],lst[i]
print(lst)

