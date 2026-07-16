import threading
from demo_01 import global_stock
# 全局共享库存（全局变量，所有线程都会用，必须提前定义）

stock_lock = threading.Lock()
global_stock =  {"珍珠奶茶": 50, "杨枝甘露": 30, "芝士葡萄": 40, "美式咖啡": 60}
# 此处定义是假设有这么多用来测试

def check_positive(num: float) -> bool:
    """
    校验数字是否大于0
    :param num: 价格、库存、数量等数字
    :return: 合法大于数返回True，否则返回False
    :raises TypeError: 输入非数字类型时抛出异常
    """
    if not isinstance(num, (int, float)):
        raise TypeError("参数必须传入数字（int/float）")
    return num > 0


def calc_total_price(price, num):
    return price * num





# 保存订单信息
def save_order_with_with(order_info:str):
    with open("order.txt", "a", encoding="utf-8") as f:
        f.write(order_info + "\n")
    print("订单保存成功，文件已自动关闭")

# 读取订单信息
def read_all_orders():
    '''
    读取所有订单
    '''
    with open("order.txt", "r", encoding="utf-8") as f:
        content = f.readlines()
    return content

# 获取最便宜的饮料
def get_cheap_drinks(drink_dict:list, limit:int) -> list:
    '''
    获取价格低于limit的饮料
    '''
    if not isinstance(drink_dict, dict):
        raise TypeError("drink_dict必须是字典类型")
    cheap_data = {name : p for name, p in drink_dict.items() if p <= limit}
    return list(cheap_data.keys())

# 点单生成器
def order_record_generator(order_list:list):
    for order in order_list:
        yield f"饮品：{order[0]}，数量：{order[1]}，总价：{order[2]}"


# ==================== 多线程库存管理 ====================
def sell_drink_thread_safe(drink_name: str, sell_num: int):
    global global_stock
    try:
        global_stock[drink_name]
    except KeyError:
        print(f"没有名字为{drink_name}的饮品！")
        return
    with stock_lock:
        if global_stock[drink_name] >= sell_num:
            global_stock[drink_name] = global_stock[drink_name] - sell_num
            info = f"{drink_name} 售出{sell_num}杯，剩余库存{global_stock[drink_name]}"
            save_order_with_with(info)
            print(info)
        else:
            print(f"{drink_name}饮品库存不足！")

# 需要将剩余库存信息保存到order.txt文件中

# def multi_thread_sell(list1):
#     thread = []
#     for drink_name, sell_num in list1:
#         t = threading.Thread(target=sell_drink_thread_safe, args=(drink_name, sell_num))
#         t.start()
#         thread.append(t)
#     for t in thread:
#         t.join()

def multi_thread_sell():
    """多线程并发售卖测试函数"""
    t1 = threading.Thread(target=sell_drink_thread_safe, args=("珍珠奶茶", 5))
    t2 = threading.Thread(target=sell_drink_thread_safe, args=("珍珠奶茶", 3))
    t1.start()
    t2.start()
    t1.join()
    t2.join()

# ==================== 模块测试代码 ====================
# 以下代码仅在直接运行 shop_tools.py 时执行（python shop_tools.py）
# 被其他文件导入时不会执行

if __name__ == "__main__":
    # save_order_with_with("珍珠奶茶,2,24")
    # save_order_with_with("杨枝甘露,1,16")
    # orders = read_all_orders()
    # print(orders)

    print(get_cheap_drinks({"珍珠奶茶":12, "杨枝甘露":16, "芝士葡萄":15, "美式咖啡":10}, 14))

    # 3.测试生成器
    for record in order_record_generator([("珍珠奶茶", 2, 24), ("杨枝甘露", 1, 16)]):
        print(record)
        # order_record_generator([("珍珠奶茶", 2, 24), ("杨枝甘露", 1, 16)])

    # 6. 测试线程锁
    print("\n--- 测试6：多线程安全售卖 ---")
    print(f"售卖前珍珠奶茶库存：{global_stock['珍珠奶茶']}")
    # multi_thread_sell([("珍珠奶茶", 20), ("珍珠奶茶", 40), ("西瓜椰椰", 10)])
    multi_thread_sell()
    print(f"售卖后珍珠奶茶库存：{global_stock['珍珠奶茶']}")