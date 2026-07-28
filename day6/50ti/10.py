'''
【程序10】
题目：一球从100米高度自由落下，每次落地后反跳回原高度的一半；再落下，求它在第10次落地时，共经过多少米？第10次反弹多高？
'''
def term(i):
    if i == 1:
        return 100
    else:
        return 100 / 2 ** (i -2)

def back(i):
    return 100 / 2 ** i

lst = []
for i in range(1, 11):
    lst.append(term(i))
print(f"第10次落地时共经过{sum(lst)}m")
print(f"第10次落地后将起跳{back(10)}m")


