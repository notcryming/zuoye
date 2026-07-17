# 数学学科子类
'''
类名: MathExam

私有属性:
  - __bonus_points = 0  # 附加分

配套方法:
  - get_bonus_points()  # getter
  - set_bonus_points(points)  # setter

等级规则:
  - ≥140优秀，≥120良好，≥90及格，<90不及格

重写方法:
  - calc_weighted_score(weight)  # 数学加权分计算包含附加分
'''
from subjects.base_exam import BaseExam


class MathExam(BaseExam):
    # 数学学科固定参数
    SUBJECT_NAME = "数学"
    MAX_SCORE = 150

    def __init__(self, student_name: str):
        super().__init__(self.SUBJECT_NAME, self.MAX_SCORE, student_name)
        self.__bonus_points = 0  # 附加分，默认0

    def get_bonus_points(self) -> float:
        return self.__bonus_points

    def set_bonus_points(self, points):
        if not isinstance(points, (int, float)):
            raise TypeError("附加分必须为数字")
        if points < 0:
            raise ValueError("附加分不能为负数")
        self.__bonus_points = points

    def get_grade(self, score) -> str:
        """等级规则：≥140优秀，≥120良好，≥90及格，<90不及格"""
        if score >= 140:
            return "优秀"
        elif score >= 120:
            return "良好"
        elif score >= 90:
            return "及格"
        else:
            return "不及格"

    def calc_weighted_score(self, weight) -> float:
        return (self.get_score() + self.__bonus_points) * weight

    def print_report_card(self):
        super().print_report_card()
        print(f"| 附加分：{self.__bonus_points}")
        print(f"| 加权分（权重0.7）：{self.calc_weighted_score(0.7):.2f}")
        print("+" + "-" * 30 + "+")
