"""
Auth
----
توابع احراز هویت که login.py و user_management.py مستقیماً صداشون
می‌زنن: hash_password, login, is_manager.

از bcrypt استفاده می‌کنیم (نه هش ساده‌ی sha256 و امثالش) چون مخصوص
پسورده: salt خودکار داره و در برابر brute-force کند طراحی شده.
"""

from typing import Optional, Dict

import bcrypt
import streamlit as st

from auth.users import get_user_by_username


# ------------------------------------------------------------------
# هش کردن / تطبیق رمز عبور
# ------------------------------------------------------------------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, AttributeError):
        # اگه password_hash خراب/خالی بود، به‌جای کرش کردن، false برگردون
        return False


# ------------------------------------------------------------------
# ورود
# ------------------------------------------------------------------
def login(username: str, password: str) -> bool:
    username = (username or "").strip()
    if not username or not password:
        return False

    user = get_user_by_username(username)
    if not user:
        return False

    if not user.get("active", True):
        return False

    if not _verify_password(password, user["password_hash"]):
        return False

    # اطلاعات کاربر لاگین‌شده رو تو session_state نگه می‌داریم تا بقیه‌ی
    # صفحات (is_manager، نمایش نام کاربر، فیلتر کردن سشن‌ها بر اساس
    # صاحبشون) بهش دسترسی داشته باشن.
    st.session_state.current_user = {
        "username": user["username"],
        "name": user["name"],
        "department": user["department"],
        "role": user["role"],
        "level": user["level"],
    }
    return True


def logout() -> None:
    for key in ("is_authenticated", "current_user"):
        st.session_state.pop(key, None)


# ------------------------------------------------------------------
# دسترسی‌ها
# ------------------------------------------------------------------
def get_current_user() -> Optional[Dict]:
    return st.session_state.get("current_user")


def is_manager() -> bool:
    """سطح ۲ (مدیر) یا بالاتر."""
    user = get_current_user()
    return bool(user) and user.get("level", 1) >= 2


def is_admin() -> bool:
    """سطح ۳ (مدیر سیستم)."""
    user = get_current_user()
    return bool(user) and user.get("level", 1) >= 3
def change_password(
    username: str,
    old_password: str,
    new_password: str,
) -> tuple[bool, str]:
    username = (username or "").strip()

    if not username or not old_password or not new_password:
        return False, "همه فیلدها الزامی هستند."

    if len(new_password) < 6:
        return False, "رمز عبور جدید باید حداقل ۶ کاراکتر باشد."

    user = get_user_by_username(username)

    if not user:
        return False, "کاربر پیدا نشد."

    if not user.get("active", True):
        return False, "حساب کاربری غیرفعال است."

    if not _verify_password(old_password, user["password_hash"]):
        return False, "رمز عبور فعلی اشتباه است."

    new_password_hash = hash_password(new_password)

    from auth.users import change_password as db_change_password

    return db_change_password(
        username=username,
        new_password_hash=new_password_hash,
    )