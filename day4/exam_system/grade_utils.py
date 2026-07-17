# 这是一个通用工具函数模块
'''
1. check_valid_score(score, max_score)  → 校验成绩是否在合法范围（0~满分）
2. calc_percentage(score, max_score)    → 计算得分率 = 分数/满分 × 100%
3. save_record(record_info)             → 使用 with 追加写入 exam_records.txt
4. read_all_records()                   → 使用 with 读取全部成绩记录
5. get_excellent_students(score_dict, threshold)  → 列表推导式筛选达到优秀的学生
6. report_card_generator(student_list)  → 生成器，yield 格式化成绩单字符串
7. input_score_thread_safe(student_name, subject, score)  → 线程锁安全录入成绩
8. multi_thread_input_test()            → 创建2个线程并发录入测试
'''
import threading

# 全局通用变量
student_records = {}   # 全局共享成绩字典，格式：{"张三": {"语文": 0, "数学": 0}}
record_lock = threading.Lock()


def check_valid_score(score, max_score):
    """校验成绩是否在合法范围（0~满分），非法则抛 ValueError"""
    if not isinstance(score, (int, float)):
        raise TypeError(f"分数必须为数字类型，当前类型：{type(score).__name__}")
    if not 0 <= score <= max_score:
        raise ValueError(f"分数必须在 0-{max_score} 之间！当前分数：{score}")
    return True


def calc_percentage(score, max_score):
    return score / max_score * 100


def save_record(record_info):
    with open("exam_records.txt", "a", encoding="utf-8") as f:
        f.write(record_info + "\n")
    print("成绩保存成功，文件已自动关闭")


def read_all_records():
    with open("exam_records.txt", "r", encoding="utf-8") as f:
        content = f.readlines()
    return content


def get_excellent_students(score_dict, threshold):
    return [name for name, score in score_dict.items() if score >= threshold]


def report_card_generator(student_list):
    for student in student_list:
        name = student.get("name", "未知")
        subject = student.get("subject", "未知学科")
        score = student.get("score", 0)
        grade = student.get("grade", "未评定")
        report = (
            "+" + "-" * 30 + "+\n"
            f"| 学生姓名：{name}\n"
            f"| 学科：{subject}\n"
            f"| 成绩：{score}\n"
            f"| 等级：{grade}\n"
            "+" + "-" * 30 + "+"
        )
        yield report


def input_score_thread_safe(student_name, subject, score):
    """线程锁安全录入成绩，更新全局字典并持久化"""
    with record_lock:
        if student_name not in student_records:
            student_records[student_name] = {}
        student_records[student_name][subject] = score
        # 持久化保存
        record_info = f"{student_name},{subject},{score}"
        save_record(record_info)
        print(f"[线程 {threading.current_thread().name}] 录入完成：{student_name} - {subject} = {score}")


def multi_thread_input_test():
    """创建2个线程并发录入测试"""
    print("\n=== 多线程并发录入测试 ===")
    t1 = threading.Thread(
        target=input_score_thread_safe,
        args=("张三", "语文", 138),
        name="Teacher-A"
    )
    t2 = threading.Thread(
        target=input_score_thread_safe,
        args=("李四", "数学", 145),
        name="Teacher-B"
    )
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print("多线程录入结束，当前共享字典：", student_records)
