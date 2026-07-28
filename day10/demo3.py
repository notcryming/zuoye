# -*- coding: utf-8 -*-
"""
学生成绩综合可视化大屏 Demo
功能：读取 CSV 数据，通过 6 个子图展示成绩分布、分组对比、相关性、占比及趋势
依赖：pandas（数据处理）, matplotlib（绘图）, numpy（数值计算）
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==================== 1. 全局配置 ====================
# 设置全局字体为黑体，解决中文显示为方块的问题
# 参数详解：
# 'font.sans-serif': 设置无衬线字体列表，matplotlib 会按顺序查找系统可用的字体
plt.rcParams['font.sans-serif'] = ['SimHei']

# 解决坐标轴负号"-"显示为方块的问题
# 参数详解：
# 'axes.unicode_minus': 设置为 False，表示不使用 Unicode 的负号字符，而是使用标准的 ASCII 减号
plt.rcParams['axes.unicode_minus'] = False

# ==================== 2. 数据读取与清洗 ====================
# 读取同目录下的学生成绩 CSV 文件
# 参数详解：
# "StudentsPerformance.csv": 文件路径字符串，表示读取当前目录下的该文件
df = pd.read_csv("StudentsPerformance.csv")

# 统一清洗列名：去除首尾空格，中间空格替换为下划线
# 参数详解：
# columns: 指定要重命名的对象（列名）
# lambda x: ... : 匿名函数，x 代表每一个原始列名
#   x.strip(): 去除字符串首尾的空格
#   .replace(" ", "_"): 将字符串中间的空格替换为下划线
# inplace=True: 表示直接在原 DataFrame 上修改，不返回新的 DataFrame 对象
df.rename(columns=lambda x: x.strip().replace(" ", "_"), inplace=True)

# 打印数据集的前 5 行
print("数据集前5行：")
print(df.head())

# 打印数据统计信息
print("\n数据统计信息：")
print(df.describe())

# ==================== 3. 创建画布 ====================
# 创建一个总画布（Figure 对象）
# 参数详解：
# figsize=(15, 10): 设置画布尺寸，单位是英寸（Inch）。(宽度，高度)
plt.figure(figsize=(15, 10))

# ==================== 4. 子图绘制 ====================

# -------------------- 子图1：三科成绩分布直方图 --------------------
# 在 2 行 3 列的网格布局中，选择第 1 个位置（左上角）
# 参数详解：
# 2: 行数（Rows）
# 3: 列数（Columns）
# 1: 索引（Index），表示第几个子图，索引从 1 开始，从左到右、从上到下计数
plt.subplot(2, 3, 1)

# 绘制数学成绩直方图
# 参数详解：
# df["math_score"]: 数据源，提取数学成绩列
# bins=12: 将数据范围分成 12 个等宽的区间（柱子数量）
# color="#66b3ff": 柱子填充颜色，使用十六进制颜色码（浅蓝色）
# alpha=0.7: 透明度，范围 0（完全透明）到 1（完全不透明），用于多组数据重叠时区分
# edgecolor="black": 柱子边框颜色，设置为黑色
# label="数学": 图例标签，用于后续 plt.legend() 显示图例名称
plt.hist(df["math_score"], bins=12, color="#66b3ff", alpha=0.7, edgecolor="black", label="数学")

# 绘制阅读成绩直方图
# 参数详解：
# color="#ff9999": 设置为浅红色
# alpha=0.6: 透明度稍低，以便与数学成绩区分
plt.hist(df["reading_score"], bins=12, color="#ff9999", alpha=0.6, edgecolor="black", label="阅读")

# 绘制写作成绩直方图
# 参数详解：
# color="#99ff99": 设置为浅绿色
plt.hist(df["writing_score"], bins=12, color="#99ff99", alpha=0.6, edgecolor="black", label="写作")

# 设置子图标题
# 参数详解：
# "三科成绩分布直方图": 标题文本内容
# fontsize=11: 字体大小，单位是磅（Points）
plt.title("三科成绩分布直方图", fontsize=11)

# 设置 X 轴标签
# 参数详解：
# "分数": X 轴显示的文本
plt.xlabel("分数")

# 设置 Y 轴标签
# 参数详解：
# "人数": Y 轴显示的文本
plt.ylabel("人数")

# 显示图例
# 参数详解：
# fontsize=8: 图例文字的大小
# 注：legend() 会自动收集前面绘图函数中设置的 label 参数
plt.legend(fontsize=8)

# 开启网格线
# 参数详解：
# alpha=0.3: 网格线的透明度，设置较淡以免遮挡数据
plt.grid(alpha=0.3)

# -------------------- 子图2：考前辅导分组柱状图 --------------------
# 选择第 2 个位置（上中）
plt.subplot(2, 3, 2)

# 按字段分组并计算平均分
# 参数详解：
# "test_preparation_course": 分组依据的列名
# [["math_score", "reading_score", "writing_score"]]: 选择要计算的列列表
# .mean(): 聚合函数，计算每组的平均值
group = df.groupby("test_preparation_course")[["math_score", "reading_score", "writing_score"]].mean()

# 提取"未参加辅导"组的数据
# 参数详解：
# loc["none"]: 通过标签索引提取名为 "none" 的行
# .values: 将 pandas Series 转换为 numpy 数组，便于绘图
none_data = group.loc["none"].values

# 提取"完成辅导"组的数据
comp_data = group.loc["completed"].values

# 生成横坐标位置数组
# 参数详解：
# [1, 2, 3]: 定义三个位置，分别对应数学、阅读、写作三个柱子组
x = np.array([1, 2, 3])

# 设置柱子宽度
# 参数详解：
# 0.35: 单根柱子的宽度，两根柱子总宽 0.7，中间留出 0.3 的间隙
width = 0.35

# 绘制左侧柱子（未参加辅导）
# 参数详解：
# x - width/2: 横坐标，将柱子中心向左偏移宽度的一半，实现并列效果
# none_data: 纵坐标，柱子的高度数据
# width: 柱子宽度
# label="未参加辅导": 图例标签
# color="#ff7f7f": 填充颜色（粉红色）
bar1 = plt.bar(x - width/2, none_data, width, label="未参加辅导", color="#ff7f7f")

# 绘制右侧柱子（完成辅导）
# 参数详解：
# x + width/2: 横坐标，向右偏移
# comp_data: 纵坐标数据
# color="#7fbf7f": 填充颜色（浅绿色）
bar2 = plt.bar(x + width/2, comp_data, width, label="完成考前辅导", color="#7fbf7f")

# 循环给柱子顶部添加数值标签
for bar in bar1:
    # 获取柱子高度
    h = bar.get_height()
    # 添加文本
    # 参数详解：
    # bar.get_x() + bar.get_width()/2: X 坐标，计算柱子中心的 X 值
    # h + 0.4: Y 坐标，在柱子顶部上方 0.4 单位处
    # f"{h:.1f}": 文本内容，格式化字符串，保留 1 位小数
    # ha="center": 水平对齐方式（Horizontal Alignment），center 表示居中
    # fontsize=8: 字体大小
    plt.text(bar.get_x() + bar.get_width()/2, h + 0.4, f"{h:.1f}", ha="center", fontsize=8)

# 循环给第二组柱子添加数值标签
for bar in bar2:
    h = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, h + 0.4, f"{h:.1f}", ha="center", fontsize=8)

# 设置 X 轴刻度
# 参数详解：
# x: 刻度位置列表 [1, 2, 3]
# ["数学", "阅读", "写作"]: 刻度标签列表，对应显示的文字
# fontsize=9: 标签字体大小
plt.xticks(x, ["数学", "阅读", "写作"], fontsize=9)

# 设置 Y 轴范围
# 参数详解：
# 0: Y 轴最小值
# 100: Y 轴最大值（满分）
plt.ylim(0, 100)

# 设置标题、轴标签
plt.title("有无考前辅导平均分对比", fontsize=11)
plt.xlabel("科目")
plt.ylabel("平均分")

# 显示图例
plt.legend(fontsize=8)

# 开启 Y 轴网格
# 参数详解：
# axis="y": 仅在 Y 轴方向（横向）绘制网格线
# alpha=0.3: 透明度
plt.grid(axis="y", alpha=0.3)

# -------------------- 子图3：阅读与写作相关性散点图 --------------------
# 选择第 3 个位置（右上角）
plt.subplot(2, 3, 3)

# 筛选男生数据
# 参数详解：
# df["gender"] == "male": 布尔条件，筛选性别为 male 的行
df_male = df[df["gender"] == "male"]

# 筛选女生数据
df_female = df[df["gender"] == "female"]

# 绘制男生散点
# 参数详解：
# df_male["reading_score"]: X 轴数据（阅读分数）
# df_male["writing_score"]: Y 轴数据（写作分数）
# c="#3366ff": 点的颜色（Color），蓝色
# alpha=0.4: 透明度，防止密集点重叠看不清
# label="男生": 图例标签
# s=20: 点的大小（Size），单位是像素^2
plt.scatter(df_male["reading_score"], df_male["writing_score"], c="#3366ff", alpha=0.4, label="男生", s=20)

# 绘制女生散点
# 参数详解：
# c="#ff3366": 点的颜色，红色
plt.scatter(df_female["reading_score"], df_female["writing_score"], c="#ff3366", alpha=0.4, label="女生", s=20)

# 线性拟合
x_all = df["reading_score"]
y_all = df["writing_score"]

# 计算拟合系数
# 参数详解：
# x_all, y_all: 拟合的 X 和 Y 数据
# 1: 多项式阶数（Degree），1 表示一次多项式（直线）
z = np.polyfit(x_all, y_all, 1)

# 生成多项式函数
# 参数详解：
# z: 拟合系数数组 [斜率，截距]
p = np.poly1d(z)

# 绘制拟合直线
# 参数详解：
# x_all: X 轴数据
# p(x_all): Y 轴数据，根据拟合函数计算出的值
# c="black": 线条颜色，黑色
# linewidth=2: 线条宽度，2 像素
# label="线性拟合线": 图例标签
plt.plot(x_all, p(x_all), c="black", linewidth=2, label="线性拟合线")

# 计算相关系数
# 参数详解：
# [0, 1]: 取相关系数矩阵的第一行第二列元素（x 与 y 的相关性）
corr = np.corrcoef(x_all, y_all)[0, 1]

# 添加相关系数文本
# 参数详解：
# 20: X 坐标位置
# 92: Y 坐标位置
# f"相关系数 r={corr:.3f}": 文本内容，保留 3 位小数
# fontsize=9: 字体大小
plt.text(20, 92, f"相关系数 r={corr:.3f}", fontsize=9)

# 设置标题和轴标签
plt.title("阅读与写作成绩相关性", fontsize=11)
plt.xlabel("阅读分数")
plt.ylabel("写作分数")

# 显示图例和网格
plt.legend(fontsize=8)
plt.grid(alpha=0.3)

# -------------------- 子图4：午餐类型占比饼图 --------------------
# 选择第 4 个位置（左下角）
plt.subplot(2, 3, 4)

# 统计频数
# 参数详解：
# .value_counts(): 统计每个类别出现的次数，返回 Series（索引为类别名，值为次数）
lunch_count = df["lunch"].value_counts()

# 提取标签和大小
labels = lunch_count.index.tolist()  # 类别名称列表
sizes = lunch_count.values           # 对应的人数数组

# 设置突出效果
# 参数详解：
# 列表推导式：如果当前值 i 等于最大值 sizes.max()，则偏移 0.08，否则为 0
explode = [0.08 if i == sizes.max() else 0 for i in sizes]

# 绘制饼图
# 参数详解：
# sizes: 每块饼的大小（决定角度）
# labels: 每块饼的标签
# autopct="%.1f%%": 自动显示百分比，格式为保留 1 位小数加百分号
# explode: 突出显示列表，非 0 的块会向外偏移
# colors=["#66c2a5", "#fc8d62"]: 颜色列表，按顺序分配给每块饼
# shadow=True: 显示阴影效果，增加立体感
# startangle=90: 起始角度，90 度表示从 12 点钟方向开始逆时针绘制
# textprops={"fontsize": 8}: 文本属性字典，设置标签和百分比的字体大小
plt.pie(sizes, labels=labels, autopct="%.1f%%", explode=explode,
        colors=["#66c2a5", "#fc8d62"], shadow=True, startangle=90, textprops={"fontsize": 8})

# 设置标题
plt.title("学生午餐类型占比", fontsize=11)

# -------------------- 子图5：家长学历成绩趋势折线图 --------------------
# 选择第 5 个位置（下中）
plt.subplot(2, 3, 5)

# 定义学历顺序
# 参数详解：
# 列表：按逻辑从低到高排列，防止 pandas 默认按字母排序导致折线乱跳
edu_order = ["some high school", "high school", "some college", 
             "associate's degree", "bachelor's degree", "master's degree"]

# 转换为有序分类变量
# 参数详解：
# categories=edu_order: 指定分类的顺序
# ordered=True: 标记为有序分类，保证 groupby 时按此顺序输出
df["parental_level_of_education"] = pd.Categorical(df["parental_level_of_education"], categories=edu_order, ordered=True)

# 分组计算平均分
edu_group = df.groupby("parental_level_of_education")[["math_score", "reading_score", "writing_score"]].mean()

# 提取数据
x = edu_group.index            # X 轴：学历类别
math_y = edu_group["math_score"]  # Y 轴：数学平均分
read_y = edu_group["reading_score"] # Y 轴：阅读平均分
write_y = edu_group["writing_score"]  # Y 轴：写作平均分

# 绘制数学折线
# 参数详解：
# x: X 轴数据
# math_y: Y 轴数据
# marker="o": 数据点标记样式，"o" 表示圆形
# linewidth=2: 线条宽度
# color="#e41a1c": 线条颜色，红色
# label="数学": 图例标签
plt.plot(x, math_y, marker="o", linewidth=2, color="#e41a1c", label="数学")

# 绘制阅读折线
# 参数详解：
# marker="s": 标记样式，"s" 表示方形（Square）
# color="#377eb8": 颜色，蓝色
plt.plot(x, read_y, marker="s", linewidth=2, color="#377eb8", label="阅读")

# 绘制写作折线
# 参数详解：
# marker="^": 标记样式，"^" 表示向上三角形
# color="#4daf4a": 颜色，绿色
plt.plot(x, write_y, marker="^", linewidth=2, color="#4daf4a", label="写作")

# 设置标题和轴标签
plt.title("家长学历与三科平均分趋势", fontsize=11)
plt.xlabel("家长学历")
plt.ylabel("平均分")

# 设置 X 轴刻度旋转
# 参数详解：
# rotation=25: 标签逆时针旋转 25 度，防止长文字重叠
# fontsize=7: 字体大小
plt.xticks(rotation=25, fontsize=7)

# 显示图例和网格
plt.legend(fontsize=8)
plt.grid(alpha=0.3)

# 设置 Y 轴范围
# 参数详解：
# 60: 最小值
# 80: 最大值（截取范围，放大分数差异）
plt.ylim(60, 80)

# -------------------- 子图6：空白占位 --------------------
# 选择第 6 个位置（右下角）
plt.subplot(2, 3, 6)

# 关闭坐标轴
# 参数详解：
# "off": 关闭所有坐标轴元素（边框、刻度、标签），仅保留空白区域
plt.axis("off")

# ==================== 5. 全局后处理与输出 ====================
# 自动调整子图间距
# 参数详解：
# tight_layout(): 自动计算子图边界，调整间距，防止标题、标签重叠
plt.tight_layout()

# 保存图片
# 参数详解：
# "学生成绩综合可视化大图.png": 保存的文件名
# dpi=300: 分辨率（Dots Per Inch），300 表示高清打印质量（默认 100）
plt.savefig("学生成绩综合可视化大图.png", dpi=300)

# 打印提示
print("\n✅ 图片已保存为 '学生成绩综合可视化大图.png'")

# 显示图表
# 参数详解：
# show(): 弹出窗口显示图表，程序会在此阻塞直到关闭窗口
plt.show()
