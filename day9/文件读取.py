import pandas as pd

try:
    df1 = pd.read_csv("job.csv")
except FileNotFoundError:
    print("文件不存在，跳过读取")
try:
    df2 = pd.read_excel("job.xlsx", engine="openpyxl")
except FileNotFoundError:
    print("文件不存在，跳过读取")
try:
    df3 = pd.read_csv("data.txt", sep=",")
except FileNotFoundError:
    print("文件不存在，跳过读取")
try:
    df4 = pd.read_csv("不存在的文件.csv")
except FileNotFoundError:
    print("文件不存在，跳过读取")

filename = {1: "job.csv", 2: "job.xlsx", 3: "data.txt"}
#column, value
i = 1
for df in [df1,df2,df3]:
    column = df.isnull().mean().idxmax()
    value = df.isnull().mean().max()
    print(f"文件{filename[i]}的{column}列，缺失值最大，为 {int(value*100)}%")
    i += 1

print(df["salary"])
# 方式1：布尔条件筛选 + len()
# print(len(df[int(df["salary"]) > 50000]))
#
# # 方式2：条件筛选 + .shape[0]
# print(df[df["salary"] > 50000].shape[0])
#
# # 方式3：使用 sum() 直接计数（将 True/False 转为 1/0 求和）
# print((df["salary"] > 50000).sum())

