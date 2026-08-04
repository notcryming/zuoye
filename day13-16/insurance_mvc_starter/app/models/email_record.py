"""邮件记录模型

【MVC 归属】Model 层（数据层）
【思路】
1. 字段：id、customer_id、subject、content、status、created_by、created_at
2. status 三态：generated（LLM 生成成功）/ failed（LLM 失败或未配置）/ sent（已发送）
3. created_by 关联 users.id，记录由谁生成（普通用户仅看自己的，admin 看全部）
4. 类方法封装操作，严格对齐 user.py / experiment.py 的写法风格

为什么 status 用字符串而非枚举？
  教学版简化，字符串直观可读；生产可换 SQLAlchemy Enum 类型。
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base
from app.core.response import BizException
from app.models.user import User


class EmailRecord(Base):
    """邮件记录模型：对应 email_records 表"""
    __tablename__ = "email_records"

    # 业务字段
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.id"), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # failed 时可能为空
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 邮件 HTML 正文
    status: Mapped[str] = mapped_column(String(20), default="generated")  # generated / failed / sent

    # 扩展字段
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    # ===== 序列化 =====
    def to_dict(self, include_content: bool = False) -> dict:
        """转字典（供接口返回复用）

        include_content=False 时不含 content 正文（列表接口省流量），
        详情接口传 True 返回完整内容。
        """
        d = {
            "id": self.id,
            "customer_id": self.customer_id,
            "subject": self.subject,
            "status": self.status,
            "created_by": self.created_by,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
        }
        if include_content:
            d["content"] = self.content
        return d

    # ===== 类方法（对齐 user.py / experiment.py 风格：classmethod 封装操作）=====
    @classmethod
    def batch_create(cls, db: Session, record_list: list[dict]) -> list["EmailRecord"]:
        """批量创建邮件记录：add_all → commit → refresh

        逐字思路：
        1. record_list 每项含 customer_id/subject/content/status/created_by
        2. 展开成 EmailRecord 实例列表 → add_all 一次性加入会话
        3. commit → 逐条 refresh 拿自增 id
        4. 返回记录对象列表
        """
        records = [cls(**item) for item in record_list]
        db.add_all(records)
        db.commit()
        for r in records:
            db.refresh(r)
        return records

    @classmethod
    def paginate_records(
        cls, db: Session, user_id: int, page: int, per_page: int,
        status_filter: str = None, is_admin: bool = False,
    ) -> dict:
        """分页查询邮件记录：返回 API 文档 0.3 的分页结构

        逐字思路：
        1. 基础 query → admin 看全部，普通用户只看 created_by=user_id
        2. 可选叠加 status 过滤
        3. count() 算总数 → offset/limit 切当前页（按 id 倒序，最新在前）
        4. 组装 {items,total,page,per_page,pages}
        5. admin 额外附 created_by_username（需 join users 表）
        """
        query = db.query(cls)
        if not is_admin:
            query = query.filter(cls.created_by == user_id)

        if status_filter:
            query = query.filter(cls.status == status_filter)

        total = query.count()
        items = query.order_by(cls.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
        pages = (total + per_page - 1) // per_page if per_page else 0

        # admin 附 created_by_username
        item_dicts = []
        if is_admin:
            user_map = {u.id: u.username for u in db.query(User).all()}

        for e in items:
            d = e.to_dict()
            if is_admin:
                d["created_by_username"] = user_map.get(e.created_by, None)
            item_dicts.append(d)

        return {
            "items": item_dicts,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    @classmethod
    def get_by_id(cls, db: Session, record_id: int) -> Optional["EmailRecord"]:
        """按 id 查单条邮件记录（详情接口用）"""
        return db.query(cls).filter(cls.id == record_id).first()

    @classmethod
    def update_record(cls, db: Session, rid: int, update_dict: dict) -> "EmailRecord":
        """修改邮件主题/正文：取记录 → 更新字段 → commit → refresh

        逐字思路：
        1. 取记录，不存在 → BizException(2001)
        2. 仅更新 update_dict 中提供的字段（subject/content）
        3. commit → refresh → 返回更新后的对象
        """
        record = cls.get_by_id(db, rid)
        if not record:
            raise BizException(2001, "邮件记录不存在", 404)

        if "subject" in update_dict and update_dict["subject"] is not None:
            record.subject = update_dict["subject"]
        if "content" in update_dict and update_dict["content"] is not None:
            record.content = update_dict["content"]

        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def patch_status(cls, db: Session, rid: int, new_status: str) -> "EmailRecord":
        """修改邮件状态：取记录 → 更新 status → commit → refresh

        逐字思路：
        1. 取记录，不存在 → BizException(2001)
        2. 更新 status（generated/failed/sent）
        3. commit → refresh → 返回更新后的对象
        """
        record = cls.get_by_id(db, rid)
        if not record:
            raise BizException(2001, "邮件记录不存在", 404)

        record.status = new_status
        db.commit()
        db.refresh(record)
        return record

    @classmethod
    def batch_delete(cls, db: Session, id_list: list[int]) -> int:
        """批量删除邮件记录：按 id 列表删除 → commit → 返回删除数

        逐字思路：
        1. id_list 为空 → BizException(1001)
        2. filter(cls.id.in_(id_list)) 批量删
        3. commit → 返回删除行数
        """
        if not id_list:
            raise BizException(1001, "record_ids 不能为空", 400)

        deleted = db.query(cls).filter(cls.id.in_(id_list)).delete(synchronize_session=False)
        db.commit()
        return deleted

    @classmethod
    def delete_single(cls, db: Session, rid: int) -> bool:
        """删除单条邮件记录：取记录 → delete → commit

        逐字思路：
        1. 取记录，不存在 → BizException(2001)
        2. delete → commit → 返回 True
        """
        record = cls.get_by_id(db, rid)
        if not record:
            raise BizException(2001, "邮件记录不存在", 404)

        db.delete(record)
        db.commit()
        return True
