import sys
import os
# 添加项目根目录到路径，使直接运行此文件时能找到 shop_tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abc import ABC, abstractmethod
from shop_tools import check_positive

class BaseDrink(ABC):
    '''
    基础饮品类
    '''

    shop_discount = 1.0

    def __init__(self, name:str, price:float):
        '''
        初始化饮品
        :param name:名称
        :param prcie:单价
        '''
        self.name = name
        self.price = price
        self.__stock = 50

    def get_stock(self) -> int:
        '''
        获取当前饮品库存
        '''
        return self.__stock

    def sell(self, num:int):
        '''
        售卖饮品
        :param num:饮品
        '''
        if not check_positive(num) or num > self.__stock:
            raise ValueError("数量非法或者库存不足")
        self.__stock -= num
        return (f"售出{num}杯{self.name}，剩余{self.__stock}杯")

    @classmethod
    def set_shop_discount(cls, discount:float):
        '''
        设置店铺折扣
        :param discount:折扣
        '''
        if 0 < discount <=1:
            cls.shop_discount = discount
            print(f"设置店铺折扣维{discount}")
        else:
            raise ValueError("折扣必须在0到1之间")

    @staticmethod
    def check_drink_name(name: str):
        """
        检查饮品名称是否合法
        :param name: 名称
        """
        if not name or name.isspace():
            raise ValueError("饮品名称不能为空")
        return name

    @abstractmethod
    def get_final_price(self, buy_num: int) -> float:
        """
        计算最终价格
        :param num: 数量
        :return: 最终价格
        """
        pass

    def print_ticket(self, buy_num: int):
        """
        打印订单票
        :param buy_num: 购买数量
        :param final_price: 最终价格
        """
        total = self.get_final_price(buy_num)
        print(f"饮品：{self.name},数量：{buy_num}, 总价：{total}")


if __name__ == "__main__":
    print("===== base_drink.py 模块自测 =====\n")

    # 1. 测试静态方法：名称校验
    print("--- 测试1：静态方法（名称校验）---")
    print(BaseDrink.check_drink_name('珍珠奶茶'))  # True
    # print(f"BaseDrink.check_drink_name('') = {BaseDrink.check_drink_name('')}")  # False
    # print(f"BaseDrink.check_drink_name('  ') = {BaseDrink.check_drink_name('  ')}")  # False

    # 2. 测试类方法：设置折扣
    # print("\n--- 测试2：类方法（全场折扣）---")
    print(f"初始折扣：{BaseDrink.shop_discount}")
    BaseDrink.set_shop_discount(0.9)
    print(f"设置后折扣：{BaseDrink.shop_discount}")

    # # 重置折扣为默认值
    BaseDrink.set_shop_discount(1.0)

    # # 3. 测试抽象类不可实例化
    print("\n--- 测试3：抽象类实例化限制 ---")
    try:
        test = BaseDrink("测试", 10)
    except TypeError as e:
        print(f"抽象类无法实例化：{e}")

    # print("\n===== 测试完成（实例方法测试请运行子类文件） =====")

