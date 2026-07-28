# 任务一
import pandas as pd

try:
    df = pd.read_csv("ecommerce_dirty.csv")
except FileNotFoundError:
    print("文件不存在，跳过读取")

# 事件标准化
# 清理首尾空格
df['event_type'] = df['event_type'].str.strip()
# 替换中文用 regex=False 表示这是固定字符串替换，避免正则匹配的性能消耗或误匹配
df['event_type'] = df['event_type'].str.replace('购买', 'purchase', regex=False)
# 统一英文小写：覆盖 VIEW / View / vIEW 等所有大小写组合
df['event_type'] = df['event_type'].str.lower()
# 未知值兜底：定义允许的标准事件列表，非列表内的强制归为 view
allowed_events = ['view', 'cart', 'purchase']
# 用 ~df[...].isin(...) 取出「不在允许列表」的行，赋值为 view
df.loc[~df['event_type'].isin(allowed_events), 'event_type'] = 'view'

# 年龄异常剔除
# 类型安全处理：将年龄列强制转为数值，非法值（如"空"、"abc"）自动变为 NaN
df['user_age'] = pd.to_numeric(df['user_age'], errors='coerce')
# 定义有效年龄的布尔条件（注意：必须加括号，否则会因运算符优先级报错）
valid_age_mask = (df['user_age'] >= 0) & (df['user_age'] <= 100)
# 筛选保留有效行
df = df[valid_age_mask]

# 处理时间戳格式错误
# 仅用于诊断的备份列（不用于修改！）
df['timestamp_raw'] = df['timestamp']
# 去首尾空格
df['timestamp'] = df['timestamp'].str.strip()
# 自动解析
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
failed_mask = df['timestamp'].isna()
# 提取失败行的【原始字符串】（用备份列 timestamp_raw）
#     重新取原始字符串，因为主表的 timestamp 已经是 NaT 了
failed_strings = df.loc[failed_mask, 'timestamp_raw'].str.strip()
# 用缺秒格式解析这些原始字符串
parsed_2 = pd.to_datetime(
    failed_strings,
    format='%Y/%m/%d %H:%M',  # 匹配 2024/01/01 04:37 这种缺秒格式
    errors='coerce')
# 把补解析成功的结果写回主表的 timestamp 列
# 用 failed_mask & parsed_2.notna() 精准定位需要更新的行
df.loc[failed_mask & parsed_2.notna(), 'timestamp'] = parsed_2
# 检查剩余未解析的行
still_failed = df['timestamp'].isna()
# 删除剩余非法值的行
df = df.dropna(subset=['timestamp'])
# 删除诊断用的备份列
df.drop(columns=['timestamp_raw'], inplace=True)

# 所有列完全相同的行，保留第一条
df = df.drop_duplicates(keep='first')

# 确保 price是数值型
df['price'] = pd.to_numeric(df['price'], errors='coerce')
# 计算每个 category 的价格中位数（返回与原表等长的 Series）
category_median = df.groupby('category')['price'].transform('median')
# 计算全局价格中位数
global_median = df['price'].median()
# 先用类别中位数填充
df['price'] = df['price'].fillna(category_median)
# 再用全局中位数填充剩余的空值（即该 category 全为空的情况）
df['price'] = df['price'].fillna(global_median)

# 设备规范化
df['device'] = df['device'].str.strip().str.lower()

df.to_csv('cleaned_data.csv', index=False, encoding='utf-8-sig')

