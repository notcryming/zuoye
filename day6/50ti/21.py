'''
【程序21】
题目：求1+2!+3!+...+20!的和
1.程序分析：此程序只是把累加变成了累乘。
'''
jc = {1:1}
def JC(n:int):
    if n <= 0:
        raise ValueError("项数必须大于0！")
    if n in jc:
        return jc[n]
    res = JC(n-1)*n
    jc[n] = res
    return res

total = 0
for i in range(1, 21):
    total += JC(i)
print(total)

