# main.py - 奶茶门店系统程序入口
# 整合所有模块：工具函数、with文件/线程锁、面向对象、方法重写多态
#
# ==================== __init__.py 引入方法说明 ====================
# goods/__init__.py 是空白文件（无代码），仅用于标记 goods 文件夹为 Python 包
# 此时引入包内模块的完整写法为：from goods.模块名 import 类名
# 例如：from goods.base_drink import BaseDrink
#       from goods.fruit_tea import FruitTea
#
# 进阶写法：在 goods/__init__.py 中预导入所有类（当前项目采用此方式）
# 此时可简写为：from goods import BaseDrink, FruitTea, MilkCapTea, Coffee
#
# 如果 goods 文件夹没有 __init__.py 文件，会报 ModuleNotFoundError
# 解决方案：在 goods 文件夹新建空白 __init__.py 文件即可

# ==================== 导入规范（三段式，空行分隔） ====================

# 1. Python内置库
import threading
from abc import ABC, abstractmethod

# 2. 第三方库（本项目暂未使用）
# import requests

# 3. 自定义包/模块
from goods import BaseDrink, FruitTea, MilkCapTea, Coffee
from shop_tools import (
    check_positive,
    calc_total_price,
    save_order_with_with,
    read_all_orders,
    multi_thread_sell,
    get_cheap_drinks,
    order_record_generator
)


def main():
    """程序主入口"""
    print("===== 奶茶门店管理系统 =====")

    # ==================== 模块0：基础计价测试 ====================
    print("\n--- 基础计价 ---")
    res = calc_total_price(12, 3)
    print(f"12元奶茶买3杯总价：{res}元")

    # ==================== 模块1：with文件操作测试 ====================
    print("\n--- 订单保存测试 ---")
    save_order_with_with("芝士葡萄 x2 总价27")
    print("\n全部订单记录：")
    print(read_all_orders())

    # ==================== 模块1：with线程锁多线程测试 ====================
    print("\n--- 多线程售卖测试 ---")
    multi_thread_sell()

    # ==================== 模块2+3：面向对象+方法重写测试 ====================
    print("\n===== 奶茶门店收银系统 =====")

    # 设置全场折扣为9折
    BaseDrink.set_shop_discount(0.9)

    # 静态方法调用
    print("\n名称校验：", BaseDrink.check_drink_name("珍珠奶茶"))

    # --- 果茶测试 ---
    print("\n--- 果茶测试 ---")
    mango = FruitTea("杨枝甘露", 16)
    print(f"饮品名称：{mango.name}")
    print(f"饮品类型：{mango.type}")
    print(f"当前库存：{mango.get_stock()}")
    mango.sell(2)  # 扣库存
    mango.print_ticket(2)  # 打印专属小票
    mango_price = mango.get_final_price(2)
    print(f"2杯杨枝甘露总价：{mango_price}元")
    save_order_with_with(f"杨枝甘露 x2 总价{mango_price}")

    # --- 奶盖茶测试 ---
    print("\n--- 奶盖茶测试 ---")
    grape = MilkCapTea("芝士葡萄", 15)
    print(f"饮品名称：{grape.name}")
    grape.sell(2)
    print(f"2杯芝士葡萄总价：{grape.get_final_price(2)}元")
    print(f"奶盖单杯成本：{grape.get_milk_cap_cost()}元")
    save_order_with_with(f"芝士葡萄 x2 总价{grape.get_final_price(2)}")

    # --- 咖啡测试 ---
    print("\n--- 咖啡测试 ---")
    american = Coffee("美式咖啡", 10)
    print(f"饮品名称：{american.name}")
    american.sell(3)
    print(f"3杯美式总价：{american.get_final_price(3)}元")
    save_order_with_with(f"美式咖啡 x3 总价{american.get_final_price(3)}")

    # --- 列表推导式测试 ---
    print("\n--- 低价饮品筛选 ---")
    menu = {"珍珠奶茶": 12, "杨枝甘露": 16, "芝士葡萄": 15, "美式咖啡": 10}
    cheap = get_cheap_drinks(menu, 14)
    print(f"低于14元的饮品：{cheap}")

    # --- 生成器测试 ---
    print("\n--- 订单生成器 ---")
    orders = [("珍珠奶茶", 2, 21.6), ("杨枝甘露", 1, 14.4)]
    for record in order_record_generator(orders):
        print(record)


def checkout_batch(drink_list: list):
    """
    批量结算函数：演示多态
    :param drink_list: 饮品实例列表，每个对象调用各自的get_final_price
    """
    print("\n===== 批量结算 =====")
    total = 0
    for drink in drink_list:
        price = drink.get_final_price(1)
        print(f"{drink.name}（{drink.type if hasattr(drink, 'type') else '咖啡'}）：{price}元")
        total += price
    print(f"合计：{round(total, 2)}元")


if __name__ == "__main__":
    main()

    # 批量结算多态测试
    drinks = [
        FruitTea("杨枝甘露", 16),
        MilkCapTea("芝士葡萄", 15),
        Coffee("拿铁", 18)
    ]
    checkout_batch(drinks)
