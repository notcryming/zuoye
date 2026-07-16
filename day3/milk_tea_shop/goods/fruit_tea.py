# goods/fruit_tea.py - 果茶子类
# 继承BaseDrink，实现果茶专属优惠：全场折扣基础上额外95折
import sys
import os

# 添加项目根目录到路径，使直接运行此文件时能找到 shop_tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goods.base_drink import BaseDrink

class FruitTea(BaseDrink):
    def __init__(self, name: str, price: float):
        super().__init__(name, price)
        self.type = "水果茶"

    # 重写打印小票方法：显示果茶专属优惠信息
    def print_ticket(self, buy_num: int):
        """
        打印订单票
        :param buy_num: 购买数量
        :param final_price: 最终价格
        """
        total = self.get_final_price(buy_num)
        print(f"饮品：{self.name},数量：{buy_num}, 总价：{total}, 果茶在全场折扣基础上额外95折")

    def get_final_price(self, buy_num: int) -> float:
        """计算果茶的最终价格"""
        origin = self.price * buy_num
        final = origin * self.shop_discount * 0.95
        print("=====")
        return round(final, 2)  # 保留小数点后两位

# 测试代码
if __name__ == "__main__":
    fruit_tea = FruitTea("西瓜茶", 5)
    print(fruit_tea.get_final_price(2))
    print(fruit_tea.print_ticket(2))