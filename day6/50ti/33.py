'''
【程序33】
题目：打印出杨辉三角形（要求打印出10行如下图）
1.程序分析：
           1
         1   1
       1   2   1
     1   3   3   1
   1   4   6   4   1
1   5   10   10   5   1
'''
n = 10
row = []
for i in range(n):
    # 扩容，每行都只多了一个数，且最后一个数刚好是1
    row.append(1)
    for j in range(i-1, 0, -1):
        row[j] = row[j] + row[j-1]
    # 打印
    print(" " * 2*(n - i - 1), end="")
    for val in row:
        print(val, end="  ")
    print()


