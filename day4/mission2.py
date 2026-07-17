# 子任务二
import asyncio
from datetime import datetime
import time
import threading

def sml_tl(data):
    # print("正在推理......")
    time.sleep(1)
    return data

async def sml_yb(data):
    # print("异步正在推理......")
    await asyncio.sleep(1)
    return data

def run_serial(list1):
    start = datetime.now()
    for data in list1:
        sml_tl(data)
    end = datetime.now()
    return (end - start).total_seconds()

def run_concurrent(list1):
    start = datetime.now()
    thread = []
    for data in list1:
        t = threading.Thread(target=sml_tl, args=(data))
        t.start()
        thread.append(t)
    for t in thread:
        t.join()
    end = datetime.now()
    return (end - start).total_seconds()

async def yibu(list1):
    start = datetime.now()
    tasks = [sml_yb(data) for data in list1]
    await asyncio.gather(*tasks)   # *解包列表，传入每一个元素
    end = datetime.now()
    return (end - start).total_seconds()

list1 = ["A", "B", "C", "D", "E"]
cost1 = run_serial(list1)
cost2 = run_concurrent(list1)
cost3 = asyncio.run(yibu(list1))
print(f"串行总耗时{cost1:.2f}s")
print(f"并行（多线程）总耗时{cost2:.2f}s")
print(f"异步总耗时{cost3:.2f}s")
