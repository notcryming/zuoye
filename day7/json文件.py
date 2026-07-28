import json
data_json = '{"title": "Python工程师", "salary": "20-30K", "city": "北京"}'

# json文件读进来是字符串，用这个转成字典
data = json.loads(data_json)
print(type(data))

# 同理，字典转字符串
py_dict = {"name": "张三", "age": 25, "city": "北京"}
json_str = json.dumps(py_dict, ensure_ascii=False)
print(type(json_str))
print(json_str)









