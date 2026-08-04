"""实验记录模型

【MVC 归属】Model 层（数据层）
【思路】
1. 字段对齐 API 文档 3.x 模型模块（model_name/accuracy/.../roc_auc/params/model_path/is_best）
2. params 存 JSON 字符串（可视化图表数据：ROC/混淆矩阵/特征重要性等）
3. is_best 标记当前最优模型（按 ROC-AUC 选优，全表仅一条 is_best=True）
4. 类方法封装操作，严格对齐 user.py / customers.py 的写法风格
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, Boolean, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base


class Experiment(Base):
    """实验记录模型：对应 experiments 表"""
    __tablename__ = "experiments"

    # 业务字段（按 API 文档定义）
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(50), nullable=False)  # logistic_regression / xgboost / random_forest
    accuracy: Mapped[float] = mapped_column(Float, nullable=False)
    precision: Mapped[float] = mapped_column(Float, nullable=False)
    recall: Mapped[float] = mapped_column(Float, nullable=False)
    f1_score: Mapped[float] = mapped_column(Float, nullable=False)
    roc_auc: Mapped[float] = mapped_column(Float, nullable=False)
    params: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON：可视化图表数据
    model_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # .joblib 绝对路径
    is_best: Mapped[bool] = mapped_column(Boolean, default=False)

    # 扩展字段
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)

    # ===== 序列化 =====
    def to_dict(self) -> dict:
        """转字典（供接口返回 / 分页列表复用）"""
        return {
            "id": self.id,
            "model_name": self.model_name,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1_score": self.f1_score,
            "roc_auc": self.roc_auc,
            "params": self.params,
            "model_path": self.model_path,
            "is_best": self.is_best,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }

    # ===== 类方法（对齐 user.py / customers.py 风格：classmethod 封装操作）=====
    @classmethod
    def create_record(cls, db: Session, args: dict) -> "Experiment":
        """创建实验记录：add → commit → refresh 拿自增 id

        逐字思路：
        1. 把 args（含 model_name/accuracy/.../params/model_path/is_best）展开成 Experiment 实例
        2. add → commit → refresh 拿自增 id
        3. 返回实验记录对象
        """
        exp = cls(**args)
        db.add(exp)
        db.commit()
        db.refresh(exp)
        return exp

    @classmethod
    def get_best_model(cls, db: Session) -> Optional["Experiment"]:
        """获取当前最优模型（is_best=True 的那条）

        全表仅一条 is_best=True，取第一条即可。
        """
        return db.query(cls).filter(cls.is_best == True).first()

    @classmethod
    def get_by_name(cls, db: Session, model_name: str) -> Optional["Experiment"]:
        """按模型名查最新一条实验记录（可视化 / 预测时用）"""
        return (
            db.query(cls)
            .filter(cls.model_name == model_name)
            .order_by(cls.id.desc())
            .first()
        )

    @classmethod
    def paginate_list(cls, db: Session, page: int, per_page: int, filter_model: str = None) -> dict:
        """分页查询实验记录：返回 API 文档 0.3 的分页结构

        逐字思路：
        1. 基础 query → 可选叠加 model_name 过滤
        2. count() 算总数 → offset/limit 切当前页（按 id 倒序，最新在前）
        3. 向上取整算总页数，组装 {items,total,page,per_page,pages}
        """
        query = db.query(cls)
        if filter_model:
            query = query.filter(cls.model_name == filter_model)

        total = query.count()
        items = query.order_by(cls.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total + per_page - 1) // per_page if per_page else 0

        return {
            "items": [e.to_dict() for e in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    @classmethod
    def clear_old_best(cls, db: Session):
        """清空旧的 is_best 标记（训练新模型选优前调用）

        逐字思路：把所有 is_best=True 的记录更新为 False → commit
        """
        db.query(cls).filter(cls.is_best == True).update({cls.is_best: False})
        db.commit()

    @classmethod
    def get_latest_batch(cls, db: Session, limit: int = 3) -> list["Experiment"]:
        """取最近一批训练的实验记录（metrics_comparison 可视化用）

        按 id 倒序取最近 limit 条（一次训练最多三个模型）。
        """
        return db.query(cls).order_by(cls.id.desc()).limit(limit).all()
