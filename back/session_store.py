"""
Session Store
-------------
لیست سشن‌های چت هر کاربر + عنوانشون رو تو Postgres نگه می‌داره (جایگزین
st.session_state.user_sessions / session_titles که با رفرش از بین می‌رفتن).

خودِ محتوای پیام‌ها (سوال/جواب) همچنان با DialogueManager (روی
message_store) مدیریت می‌شه - این‌جا فقط متادیتای سشنه.
"""

import datetime
from typing import Dict, List, Optional

from back.db import get_db_session
from back.models import ChatSession


def create_session(session_id: str, username: str, title: Optional[str] = None) -> None:
    """یک سشن جدید برای این کاربر ثبت می‌کنه (اگه از قبل نبود)."""
    with get_db_session() as db:
        existing = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if existing:
            return
        db.add(ChatSession(id=session_id, user_username=username, title=title))


def list_sessions(username: str) -> List[Dict]:
    """لیست سشن‌های یک کاربر، آخرین فعالیت اول - دقیقاً چیزی که سایدبار
    برای session_list نیاز داره."""
    with get_db_session() as db:
        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.user_username == username)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )
        return [
            {"id": s.id, "title": s.title or "گفتگوی جدید"}
            for s in sessions
        ]
def set_session_title(
    session_id: str,
    title: str,
    overwrite: bool = False
) -> None:
    """عنوان سشن را تنظیم می‌کند.
    
    پیش‌فرض فقط وقتی عنوان قبلی خالی باشد عنوان جدید را ذخیره می‌کند.
    """

    # اگر عنوان None یا خالی بود، کاری انجام نده
    if not title:
        return

    title = str(title).strip()

    if not title:
        return

    # محدود کردن عنوان به ۵۰ کاراکتر
    if len(title) > 50:
        title = title[:50] + "..."

    with get_db_session() as db:
        session = (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )

        if not session:
            return

        if overwrite or not session.title:
            session.title = title

def touch_session(session_id: str) -> None:
    """زمان آخرین فعالیت سشن رو آپدیت می‌کنه (برای مرتب‌سازی بر اساس
    جدیدترین فعالیت تو سایدبار)."""
    with get_db_session() as db:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            session.updated_at = datetime.datetime.utcnow()


def delete_session(session_id: str) -> None:
    with get_db_session() as db:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if session:
            db.delete(session)
