import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading


class AIModel():
    def __init__(self, name, model_type):
        self.name = name
        self.model_type = model_type

    def predict(self, input_data):
        # print(f"{self.name}模型收到输入：{input_data},但具体推理逻辑由子类实现")
        # return "父类默认结果"
        raise NotImplementedError("子类必须实现predict方法")


class TextModel(AIModel):
    def __init__(self, name, model_type):
        super().__init__(name, model_type)

    def predict(self, input_data):
        print(f"文本模型{self.name}正在生成文本...")
        start = datetime.now()
        time.sleep(1)
        end = datetime.now()
        cost = (end-start).total_seconds()
        return f"生成的文本结果：{input_data}", cost



class ImageModel(AIModel):
    def __init__(self, name, model_type):
        super().__init__(name, model_type)

    def predict(self, input_data):
        print(f"图像模型{self.name}正在识别图像...")
        start = datetime.now()
        time.sleep(2)
        end = datetime.now()
        cost = (end-start).total_seconds()
        return f"识别结果：{input_data}", cost


class AudioModel(AIModel):
    def __init__(self, name, model_type):
        super().__init__(name, model_type)

    def predict(self, input_data):
        print(f"语音模型{self.name}正在生成音频...")
        start = datetime.now()
        time.sleep(3)
        end = datetime.now()
        cost = (end-start).total_seconds()
        return f"输出音频：{input_data}", cost


class Scheduler():
    def __init__(self):
        self.records = []
        self.lock = threading.Lock()

    def report(self):
        for i in self.records:
            print(f"{i['user']}的问题已由{i['model']}花费{i['cost']}s解决，{i['result']}")
            
    def _run_one(self, model, user_name, input_data):    # 单个下划线是保护类型
        print(f"用户{user_name}发起请求")                 # 传入AI模型实例，这样来访问模型类里面的predict
        result, cost = model.predict(input_data)
        print(f"模型{model.name}推理结束")
        self.lock.acquire()
        record = {"user": user_name, "model": model.name,
                  "cost": cost, "result": result}
        self.records.append(record)
        self.lock.release()
        
    def run_serial(self, list1):
        # 需要传入一个列表，这个列表的每个元素是一个有3个元素的元组，分别是使用的模型实例，用户名称，输入内容
        start = datetime.now()
        for mod, un, inda in list1:
            # 这里直接调用写好的_run_one就好了
            self._run_one(mod, un, inda)
        end = datetime.now()
        cost = (end-start).total_seconds()
        return cost

    def run_concurrent(self, list1):
        '''
        start = datetime.now()
        thread = []
        for mod, un, inda in list1:
            t = threading.Thread(target=self._run_one, args=(mod, un, inda)) 
            t.start()
            thread.append(t)
        for t in thread:
            t.join()
        end = datetime.now()
        cost = (end-start).total_seconds()
        return cost
        '''
        start = datetime.now()
        with ThreadPoolExecutor() as executor:
            futures = []
            for mod, un, inda in list1:
                fut = executor.submit(self._run_one, mod, un, inda)  # 提交任务，传参
                futures.append(fut)
        end = datetime.now()
        cost = (end-start).total_seconds()
        return cost


def main():
    text = TextModel("解意", "文本模型")
    image = ImageModel("识图", "图像模型")
    voice = AudioModel("闻声", "声音模型")
    S = Scheduler()
    # 文本图像混合任务
    list1 = [(text, "路人甲", "今天天气如何"),  (voice, "路人乙", "音频Z.mp3"), (image, "路人丙", "图片A.jpg"),
             (image, "路人乙", "图片B.jpg"),  (voice, "路人丙", "音频Y.mp3"), (text, "路人乙", "附近有什么好吃的"),
             (image, "路人甲", "图片C.jpg"), (text, "路人丙", "帮我写一段有关环境保护的作文"), (voice, "路人甲", "音频X.mp3")]
    # 串行任务
    tc = S.run_serial(list1)
    # 并行任务
    tb = S.run_concurrent(list1)
    # 打印一下全部的记录
    S.report()
    # print(f"串行总耗时{tc:.2f}秒，并行总耗时{tb:.2f}秒")
    # print(f"并行节省了{(tc-tb):.2f}秒，加速比为{tc/tb:.2f}")
    # print(f"当前系统时间为：{datetime.strftime(datetime.now(), "%Y-%m-%d %H:%M:%S")}")
    list2 = [f"串行总耗时{tc: .2f}秒，并行总耗时{tb: .2f}秒", f"并行节省了{(tc-tb): .2f}秒，加速比为{tc/tb: .2f}",
             f"当前系统时间为：{datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')}"]
    with open("report.txt", "w", encoding="utf-8") as f:
        for context in list2:
            f.write(context + "\n")
            print(context)

if __name__ == "__main__":
    main()