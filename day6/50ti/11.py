'''
【程序11】
题目：有数字1、2、3、4，能组成多少个互不相同且无重复数字的三位数？都是多少？
1.程序分析：可填在百位、十位、个位的数字都是1、2、3、4。组成所有的排列后再去掉不满足条件的排列。
'''
def number(a, b, c):
    return a*100+b*10+c

def C43(a, b, c, d):
    return [(a, b, c), (a, b, d), (a, c, d), (b, c, d)]

def A33(a, b, c):
    lst = []
    lst.append(number(a, b, c))
    lst.append(number(a, c, b))
    lst.append(number(b, a, c))
    lst.append(number(b, c, a))
    lst.append(number(c, a, b))
    lst.append(number(c, b, a))
    return lst

lst = []
time = 0
for a, b, c in C43(1,2,3,4):
    lst += A33(a, b, c)
print(f"组成{len(lst)}个互不相同且无重复数字的三位数")
for i in lst:
    print(i, end=" ")
    time += 1
    if time % 10 == 0:
        print("\n")

