"""操作审计日志模型

【MVC 归属】Model 层（数据层）
【思路】
1. 字段：id、user_id、action（枚举）、details（JSON 存储操作详情）、created_at
2. action 严格限定 7 种枚举值，禁止自定义操作类型
3. details 以 JSON 字符串存储操作上下文（训练参数、生成数量、删除 ID 列表等）便于审计追溯
4. user_id 关联 users.id，记录操作发起人（nullable 兼容系统级操作）
5. 类方法封装操作，严格对齐 experiment.py / email_record.py 的写法风格

为什么 details 用 Text 存 JSON 而非 JSON 类型？
  SQLite 对 JSON 类型的支持有限，Text 存 JSON 字符串兼容性最好（与 experiment.params 一致）。
"""
import json as json_lib
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base
from app.core.response import BizException


# action 枚举值（严格限定，禁止自定义）
VALID_ACTIONS = {
    "model_training",    # 模型训练
    "prediction",        # 全量预测
    "model_import",      # 模型导入
    "email_generation",  # 邮件生成
    "email_update",      # 邮件修改
    "email_mark",        # 邮件状态标记
    "email_delete",      # 邮件删除
}


class OperationLog(Base):
    """操作审计日志模型：对应 operation_logs 表"""
    __tablename__ = "operation_logs"

    # 业务字段
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)  # 枚举值，见 VALID_ACTIONS
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON 字符串：操作上下文

    # 时间字段
    # 【坑】不能用 server_default=func.now()：SQLite 的 CURRENT_TIMESTAMP 返回 UTC 时间，
    #        会比北京时间慢 8 小时。改用 Python 端 default=datetime.now 取本地时间。
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # ===== 序列化 =====
    def to_dict(self) -> dict:
        """转字典（供接口返回 / 分页列表复用）

        details JSON 字符串反序列化为 dict 返回，前端可直接读取操作上下文。
        """
        try:
            details_dict = json_lib.loads(self.details) if self.details else None
        except (json_lib.JSONDecodeError, TypeError):
            details_dict = self.details  # 解析失败保留原始字符串

        return {
            "id": self.id,
            "user_id": self.user_id,
            "action": self.action,
            "details": details_dict,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }

    # ===== 类方法（对齐 experiment.py / email_record.py 风格：classmethod 封装操作）=====
    @classmethod
    def create_log(cls, db: Session, user_id: int, action: str, detail_dict: dict) -> "OperationLog":
        """创建操作日志：校验 action 枚举 → JSON 序列化 details → add → commit

        逐字思路：
        1. action 不在 VALID_ACTIONS 中 → 抛 BizException（禁止自定义操作类型）
        2. detail_dict 转 JSON 字符串存入 details
        3. add → commit → refresh 拿自增 id
        4. 返回日志对象
        """
        if action not in VALID_ACTIONS:
            raise BizException(1001, f"非法操作类型：{action}，允许值：{VALID_ACTIONS}", 400)

        log = cls(
            user_id=user_id,
            action=action,
            details=json_lib.dumps(detail_dict, ensure_ascii=False) if detail_dict else None,
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    @classmethod
    def paginate_logs(
        cls, db: Session, page: int, per_page: int,
        filter_user_id: int = None, filter_action: str = None,
    ) -> dict:
        """分页查询操作日志：返回 API 文档 0.3 的分页结构

        逐字思路：
        1. 基础 query → 可选叠加 user_id / action 过滤
        2. count() 算总数 → offset/limit 切当前页（按 id 倒序，最新在前）
        3. 向上取整算总页数，组装 {items,total,page,per_page,pages}
        """
        query = db.query(cls)
        if filter_user_id is not None:
            query = query.filter(cls.user_id == filter_user_id)
        if filter_action:
            query = query.filter(cls.action == filter_action)

        total = query.count()
        items = query.order_by(cls.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total + per_page - 1) // per_page if per_page else 0

        return {
            "items": [log.to_dict() for log in items],
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }
