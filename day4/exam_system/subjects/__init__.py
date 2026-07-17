# subjects 包：统一预导入所有学科类
# goods/__init__.py
# 包标识文件：标记 goods 文件夹为 Python 包，使外部可通过 from goods.xxx 导入
# 此文件可为空白，此处使用进阶简化导入写法，预导入所有饮品类
# 外部可直接 from subjects import BaseExam, ChineseExam, MathExam, EnglishExam
from subjects.base_exam import BaseExam
from subjects.chinese import ChineseExam
from subjects.math import MathExam
from subjects.english import EnglishExam

__all__ = ["BaseExam", "ChineseExam", "MathExam", "EnglishExam"]
