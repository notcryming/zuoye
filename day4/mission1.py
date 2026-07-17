# 子任务一
import asyncio
import time

async def greet(name, delay):
    await asyncio.sleep(delay)
    print(f"Hello,{name}!")
    return name

async def main():
    start = time.time()
    result = await asyncio.gather(
        greet("Alice", 1),
        greet("Bob", 2),
        greet("Carol", 3)
    )
    end = time.time()
    print("返回的结果列表为：", end="")
    print(list(result))
    print(f"打印总耗时：{end-start}s")

asyncio.run(main())
