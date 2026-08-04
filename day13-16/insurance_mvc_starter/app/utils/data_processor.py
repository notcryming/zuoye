"""Excel 解析工具

【MVC 归属】工具层（纯函数，不依赖业务层）
【思路】
1. parse_excel：读 Excel → 校验列名 → 转小写下划线 → 校验类型 → 收集非法行 → 返回 list[dict]
2. build_quality_report：基于解析后的行算数据质量报告（缺失/重复/类型）
3. 解析失败抛 BizException(2002)，列名缺失抛 BizException(2002)

为什么用 pandas？
  pandas.read_excel 一行解析 + 向量化类型转换，比 openpyxl 手写循环简洁稳定。
"""
import io
import pandas as pd
from werkzeug.datastructures import FileStorage
from app.core.response import BizException

# Excel 原始列名 → 入库字段名（小写下划线）
COLUMN_MAP = {
    "id": "id",
    "Gender": "gender",
    "Age": "age",
    "Driving_License": "driving_license",
    "Region_Code": "region_code",
    "Previously_Insured": "previously_insured",
    "Vehicle_Age": "vehicle_age",
    "Vehicle_Damage": "vehicle_damage",
    "Annual_Premium": "annual_premium",
    "Policy_Sales_Channel": "policy_sales_channel",
    "Vintage": "vintage",
    "Response": "response",
}

# 必须存在的原始列名
REQUIRED_COLUMNS = set(COLUMN_MAP.keys())

# 数值列（需转数字，非法转 NaN 后剔除该行）
NUMERIC_COLUMNS = [
    "id", "age", "driving_license", "region_code", "previously_insured",
    "annual_premium", "policy_sales_channel", "vintage", "response",
]

# 整数列（数值校验通过后转 int）
INT_COLUMNS = ["id", "age", "driving_license", "previously_insured", "vintage", "response"]


def parse_excel(file_storage: FileStorage) -> list[dict]:
    """解析 Excel → 返回合法行（list[dict]，键为小写下划线字段名）

    逐字思路：
    1. 读文件流到 pandas DataFrame（失败 → BizException 2002）
    2. 校验列名是否齐全（缺列 → BizException 2002）
    3. 列名统一转小写下划线
    4. 数值列 to_numeric(errors='coerce')，非法值变 NaN
    5. 收集含 NaN 的非法行到 errors，剔除后返回合法行
    """
    # 1. 读取
    try:
        stream = io.BytesIO(file_storage.read())
        df = pd.read_excel(stream)
    except Exception as e:
        raise BizException(2002, f"Excel 解析失败：{e}", 400)

    if df.empty:
        raise BizException(2002, "Excel 文件为空", 400)

    # 2. 校验列名
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise BizException(2002, f"缺少必要列：{','.join(sorted(missing))}", 400)

    # 3. 列名转小写下划线（只保留需要的列）
    df = df.rename(columns=COLUMN_MAP)[list(COLUMN_MAP.values())]

    # 4. 数值列类型转换
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 4.5 缓存"原始"质量报告（基于清洗前的 df，缺失值才真实反映原始数据）
    _last_raw_report.clear()
    _last_raw_report.update(_compute_report_from_df(df))

    # 5. 收集非法行（数值列出现 NaN 视为非法）
    errors: list[dict] = []
    mask = df[NUMERIC_COLUMNS].isnull().any(axis=1)
    for idx in df[mask].index:
        errors.append({"row": int(idx) + 2, "reason": "数值字段非法或缺失"})  # +2：表头 + 1 起始

    # 剔除非法行
    df = df[~mask].copy()

    # 整数列转 int（pandas 读 Excel 常把整数读成 float）
    for col in INT_COLUMNS:
        df[col] = df[col].astype(int)

    # 转成 list[dict]
    rows = df.to_dict(orient="records")

    # 非法行信息挂到模块级，供 build_quality_report 取用
    _last_errors.clear()
    _last_errors.extend(errors)

    return rows


# 模块级缓存上一次解析的非法行（简单教学实现，避免改 parse_excel 签名）
_last_errors: list[dict] = []

# 模块级缓存上一次解析的"原始"质量报告（清洗前，缺失值才真实）
_last_raw_report: dict = {}


def get_last_errors() -> list[dict]:
    """取上一次 parse_excel 收集到的非法行"""
    return list(_last_errors)


def get_last_raw_report() -> dict:
    """取上一次 parse_excel 基于原始数据算出的质量报告（清洗前）"""
    return dict(_last_raw_report)


def _compute_report_from_df(df) -> dict:
    """从 DataFrame 算质量报告（build_quality_report / parse_excel 复用）"""
    if df is None or df.empty:
        return {
            "total_rows": 0,
            "total_cols": 0,
            "missing_values": {},
            "duplicates": 0,
            "dtypes": {},
        }
    missing = {k: int(v) for k, v in df.isnull().sum().to_dict().items()}
    duplicates = int(df.duplicated().sum())
    dtypes = {k: str(v) for k, v in df.dtypes.astype(str).to_dict().items()}
    return {
        "total_rows": len(df),
        "total_cols": len(df.columns),
        "missing_values": missing,
        "duplicates": duplicates,
        "dtypes": dtypes,
    }


def build_quality_report(rows: list[dict]) -> dict:
    """基于解析后的合法行算数据质量报告

    返回结构对齐 API 文档 2.1 的 quality_report：
    { total_rows, total_cols, missing_values, duplicates, dtypes }

    注意：若需反映"原始数据"的缺失情况（含被清洗掉的非法行），
    请改用 get_last_raw_report()，本函数入参是清洗后的 rows，缺失值恒为 0。
    """
    if not rows:
        return _compute_report_from_df(None)
    return _compute_report_from_df(pd.DataFrame(rows))


# ====================================================================
# 机器学习特征工程工具
# ====================================================================

# ML 特征列（顺序固定，训练 / 预测必须一致）
# 注意：id 仅是数据顺序标识，对训练无帮助，已剔除；
#       annual_premium 分布不均，改用 annual_premium_bin 分箱特征
FEATURE_COLUMNS = [
    "gender", "age", "driving_license", "region_code", "previously_insured",
    "vehicle_age", "vehicle_damage", "annual_premium_bin", "policy_sales_channel", "vintage",
]

# 原始输入特征列（编码前，用于上传预测时校验 Excel 列是否齐全）
# 与 FEATURE_COLUMNS 的差异：annual_premium（原始）→ annual_premium_bin（分箱后）
ORIGINAL_FEATURE_COLUMNS = [
    "gender", "age", "driving_license", "region_code", "previously_insured",
    "vehicle_age", "vehicle_damage", "annual_premium", "policy_sales_channel", "vintage",
]

# 标签列
LABEL_COLUMN = "response"

# 分类特征编码映射（对齐 AI 技术方案 2.3）
GENDER_MAP = {"Male": 0, "Female": 1}
VEHICLE_DAMAGE_MAP = {"No": 0, "Yes": 1}
VEHICLE_AGE_MAP = {"< 1 Year": 0, "1-2 Year": 1, "> 2 Years": 2}

# Annual_Premium 分箱配置（保费分布不均，按业务逻辑分段更稳健）
ANNUAL_PREMIUM_BINS = [0, 10000, 20000, 40000, 70000, 100000, float('inf')]
ANNUAL_PREMIUM_LABELS = [1, 2, 3, 4, 5, 6]

# 反编码映射（编码值 → 自然语言，供 LLM 模块调用）
DECODE_MAP = {
    "gender": {0: "男", 1: "女"},
    "vehicle_damage": {0: "未受损", 1: "曾受损"},
    "vehicle_age": {0: "< 1年", 1: "1-2年", 2: "> 2年"},
    "driving_license": {0: "无驾照", 1: "有驾照"},
    "previously_insured": {0: "未投保", 1: "已投保"},
}


def encode_raw_features(df: pd.DataFrame) -> pd.DataFrame:
    """特征编码：性别/车辆损伤 Label 编码，车龄有序编码，保费分箱

    【关键】本函数只做分类 → 数值的编码与分箱，不做 StandardScaler 标准化。
    标准化由 ml_service 在训练时 fit、预测时 transform，避免数据泄漏。

    逐字思路：
    1. copy df 避免修改原始数据
    2. 显式剔除 id 列（仅是数据顺序标识，对训练无帮助）
    3. gender: Male=0, Female=1（Label 编码）
    4. vehicle_damage: No=0, Yes=1（Label 编码）
    5. vehicle_age: < 1 Year=0, 1-2 Year=1, > 2 Years=2（Ordinal 有序编码，保留大小关系）
    6. annual_premium: 按业务逻辑分段分箱（0-1万/1-2万/2-4万/4-7万/7-10万/>10万），
       删除原始保费列，分布不均时分箱后更稳健
    7. 返回编码后的 DataFrame（仅含 FEATURE_COLUMNS）
    """
    df = df.copy()

    # 2. 显式剔除 id 列（仅是数据顺序标识，不参与训练）
    if "id" in df.columns:
        df = df.drop(columns=["id"])

    # 3-5. 分类特征 Label / Ordinal 编码
    df["gender"] = df["gender"].map(GENDER_MAP)
    df["vehicle_damage"] = df["vehicle_damage"].map(VEHICLE_DAMAGE_MAP)
    df["vehicle_age"] = df["vehicle_age"].map(VEHICLE_AGE_MAP)

    # 检查编码后是否有 NaN（原始值不在映射表里）
    for col in ["gender", "vehicle_damage", "vehicle_age"]:
        if df[col].isnull().any():
            raise BizException(2002, f"特征编码失败：{col} 列存在未知值", 400)

    # 6. Annual_Premium 分箱（保费分布不均，按业务逻辑分段）
    if "annual_premium" not in df.columns:
        raise BizException(2002, "特征编码失败：缺少 annual_premium 列", 400)
    # 缺失/非法保费先转 NaN，分箱后同样为 NaN，下面统一剔除
    df["annual_premium"] = pd.to_numeric(df["annual_premium"], errors="coerce")
    if df["annual_premium"].isnull().any():
        raise BizException(2002, "特征编码失败：annual_premium 列存在非法或缺失值", 400)
    df["annual_premium_bin"] = pd.cut(
        df["annual_premium"],
        bins=ANNUAL_PREMIUM_BINS,
        labels=ANNUAL_PREMIUM_LABELS,
        include_lowest=True,
    ).astype(int)
    # 删除原始保费列（已被分箱特征替代）
    df = df.drop(columns=["annual_premium"])

    return df[FEATURE_COLUMNS]


def decode_feature_text(val, field: str) -> str:
    """编码值反译为自然语言（供 LLM 模块调用）

    逐字思路：
    1. 从 DECODE_MAP 查 field 对应的反编码字典
    2. 找不到 field 或 val → 返回 str(val) 兜底
    3. 返回自然语言字符串（如 1 → "女"、"曾受损"）

    这是 ML → LLM 的"反编码桥梁"：ML 用 0/1 编码训练，
    LLM 看自然语言，两者衔接处必须语义还原。
    """
    mapping = DECODE_MAP.get(field)
    if mapping is None:
        return str(val)
    return mapping.get(val, str(val))


def parse_excel_for_prediction(file_storage: FileStorage) -> pd.DataFrame:
    """解析预测用 Excel → 返回编码后的特征 DataFrame

    与 parse_excel 区别：本函数不要求 Response 列（预测时可能无标签），
    只需要特征列。返回 pandas DataFrame 而非 list[dict]。

    逐字思路：
    1. 读 Excel → 校验特征列是否齐全
    2. 列名转小写下划线
    3. 数值列 to_numeric
    4. 剔除含 NaN 的非法行
    5. encode_raw_features 编码分类特征
    6. 返回编码后的 DataFrame
    """
    # 1. 读取
    try:
        stream = io.BytesIO(file_storage.read())
        df = pd.read_excel(stream)
    except Exception as e:
        raise BizException(2002, f"Excel 解析失败：{e}", 400)

    if df.empty:
        raise BizException(2002, "Excel 文件为空", 400)

    # 2. 校验特征列（Response 可选）
    feature_columns_original = [k for k in COLUMN_MAP.keys() if COLUMN_MAP[k] != "response"]
    missing = set(feature_columns_original) - set(df.columns)
    if missing:
        raise BizException(2002, f"缺少必要列：{','.join(sorted(missing))}", 400)

    # 3. 列名转小写下划线（保留所有可用列）
    rename_map = {k: v for k, v in COLUMN_MAP.items() if k in df.columns}
    df = df.rename(columns=rename_map)

    # 4. 数值列类型转换
    numeric_cols = [c for c in NUMERIC_COLUMNS if c in df.columns and c != "response"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 5. 剔除含 NaN 的非法行
    df = df.dropna(subset=numeric_cols).copy()

    # 整数列转 int
    int_cols = [c for c in INT_COLUMNS if c in df.columns and c != "response"]
    for col in int_cols:
        df[col] = df[col].astype(int)

    # 6. 特征编码
    df_encoded = encode_raw_features(df)

    return df_encoded


# ====================================================================
# 客户画像自然语言转换（ML → LLM 反编码桥梁）
# ====================================================================

# 原始 DB 值 → 自然语言中文描述（供 LLM Prompt 用）
# DB 存储的 gender/vehicle_damage/vehicle_age 是英文字符串，
# driving_license/previously_insured 是 0/1 整数，
# 禁止直接传 0/1 编码给 LLM，全部转换为中文描述。
RAW_TEXT_MAP = {
    "gender": {"Male": "男", "Female": "女"},
    "vehicle_damage": {"Yes": "曾受损", "No": "未受损"},
    "vehicle_age": {"< 1 Year": "< 1年", "1-2 Year": "1-2年", "> 2 Years": "> 2年"},
    "driving_license": {0: "无驾照", 1: "有驾照"},
    "previously_insured": {0: "未投保", 1: "已投保"},
}


def customer_to_natural_text(customer) -> dict:
    """客户画像反编码：DB 原始值 → 自然语言中文描述 dict

    【用途】LLM Prompt 占位符填充的桥梁：ML 用 0/1 编码训练，
    LLM 看自然语言，两者衔接处必须把编码值反解为人类语言。

    逐字思路：
    1. 兼容 Customer 对象和 dict（to_dict() 后的行）
    2. 逐字段查 RAW_TEXT_MAP，找到则转中文，找不到保留原值
    3. 返回 dict，键与 Prompt 模板占位符一一对应

    示例：
      输入 {gender:"Male", age:45, driving_license:1, vehicle_age:"1-2 Year", ...}
      输出 {gender:"男", age:45, driving_license:"有驾照", vehicle_age:"1-2年", ...}
    """
    # 兼容 ORM 对象和 dict
    if hasattr(customer, "to_dict"):
        row = customer.to_dict()
    elif isinstance(customer, dict):
        row = customer
    else:
        row = dict(customer)

    result = {}
    for key, val in row.items():
        mapping = RAW_TEXT_MAP.get(key)
        if mapping is not None and val in mapping:
            result[key] = mapping[val]
        else:
            result[key] = val

    return result
