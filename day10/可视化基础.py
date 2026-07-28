from matplotlib import lines
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.family"] = ["Microsoft YaHei", "SimHei"]
plt.rcParams["axes.unicode_minus"] = False

data = {"月份":[1,2,3,4,5,6],"销售额":[50,80,120,90,150,180]}
df = pd.DataFrame(data)
print("基础图表：")
print(df)

# 折线图
plt.figure(figsize=(8,4))
plt.plot(data["月份"], data["销售额"], marker='o', color='blue', label='销量')
plt.title("销售额趋势")
plt.xlabel("月份")
plt.ylabel("销售额")
plt.grid(False)
plt.show()








