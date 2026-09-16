"""
Models
------
مدل‌های SQLAlchemy برای جدول‌های users و chat_sessions.

نکته: تاریخچه‌ی خودِ پیام‌ها (متن سوال/جواب) رو LangChain's
SQLChatMessageHistory تو جدول message_store مدیریت می‌کنه (از طریق
DialogueManager) - این‌جا فقط "متادیتای" سشن (عنوان، صاحب سشن، زمان) رو
نگه می‌داریم که سبک و مستقل از LangChain باشه.
"""

import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from back.db import Base


def _new_uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    username = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    department = Column(String(128), nullable=False, default="")
    role = Column(String(128), nullable=False, default="")
    level = Column(Integer, nullable=False, default=1)  # 1=کاربر, 2=مدیر, 3=مدیر سیستم
    password_hash = Column(String(256), nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

    sessions = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=_new_uuid)
    user_username = Column(
        String(64), ForeignKey("users.username", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.datetime.utcnow,
        onupdate=datetime.datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="sessions")
