# 考试抽象基类
'''
类名: BaseExam (ABC)

类属性:
  - passing_rate = 0.6  # 及格率（60%）

实例属性:
  - subject_name: str   # 学科名称
  - max_score: float    # 满分值
  - student_name: str   # 学生姓名
  - __score: float      # 私有成绩，默认0

方法:
  - __init__(subject_name, max_score, student_name)
  - get_score() → float
  - input_score(score)                    # 录入成绩，超出满分抛异常
  - set_passing_rate(cls, rate)           # 类方法
  - check_student_name(name) → bool       # 静态方法
  - get_grade(score) → str                # 抽象方法（子类必须实现等级规则）
  - calc_weighted_score(weight) → float   # 计算加权分（如期末占70%）
  - print_report_card()                   # 通用成绩单打印
'''
import sys
import os
# 添加项目根目录到路径，使直接运行此文件时能找到 grade_utils
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abc import ABC, abstractmethod
from grade_utils import check_valid_score, calc_percentage, save_record


class BaseExam(ABC):
    passing_rate = 0.6  # 及格率（60%）

    def __init__(self, subject_name: str, max_score: float, student_name: str):
        self.subject_name = subject_name   # 学科名称
        self.max_score = max_score         # 满分值
        self.student_name = student_name   # 学生姓名
        self.__score = 0.0                 # 私有成绩，默认0

    def get_score(self) -> float:
        return self.__score

    def input_score(self, score):
        check_valid_score(score, self.max_score)
        self.__score = score

    @classmethod
    def set_passing_rate(cls, rate):
        if not 0 <= rate <= 1:
            raise ValueError("及格率必须在 0-1 之间")
        cls.passing_rate = rate

    @staticmethod
    def check_student_name(name) -> bool:
        return isinstance(name, str) and len(name.strip()) > 0

    @abstractmethod
    def get_grade(self, score) -> str:
        raise NotImplementedError("子类必须实现predict方法")

    def calc_weighted_score(self, weight) -> float:
        return self.__score * weight

    def print_report_card(self):
        """通用成绩单打印"""
        percentage = calc_percentage(self.__score, self.max_score)
        grade = self.get_grade(self.__score)
        print("+" + "-" * 30 + "+")
        print(f"| 学生姓名：{self.student_name}")
        print(f"| 学科：{self.subject_name}")
        print(f"| 成绩：{self.__score}/{self.max_score}")
        print(f"| 得分率：{percentage:.2f}%")
        print(f"| 等级：{grade}")
        print("+" + "-" * 30 + "+")


    # md文件里面的测试要求说要保存记录，但是类的结构里面实际没有这个功能，所以还得自己添加
    def save_to_file(self):
        """将本次成绩记录持久化保存"""
        record_info = f"{self.student_name},{self.subject_name},{self.get_score()},{self.get_grade(self.get_score())}"
        save_record(record_info)
