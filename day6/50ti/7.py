'''
【程序7】
题目：输入一行字符，分别统计出其中英文字母、空格、数字和其它字符的个数。
1.程序分析：利用while语句,条件为输入的字符不为 '\n '.
'''
print("请输入一串字符：", end="")
letter = space = digit = other = 0
string = input()
for iter in string:
    asc = ord(iter)
    # 大写字母 A-Z:65~90  小写a-z:97~122
    if (65 <= asc <= 90) or (97 <= asc <= 122):
        letter += 1
    # 空格ASCII码是32
    elif asc == 32:
        space += 1
    # 数字 0-9:48~57
    elif 48 <= asc <= 57:
        digit += 1
    else:
        other += 1
print(f"英文字母：{letter}\n空格：{space}\n数字：{digit}\n其他字符：{other}")

