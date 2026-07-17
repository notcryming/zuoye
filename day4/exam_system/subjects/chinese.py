# 语文学科子类
'''
类名: ChineseExam

独有属性:
  - essay_score: float  # 作文分（满分60）

等级规则:
  - ≥135优秀，≥120良好，≥90及格，<90不及格
'''
from subjects.base_exam import BaseExam
from grade_utils import check_valid_score


class ChineseExam(BaseExam):
    # 语文学科固定参数
    SUBJECT_NAME = "语文"
    MAX_SCORE = 150
    ESSAY_MAX_SCORE = 60  # 作文分满分60

    def __init__(self, student_name: str):
        super().__init__(self.SUBJECT_NAME, self.MAX_SCORE, student_name)
        self.essay_score = 0.0  # 作文分，默认0

    def input_essay_score(self, essay_score):
        """录入作文分，校验是否在 0-60 之间"""
        check_valid_score(essay_score, self.ESSAY_MAX_SCORE)
        self.essay_score = essay_score

    def get_grade(self, score) -> str:
        """等级规则：≥135优秀，≥120良好，≥90及格，<90不及格"""
        if score >= 135:
            return "优秀"
        elif score >= 120:
            return "良好"
        elif score >= 90:
            return "及格"
        else:
            return "不及格"

    def print_report_card(self):
        """语文成绩单（额外展示作文分）"""
        super().print_report_card()
        print(f"| 作文分：{self.essay_score}/{self.ESSAY_MAX_SCORE}")
        print("+" + "-" * 30 + "+")
