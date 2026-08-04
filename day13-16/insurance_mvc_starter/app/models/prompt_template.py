"""Prompt 模板模型

【MVC 归属】Model 层（数据层）
【思路】
1. 字段：id、name、content、is_active、created_at、updated_at
2. content 存 Prompt 模板文本，含 {gender}/{age}/{vehicle_damage} 等占位符
3. is_active=True 标记当前生效模板（全表仅一条）
4. 启动时 init_default_template 自动 seed 一份默认模板兜底
5. 类方法封装操作，严格对齐 user.py / experiment.py 的写法风格

为什么 Prompt 存数据库而不写死在代码里？
  运营在前端改文案不用重新部署，模板迭代与代码发布解耦。
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base
from app.core.response import BizException

# 默认 Prompt 模板（init_default_template seed 用）
# 占位符用 {gender} 命名 → str.format 填充；JSON 示例用 {{ }} 转义为字面花括号
DEFAULT_PROMPT_CONTENT = """你是保险营销文案专家。请根据以下客户画像生成一封个性化车险营销邮件。
客户画像：性别{gender}，年龄{age}岁，{driving_license}，车龄{vehicle_age}，车辆{vehicle_damage}，年保费{annual_premium}元，{previously_insured}。
要求：语气专业有温度，突出该客户画像的痛点与利益，包含行动号召(CTA)。
仅返回严格 JSON，格式：{{"subject":"邮件主题","content":"HTML格式正文"}}"""

DEFAULT_PROMPT_NAME = "默认营销邮件模板"


class PromptTemplate(Base):
    """Prompt 模板模型：对应 prompt_templates 表"""
    __tablename__ = "prompt_templates"

    # 业务字段
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # 模板名称
    content: Mapped[str] = mapped_column(Text, nullable=False)  # Prompt 文本（含占位符）
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)  # 是否生效

    # 时间字段（用 Python 端 default=datetime.now 取本地时间，避免 SQLite UTC 偏差）
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # ===== 序列化 =====
    def to_dict(self) -> dict:
        """转字典（供接口返回复用）"""
        return {
            "id": self.id,
            "name": self.name,
            "content": self.content,
            "is_active": self.is_active,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
        }

    # ===== 类方法（对齐 user.py / experiment.py 风格：classmethod 封装操作）=====
    @classmethod
    def get_active_template(cls, db: Session) -> Optional["PromptTemplate"]:
        """获取当前生效的 Prompt 模板（is_active=True 的那条）

        全表仅一条 is_active=True，取第一条即可。
        无生效模板时返回 None，上层用 DEFAULT_PROMPT_CONTENT 兜底。
        """
        return db.query(cls).filter(cls.is_active == True).first()

    @classmethod
    def update_content(cls, db: Session, new_content: str) -> "PromptTemplate":
        """更新当前生效模板的 content 文本

        逐字思路：
        1. 取生效模板，不存在则抛异常
        2. 更新 content → commit → refresh
        3. 返回更新后的模板对象
        """
        tpl = cls.get_active_template(db)
        if not tpl:
            raise BizException(2001, "无生效的 Prompt 模板", 404)

        tpl.content = new_content
        db.commit()
        db.refresh(tpl)
        return tpl

    @classmethod
    def init_default_template(cls, db: Session) -> "PromptTemplate":
        """首次启动初始化默认 Prompt 模板

        逐字思路：
        1. 查是否已有模板记录 → 有则直接返回（幂等，不重复插入）
        2. 无记录 → 插入默认模板（is_active=True）
        3. commit → refresh 拿自增 id
        """
        existing = db.query(cls).first()
        if existing:
            return existing

        tpl = cls(
            name=DEFAULT_PROMPT_NAME,
            content=DEFAULT_PROMPT_CONTENT,
            is_active=True,
        )
        db.add(tpl)
        db.commit()
        db.refresh(tpl)
        return tpl
