'''
【程序50】
题目：有五个学生，每个学生有3门课的成绩，从键盘输入以上数据（包括学生号，姓名，三门课成绩），计算出平均成绩，将原有的数据和计算出的平均分数存放在磁盘文件 "stud" 中。
'''
students = []
for i in range(5):
    print(f"\n请输入第{i+1}个学生的信息:")
    student_id = input("学生号: ")
    name = input("姓名: ")
    score1 = float(input("课程1成绩: "))
    score2 = float(input("课程2成绩: "))
    score3 = float(input("课程3成绩: "))
    avg = (score1 + score2 + score3) / 3
    students.append({
        'id': student_id,
        'name': name,
        'scores': [score1, score2, score3],
        'avg': avg
    })

with open('stud', 'w') as f:
    for s in students:
        f.write(f"{s['id']} {s['name']} {s['scores'][0]} {s['scores'][1]} {s['scores'][2]} {s['avg']:.2f}\n")

print("\n数据已保存到文件 'stud' 中")