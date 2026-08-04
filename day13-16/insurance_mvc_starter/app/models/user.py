from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, Session
from app.core.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user")  # admin / user
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    @classmethod #查用户不需要有用户实例，可以直接调用类方法调用，逻辑上的优化
    def find_by_username(cls, db: Session, username: str) -> Optional["User"]:
        """按用户名查用户（登录/注册查重用）"""
        return db.query(cls).filter(cls.username == username).first()

    @classmethod
    def create(cls, db: Session, username: str, password_hash: str, role: str = "user") -> "User":
        """创建用户：add → commit → refresh 拿自增 id"""
        user = cls(username=username, password_hash=password_hash, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def modify(self, db: Session, data: str, type: str) -> "User":
        if type == "username":
            self.username = data
            db.commit()
            db.refresh(self)
            return self
        elif type == "password":
            self.password_hash = data
            db.commit()
            db.refresh(self)
            return self

    @classmethod
    def all_users(cls, db: Session) -> list["User"]:
        """查所有用户（admin 接口用，按 id 升序）"""
        return db.query(cls).order_by(cls.id).all()
