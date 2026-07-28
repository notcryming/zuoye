'''
【程序47】
题目：读取7个数（1—50）的整数值，每读取一个值，程序打印出该值个数的＊。
'''
for i in range(7):
    while True:
        n = int(input(f"请输入第{i+1}个数(1-50): "))
        if 1 <= n <= 50:
            break
        print("请输入1-50之间的整数!")
    print('*' * n)