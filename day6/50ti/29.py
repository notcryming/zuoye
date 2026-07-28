'''
【程序29】
题目：求一个3*3矩阵对角线元素之和
1.程序分析：利用双重for循环控制输入二维数组，再将a累加后输出。
'''
lst = list(list(0 for x in range(0,3)) for x in range(0,3))
for i in range(0, 3):
    print(f"请输入矩阵第{i+1}行数字(用空格分隔):")
    lst[i][0],lst[i][1],lst[i][2] = map(int, input().split())
print(f"主对角线之和为：{lst[0][0]+lst[1][1]+lst[2][2]}")
print(f"副对角线之和为：{lst[0][2]+lst[1][1]+lst[2][0]}")
