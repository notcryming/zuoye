"""
with管理线程锁
"""

import threading

# 【重点补充】全局共享库存字典，所有线程共用，必须提前定义
global_stock = {"珍珠奶茶": 50, "杨枝甘露": 30}
# 创建互斥锁对象
lock = threading.Lock()

# # 传统手动加锁写法，必须搭配try-finally防止死锁
# lock.acquire()
# try:
#     global_stock["珍珠奶茶"] -= 1
# finally:
#     lock.release()

# with简化写法：自动acquire加锁，代码结束自动release释放锁
with lock:
    global_stock["珍珠奶茶"] -= 1
