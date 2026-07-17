# 学生成绩管理系统 - 主程序入口
# 整合所有模块，按需求文档完成 10 步测试流程
import os
import sys

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from grade_utils import (
    calc_percentage,
    save_record,
    read_all_records,
    get_excellent_students,
    report_card_generator,
    multi_thread_input_test,
)
from subjects import BaseExam, ChineseExam, MathExam, EnglishExam


def test1_percentage():
    """1. 基础得分率计算测试"""
    print("\n" + "=" * 50)
    print("测试1：基础得分率计算")
    print("=" * 50)
    print(f"语文 120/150 得分率：{calc_percentage(120, 150):.2f}%")
    print(f"数学 135/150 得分率：{calc_percentage(135, 150):.2f}%")
    print(f"英语 85/100 得分率：{calc_percentage(85, 100):.2f}%")


def test2_save_and_read():
    """2. 成绩保存与读取测试"""
    print("\n" + "=" * 50)
    print("测试2：成绩保存与读取")
    print("=" * 50)
    save_record("测试学生,语文,100,及格")
    save_record("测试学生,数学,110,及格")
    records = read_all_records()
    print(f"已读取 {len(records)} 条记录")
    for line in records[-2:]:
        print("  ->", line.strip())


def test3_multi_thread():
    """3. 多线程录入测试"""
    print("\n" + "=" * 50)
    print("测试3：多线程并发录入")
    print("=" * 50)
    multi_thread_input_test()


def test4_set_passing_rate():
    """4. 设置及格率为 0.65"""
    print("\n" + "=" * 50)
    print("测试4：设置及格率")
    print("=" * 50)
    print(f"修改前及格率：{BaseExam.passing_rate}")
    BaseExam.set_passing_rate(0.65)
    print(f"修改后及格率：{BaseExam.passing_rate}")


def test5_chinese():
    """5. 语文测试"""
    print("\n" + "=" * 50)
    print("测试5：语文学科")
    print("=" * 50)
    try:
        chinese = ChineseExam("王小明")
        chinese.input_score(138)
        chinese.input_essay_score(55)
        print(f"学生：{chinese.student_name}")
        print(f"成绩：{chinese.get_score()}")
        print(f"作文分：{chinese.essay_score}")
        print(f"等级：{chinese.get_grade(chinese.get_score())}")
        chinese.print_report_card()
        chinese.save_to_file()
    except (ValueError, TypeError) as e:
        print(f"语文录入异常：{e}")


def test6_math():
    """6. 数学测试"""
    print("\n" + "=" * 50)
    print("测试6：数学学科")
    print("=" * 50)
    try:
        math = MathExam("李大壮")
        math.input_score(142)
        math.set_bonus_points(5)
        print(f"学生：{math.student_name}")
        print(f"成绩：{math.get_score()}")
        print(f"附加分：{math.get_bonus_points()}")
        print(f"加权分（权重0.7）：{math.calc_weighted_score(0.7):.2f}")
        print(f"等级：{math.get_grade(math.get_score())}")
        math.print_report_card()
        math.save_to_file()
    except (ValueError, TypeError) as e:
        print(f"数学录入异常：{e}")


def test7_english():
    """7. 英语测试"""
    print("\n" + "=" * 50)
    print("测试7：英语学科")
    print("=" * 50)
    try:
        english = EnglishExam("张美丽")
        english.input_sub_scores(listening=28, reading=35, writing=30)
        print(f"学生：{english.student_name}")
        print(f"总成绩：{english.get_score()}")
        print(f"等级：{english.get_grade(english.get_score())}")
        english.print_report_card()
        english.save_to_file()
    except (ValueError, TypeError) as e:
        print(f"英语录入异常：{e}")


def test8_excellent_filter():
    """8. 优秀学生筛选测试"""
    print("\n" + "=" * 50)
    print("测试8：优秀学生筛选（列表推导式）")
    print("=" * 50)
    score_dict = {
        "张三": 92, "李四": 85, "王五": 95,
        "赵六": 78, "钱七": 90, "孙八": 88,
    }
    threshold = 90
    excellent = get_excellent_students(score_dict, threshold)
    print(f"全班成绩：{score_dict}")
    print(f"优秀线：{threshold}分")
    print(f"优秀学生：{excellent}")


def test9_report_card_generator():
    """9. 成绩单生成器测试"""
    print("\n" + "=" * 50)
    print("测试9：成绩单生成器（yield 惰性生成）")
    print("=" * 50)
    students = [
        {"name": "张三", "subject": "语文", "score": 138, "grade": "优秀"},
        {"name": "李四", "subject": "数学", "score": 142, "grade": "优秀"},
        {"name": "王五", "subject": "英语", "score": 93, "grade": "优秀"},
    ]
    gen = report_card_generator(students)
    for idx, card in enumerate(gen, 1):
        print(f"\n--- 第 {idx} 份成绩单 ---")
        print(card)


def test10_polymorphism():
    """10. 批量统计多态测试"""
    print("\n" + "=" * 50)
    print("测试10：批量统计多态（3门学科各1份答卷）")
    print("=" * 50)
    exams = [
        ChineseExam("学生A"),
        MathExam("学生B"),
        EnglishExam("学生C"),
    ]
    exams[0].input_score(130)
    exams[1].input_score(125)
    exams[1].set_bonus_points(3)
    exams[2].input_sub_scores(25, 30, 28)

    weight = 0.7
    print(f"加权权重：{weight}")
    total_weighted = 0
    for exam in exams:
        weighted = exam.calc_weighted_score(weight)
        total_weighted += weighted
        print(f"{exam.student_name} - {exam.subject_name}: 卷面 {exam.get_score()}, 加权分 {weighted:.2f}")
    print(f"三门学科加权总分：{total_weighted:.2f}")
    print(f"三门学科加权平均分：{total_weighted / len(exams):.2f}")


def main():
    print("=" * 50)
    print("   学生成绩管理系统 V1.0   ")
    print("=" * 50)

    # 清空旧记录文件，便于观察本次运行结果
    if os.path.exists("exam_records.txt"):
        os.remove("exam_records.txt")

    try:
        test1_percentage()
        test2_save_and_read()
        test3_multi_thread()
        test4_set_passing_rate()
        test5_chinese()
        test6_math()
        test7_english()
        test8_excellent_filter()
        test9_report_card_generator()
        test10_polymorphism()
    except ValueError as e:
        print(f"[捕获 ValueError] {e}")
    except TypeError as e:
        print(f"[捕获 TypeError] {e}")
    except Exception as e:
        print(f"[捕获未知异常] {type(e).__name__}: {e}")

    print("\n" + "=" * 50)
    print("   所有测试流程执行完毕   ")
    print("=" * 50)


if __name__ == "__main__":
    main()
