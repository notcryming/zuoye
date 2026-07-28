import pandas as pd

try:
    df = pd.read_csv("iot_sensor_dirty.csv")
except FileNotFoundError:
    print("文件不存在，跳过读取")

df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')















