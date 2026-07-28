'''
【程序18】
题目：两个乒乓球队进行比赛，各出三人。
甲队为a,b,c三人，乙队为x,y,z三人。已抽签决定比赛名单。有人向队员打听比赛的名单。
a说他不和x比，c说他不和x,z比，请编程序找出三队赛手的名单。
'''
team_b = ['x', 'y', 'z']
for a in team_b:
    for b in team_b:
        for c in team_b:
            if a != b and b != c and a != c:
                if a != 'x' and c != 'x' and c != 'z':
                    print(f"a 对战 {a}")
                    print(f"b 对战 {b}")
                    print(f"c 对战 {c}")
'''
import itertools

# 生成x,y,z的所有不重复排列，分别分配给a,b,c
for a_op, b_op, c_op in itertools.permutations(['x','y','z']):
    if a_op != 'x' and c_op not in ('x','z'):
        print(f"a -> {a_op}")
        print(f"b -> {b_op}")
        print(f"c -> {c_op}")
'''


