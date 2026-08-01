"""客户数据模型

【MVC 归属】Model 层（数据层）
【思路】
1. 字段对齐 API 文档 2.x 数据模块（id/gender/age/.../response）
2. uploaded_by 关联 users.id，记录由谁上传
3. predicted_prob 预测概率回写位（模型预测后填充，初始为 None）
4. 类方法封装操作，严格对齐 user.py 的写法风格
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base
from app.core.response import BizException


class Customer(Base):
    """客户模型：对应 customers 表"""
    __tablename__ = "customers"

    # 业务字段（按 API 文档定义）
    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # 用 Excel 自带 id 作主键
    gender: Mapped[str] = mapped_column(String(10), nullable=False)              # Male / Female
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    region_code: Mapped[float] = mapped_column(Float, nullable=False)            # 如 28.0
    policy_sales_channel: Mapped[float] = mapped_column(Float, nullable=False)   # 如 152.0
    previously_insured: Mapped[int] = mapped_column(Integer, nullable=False)     # 0/1
    annual_premium: Mapped[float] = mapped_column(Float, nullable=False)         # 如 40454.0
    vintage: Mapped[int] = mapped_column(Integer, nullable=False)                # 如 217
    vehicle_age: Mapped[str] = mapped_column(String(20), nullable=False)         # < 1 Year / 1-2 Year / > 2 Years
    vehicle_damage: Mapped[str] = mapped_column(String(5), nullable=False)       # Yes / No
    driving_license: Mapped[int] = mapped_column(Integer, nullable=False)        # 0/1
    response: Mapped[int] = mapped_column(Integer, nullable=False)               # 0/1（标签）

    # 扩展字段
    predicted_prob: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # 预测概率回写
    uploaded_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)  # 上传者
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    # ===== 序列化 =====
    def to_dict(self) -> dict:
        """转字典（剔除内部细节，供接口返回 / 导出复用）"""
        return {
            "id": self.id,
            "gender": self.gender,
            "age": self.age,
            "driving_license": self.driving_license,
            "region_code": self.region_code,
            "previously_insured": self.previously_insured,
            "vehicle_age": self.vehicle_age,
            "vehicle_damage": self.vehicle_damage,
            "annual_premium": self.annual_premium,
            "policy_sales_channel": self.policy_sales_channel,
            "vintage": self.vintage,
            "response": self.response,
            "predicted_prob": self.predicted_prob,
            "uploaded_by": self.uploaded_by,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }

    # ===== 类方法（对齐 user.py 风格：classmethod 封装操作）=====
    @classmethod
    def bulk_create(cls, db: Session, rows: list[dict], user_id: int) -> int:
        """批量入库：先清空旧数据（教学版覆盖策略）→ 批量插入 → commit

        逐字思路：
        1. delete() 清空 customers 旧数据（API 文档约定上传即覆盖）
        2. 把每行 dict 展开成 Customer 实例，统一打上 uploaded_by
        3. add_all 一次性加入会话 → commit 持久化
        4. 返回入库行数
        """
        db.query(cls).delete()
        objects = [cls(**row, uploaded_by=user_id) for row in rows]
        db.add_all(objects)
        db.commit()
        return len(objects)

    @classmethod
    def paginate(cls, db: Session, page: int, per_page: int, filters: dict) -> dict:
        """分页查询：带筛选条件，返回 API 文档 0.3 的分页结构

        逐字思路：
        1. 基础 query → 叠加 gender/age/previously_insured/keyword 过滤
        2. count() 算总数 → offset/limit 切当前页
        3. 向上取整算总页数，组装 {items,total,page,per_page,pages}
        """
        query = db.query(cls)
        query = cls.apply_filters(query, filters)

        total = query.count()
        items = query.order_by(cls.id).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total + per_page - 1) // per_page if per_page else 0

        return {
            "items": [c.to_dict() for c in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    @classmethod
    def count(cls, db: Session) -> int:
        """统计客户总数"""
        return db.query(cls).count()

    @classmethod
    def all_rows(cls, db: Session) -> list[dict]:
        """查全部客户转 list[dict]（质量报告 / 可视化复用）"""
        return [c.to_dict() for c in db.query(cls).order_by(cls.id).all()]

    @classmethod
    def quality_report(cls, db: Session) -> dict:
        """数据质量报告：查全表 → 算缺失/重复/类型，返回 API 文档 2.4 结构

        逐字思路：
        1. 查全部客户转 list[dict]
        2. 无数据返回空结构（total_rows=0）
        3. 转 DataFrame 算 missing_values / duplicates / dtypes
        4. 组装 {total_rows, total_cols, missing_values, duplicates, dtypes}
        """
        import pandas as pd
        rows = cls.all_rows(db)
        if not rows:
            return {
                "total_rows": 0,
                "total_cols": 0,
                "missing_values": {},
                "duplicates": 0,
                "dtypes": {},
            }
        df = pd.DataFrame(rows)
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

    @classmethod
    def find_high_potential(cls, db: Session, top_percent: float = 0.9) -> list["Customer"]:
        """筛选高潜客户：返回 predicted_prob 排名前 (1-top_percent) 的客户

        逐字思路：
        1. top_percent=0.9 表示 90 分位阈值 → 取 top 10% 的高潜客户
        2. 只看 predicted_prob 非空（已预测）的客户
        3. 按预测概率降序，取前 N 条
        """
        base = db.query(cls).filter(cls.predicted_prob.isnot(None))
        total = base.count()
        if total == 0:
            return []
        limit = max(1, total - int(top_percent * total))
        return base.order_by(cls.predicted_prob.desc()).limit(limit).all()

    @classmethod
    def apply_filters(cls, query, filters: dict):
        """公开辅助：把筛选条件叠加到 query 上（分页/导出复用）"""
        if filters.get("gender"):
            query = query.filter(cls.gender == filters["gender"])
        if filters.get("age_min") is not None:
            query = query.filter(cls.age >= filters["age_min"])
        if filters.get("age_max") is not None:
            query = query.filter(cls.age <= filters["age_max"])
        if filters.get("previously_insured") is not None:
            query = query.filter(cls.previously_insured == filters["previously_insured"])
        if filters.get("keyword"):
            try:
                query = query.filter(cls.id == int(filters["keyword"]))
            except (ValueError, TypeError):
                raise BizException(1001, "keyword 必须为数字", 400)
        return query
