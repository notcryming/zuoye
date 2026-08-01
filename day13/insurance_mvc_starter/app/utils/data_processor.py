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
