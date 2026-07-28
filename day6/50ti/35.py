'''
【程序35】
题目：输入数组，最大的与第一个元素交换，最小的与最后一个元素交换，输出数组。
'''
print("开始输入数组(输入字母停止)：")
lst = []
while 1:
    try:
        a = int(input())
        lst.append(a)
    except Exception as e:
        print("结束输入")
        break
print(lst)
# 枚举生成序号和元素组合而成的元组，拼合返回迭代器类型，key是max的参数，x:x[1]取元组中第二个数比大小
idx1, ma = max(enumerate(lst), key=lambda x: x[1])
lst[0],lst[idx1] = lst[idx1],lst[0]
idx2, mi = min(enumerate(lst), key=lambda x: x[1])
lst[-1],lst[idx2] = lst[idx2],lst[-1]
print(lst)

