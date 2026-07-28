'''
【程序22】
题目：利用递归方法求5!。
1.程序分析：递归公式：fn=fn_1*4!
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

print(JC(5))
