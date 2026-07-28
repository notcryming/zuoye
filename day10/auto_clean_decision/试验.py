import pandas as pd

try:
    df = pd.read_csv("./rowdata/customer_chat_raw.csv")
except FileNotFoundError:
    print("文件不存在，跳过读取")

missing_rate = df.isnull().mean()
print(missing_rate)








