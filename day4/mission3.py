import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading
import asyncio

class AIModel():
    def __init__(self, name, model_type):
        self.name = name
        self.model_type = model_type

    async def predict(self, input_data):
        # print(f"{self.name}模型收到输入：{input_data},但具体推理逻辑由子类实现")
        # return "父类默认结果"
        raise NotImplementedError("子类必须实现predict方法")


class TextModel(AIModel):
    def __init__(self, name, model_type):
        super().__init__(name, model_type)

    async def predict(self, input_data):
        # print(f"文本模型{self.name}正在生成文本...")
        start = datetime.now()
        await asyncio.sleep(1)
        end = datetime.now()
        cost = (end - start).total_seconds()
        return f"文本结果：{input_data}", cost


class ImageModel(AIModel):
    def __init__(self, name, model_type):
        super().__init__(name, model_type)

    async def predict(self, input_data):
        # print(f"图像模型{self.name}正在识别图像...")
        start = datetime.now()
        await asyncio.sleep(2)
        end = datetime.now()
        cost = (end - start).total_seconds()
        return f"图像结果：{input_data}", cost


class AudioModel(AIModel):
    def __init__(self, name, model_type):
        super().__init__(name, model_type)

    async def predict(self, input_data):
        print(f"语音模型{self.name}正在生成音频...")
        start = datetime.now()
        await asyncio.sleep(3)
        end = datetime.now()
        cost = (end - start).total_seconds()
        return f"音频结果：{input_data}", cost


class Scheduler():
    def __init__(self):
        self.records = []
        self.lock = threading.Lock()

    def report(self):
        for i in self.records:
            print(f"{i['user']}的问题已由{i['model']}花费{i['cost']}s解决，{i['result']}")

    async def user_request(self, model, user_name, input_data):  # 单个下划线是保护类型
        start = datetime.now()
        # print(f"用户{user_name}发起请求")  # 传入AI模型实例，这样来访问模型类里面的predict
        result, cost = await model.predict(input_data)
        # print(f"模型{model.name}推理结束")
        self.lock.acquire()
        record = {"user": user_name, "model": model.name, "cost": cost, "result": result}
        self.records.append(record)
        self.lock.release()
        end = datetime.now()
        cost = (end - start).total_seconds()
        print(f"任务{input_data}已完成，耗时{cost:.2f}秒")
        return cost


async def main():
    text = TextModel("解意", "文本模型")
    image = ImageModel("识图", "图像模型")
    voice = AudioModel("闻声", "声音模型")
    S = Scheduler()
    # 文本图像混合任务
    list1 = [(text, "路人甲", "今天天气如何"), (image, "路人丙", "图片A.jpg"),
             (image, "路人乙", "图片B.jpg"), (text, "路人乙", "附近有什么好吃的")]
    # 异步任务
    tasks = [S.user_request(mod, un, inda) for mod, un, inda in list1]
    start = time.time()
    await asyncio.gather(*tasks)
    end = time.time()
    cost = end - start
    print(f"异步总耗时{cost:.2f}秒")
    print(f"当前系统时间为：{datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')}")

asyncio.run(main())