'''
【程序14】
题目：输入某年某月某日，判断这一天是这一年的第几天？
1.程序分析：以3月5日为例，应该先把前两个月的加起来，然后再加上5天即本年的第几天，特殊情况，闰年且输入月份大于3时需考虑多加一天。
'''
day = {1:31, 2:28, 3:31, 4:30, 5:31, 6:30, 7:31, 8:31, 9:30, 10:31, 11:30, 12:31}
days = 0
print("请输入x年x月x日(用空格分割)：", end="")
y, m, d = map(int, input().split())
'''
python的case匹配到一个自动停止了
match m:
    case 12:days += day[11];m -= 1
    case 11:days += day[10];m -= 1
    case 10:days += day[9];m -= 1
    case 9:days += day[8];m -= 1
    case 8:days += day[7];m -= 1
    case 7:days += day[6];m -= 1
    case 6:days += day[5];m -= 1
    case 5:days += day[4];m -= 1
    case 4:days += day[3];m -= 1
    case 3:
        if y%4==0:
            days = days + day[2] + 1
            m -= 1
        else:
            days += day[2]
            m -= 1
    case 2:days += day[1];m -= 1
'''
for month in range(1,m):
    days += day[month]
if m > 3 and y % 4 == 0:
    days +=1
days += d
print(f"{y}年{m}月{d}日是这一年的第{days}天")
