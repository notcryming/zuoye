# 英语学科子类
'''
类名: EnglishExam

等级规则:
  - ≥90优秀，≥75良好，≥60及格，<60不及格

重写方法:
  - print_report_card()  # 打印"听力/阅读/写作分项成绩"标语
'''
from subjects.base_exam import BaseExam


class EnglishExam(BaseExam):
    # 英语学科固定参数
    SUBJECT_NAME = "英语"
    MAX_SCORE = 100

    def __init__(self, student_name: str):
        super().__init__(self.SUBJECT_NAME, self.MAX_SCORE, student_name)
        # 分项成绩：听力/阅读/写作
        self.listening_score = 0.0   # 听力（满分30）
        self.reading_score = 0.0     # 阅读（满分40）
        self.writing_score = 0.0     # 写作（满分30）

    def input_sub_scores(self, listening, reading, writing):
        """录入三项分项成绩（听力/阅读/写作）"""
        check = lambda s, m: (isinstance(s, (int, float)) and 0 <= s <= m)
        if not (check(listening, 30) and check(reading, 40) and check(writing, 30)):
            raise ValueError("分项成绩非法：听力(0-30)、阅读(0-40)、写作(0-30)")
        self.listening_score = listening
        self.reading_score = reading
        self.writing_score = writing
        # 自动汇总总分
        self.input_score(listening + reading + writing)

    def get_grade(self, score) -> str:
        """等级规则：≥90优秀，≥75良好，≥60及格，<60不及格"""
        if score >= 90:
            return "优秀"
        elif score >= 75:
            return "良好"
        elif score >= 60:
            return "及格"
        else:
            return "不及格"

    def print_report_card(self):
        """英语成绩单：打印听力/阅读/写作分项成绩标语"""
        print("+" + "-" * 30 + "+")
        print("| 英语分项成绩单 ")
        print(f"| 学生姓名：{self.student_name}")
        print(f"| 听力分：{self.listening_score}/30")
        print(f"| 阅读分：{self.reading_score}/40")
        print(f"| 写作分：{self.writing_score}/30")
        print(f"| 总成绩：{self.get_score()}/{self.MAX_SCORE}")
        print(f"| 等级：{self.get_grade(self.get_score())}")
        print("+" + "-" * 30 + "+")
