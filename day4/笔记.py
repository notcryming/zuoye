class Logger():
    def __int__(self, level="INFO"):
        self.level =level

    def __call__(self, func):
        def wrapper(*args, **kwargs):
            print(f"[{self.level}]调用函数")

def log_record(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        res = func(*args, **kwargs)
        cost = time.time() - start
        print(f"调用{func.__name__}，耗时{cost:.2f}s")
        return res
    return wrapper

@log_record
def calc_damage(base):
    return base * 1.5

# 类装饰器实现缓存管理
class CacheDecorator:
    def __init__(self, func):
        self.func = func
        self._cache = {}

    def __call__(self, *args):
        if args in self._cache:
            return self._cache[args]
        res = self.func(*args)
        self._cache[args] = res
        return res

    def clear(self):
        self._cache.clear()
        print("缓存已清空")

    #新增获取缓存的方法
    def get_cache(self):
        return self._cache

@CacheDecorator
def big_calc(a,b):
    print("复杂计算中...")
    return a**b

@CacheDecorator
def add(a,b):
    return a + b

print(big_calc(3,2))
print(big_calc.get_cache())
print(add(3,2))
print(add.get_cache())
big_calc.clear()
print(big_calc.get_cache())
print(add.get_cache())

class CallCounter:
    def __init__(self, func):
        self.__count = 0
        self.func = func

    def __call__(self, *args, **kwargs):
        self.__count += 1
        return self.func(*args, **kwargs)

    def get_count(self):
        return self.__count

@CallCounter
def hello():
    print("Hello World")

hello()
hello()
hello()

# 外部调用装饰器实例的方法
print("总调用次数：", hello.get_count())

# 什么时候优先使用类装饰器：需要保存状态，外部需要操作内部数据，资源管理

'''
异步：一个工人特别会统筹，等着干一件事的时候，就赶紧去干另一件事
AI：agent->调用，cpu去服务于别的用户
模拟“多个用户请求AI模型”
同步vs异步
sync同步：time.sleep(2)
async异步：await asyncio.sleep(2)
关键词
async def：定义一个特殊函数，协程函数，注意：调用时并不会马上执行，只是获得一个任务单
await：等一下
asyncio.run(...)：总开关，启动整个异步系统，程序入口
'''
import asyncio
import time

async def task(name):
    print(f"{name} 开始")
    await asyncio.sleep(2)
    print(f"{name} 结束")

async def main():
    start = time.time()
    # await task("A")
    # await task("B")
    # await task("C")
    await asyncio.gather(task("A"), task("B"), task("C"))
    end = time.time()
    print(f"异步版耗时{end-start}s")

asyncio.run(main())

async def fetch(name, delay):
    await asyncio.sleep(delay)
    print(f"{name}完成")

async def main():
    start = time.time()
    # await task("A")
    # await task("B")
    # await task("C")
    await asyncio.gather(fetch("A", 1),
                         fetch("B",1),
                         fetch("C",3))
    end = time.time()
    print(f"总耗时{end-start}s")

asyncio.run(main())


