# 咖啡子类
# 继承BaseDrink，实现咖啡专属优惠：88折
import sys
import os

# 添加项目根目录到路径，使直接运行此文件时能找到 shop_tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from goods.base_drink import BaseDrink


class Coffee(BaseDrink):
    def __init__(self, name: str, price: float):
        super().__init__(name, price)

    def get_final_price(self, buy_num: int) -> float:
        """计算咖啡的最终价格"""
        origin = self.price * buy_num
        final = origin * self.shop_discount * 0.88
        print("=====")
        return round(final, 2)    # 保留小数点后两位


if __name__ == "__main__":
    coffee = Coffee("美式咖啡", 5)
    print(coffee.get_final_price(2))
