# goods/milk_cap.py - 奶盖茶子类
# 继承BaseDrink，实现奶盖茶专属优惠：购买2杯及以上立减3元
import sys
import os

# 添加项目根目录到路径，使直接运行此文件时能找到 shop_tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goods.base_drink import BaseDrink

class MilkCapTea(BaseDrink):
    def __init__(self, name: str, price: float):
        super().__init__(name, price)
        # 实例属性，__milk_cap_cost
        self.__milk_cap_cost = 7

    def get_milk_cap_cost(self):   # -->获取奶盖的单杯价格
        return self.__milk_cap_cost

    def get_final_price(self, buy_num: int) -> float:
        """计算奶盖茶的最终价格"""
        if buy_num >= 2:
            origin = self.price * buy_num
            final = origin * self.shop_discount - 3
        else:
            origin = self.price * buy_num
            final = origin * self.shop_discount
        print("=====")
        return round(final, 2)    # 保留小数点后两位

# 测试代码
if __name__ == "__main__":
    milk_cap = MilkCapTea("奶盖茶", 5)
    print(milk_cap.get_final_price(2))
