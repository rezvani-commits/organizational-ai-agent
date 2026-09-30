from typing import Dict, List, Optional, Tuple

from sqlalchemy.exc import IntegrityError

from back.db import get_db_session
from back.models import User


def _to_dict(user: User) -> Dict:
    return {
        "username": user.username,
        "name": user.name,
        "department": user.department,
        "role": user.role,
        "level": user.level,
        "password_hash": user.password_hash,
        "active": user.active,
    }


def get_users() -> List[Dict]:
    """لیست همه‌ی کاربران، جدیدترین‌ها اول."""
    with get_db_session() as db:
        users = db.query(User).order_by(User.created_at.desc()).all()
        return [_to_dict(u) for u in users]


def get_user_by_username(username: str) -> Optional[Dict]:
    """برای login.py - برگردوندن یک کاربر خاص (یا None اگه نبود)."""
    if not username:
        return None
    with get_db_session() as db:
        user = db.query(User).filter(User.username == username.strip()).first()
        return _to_dict(user) if user else None


def create_user(
    username: str,
    name: str,
    department: str,
    role: str,
    level: int,
    password: str,  # این‌جا از قبل هش شده (hash_password تو auth.py صداش زده)
) -> Tuple[bool, str]:
    username = (username or "").strip()

    with get_db_session() as db:
        existing = db.query(User).filter(User.username == username).first()
        if existing:
            return False, "این نام کاربری قبلاً ثبت شده است."

        user = User(
            username=username,
            name=name,
            department=department,
            role=role,
            level=level,
            password_hash=password,
            active=True,
        )
        db.add(user)

        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            return False, "این نام کاربری قبلاً ثبت شده است."

    return True, "کاربر با موفقیت ایجاد شد."


def update_user(
    username: str,
    name: str,
    department: str,
    role: str,
    level: int,
) -> Tuple[bool, str]:
    with get_db_session() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False, "کاربر پیدا نشد."

        user.name = name
        user.department = department
        user.role = role
        user.level = level

    return True, "اطلاعات کاربر به‌روزرسانی شد."


def set_user_active(username: str, active: bool) -> Tuple[bool, str]:
    with get_db_session() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False, "کاربر پیدا نشد."

        user.active = active

    return True, "وضعیت کاربر به‌روزرسانی شد."


def change_password(username: str, new_password_hash: str) -> Tuple[bool, str]:
    """اختیاری - برای صفحه‌ی «تغییر رمز عبور» که تو app.py بهش اشاره شده بود."""
    with get_db_session() as db:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False, "کاربر پیدا نشد."

        user.password_hash = new_password_hash

    return True, "رمز عبور با موفقیت تغییر کرد."
