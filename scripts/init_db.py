"""
اسکریپت راه‌اندازی اولیه‌ی دیتابیس.

اجرا از ریشه‌ی پروژه:
    python -m scripts.init_db

کارهایی که انجام می‌ده:
  ۱) اتصال خام به Postgres رو تست می‌کنه.
  ۲) جدول‌های users و chat_sessions رو می‌سازه (اگه از قبل نبودن).
  ۳) اگه هیچ کاربری تو دیتابیس نبود، یک کاربر «مدیر سیستم» اولیه با
     نام کاربری/رمز پیش‌فرض می‌سازه تا بشه اولین بار وارد شد.
"""

import sys

from sqlalchemy import text

from back.db import engine, init_db
from auth.auth import hash_password
from auth.users import get_users, create_user

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "ChangeMe123!"  # حتماً بعد از اولین ورود عوضش کن


def main() -> None:
    print("[۱/۳] در حال تست اتصال خام به Postgres...")
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("      ✅ اتصال برقرار شد.")
    except Exception as exc:
        print(f"      ❌ اتصال شکست خورد: {exc}")
        print("      -> Config.DB_URL رو چک کن (یوزر/پسورد/هاست/پورت/دیتابیس).")
        sys.exit(1)

    print("[۲/۳] در حال ساخت جدول‌ها (اگه از قبل نبودن)...")
    try:
        init_db()
        print("      ✅ جدول‌های users و chat_sessions آماده‌ن.")
    except Exception as exc:
        print(f"      ❌ ساخت جدول‌ها شکست خورد: {exc}")
        sys.exit(1)

    print("[۳/۳] بررسی وجود کاربر ادمین اولیه...")
    try:
        if get_users():
            print("      ℹ️ دیتابیس از قبل کاربر داره - کاربر پیش‌فرض ساخته نشد.")
        else:
            success, message = create_user(
                username=DEFAULT_ADMIN_USERNAME,
                name="مدیر سیستم",
                department="فناوری اطلاعات",
                role="مدیر سیستم",
                level=3,
                password=hash_password(DEFAULT_ADMIN_PASSWORD),
            )
            if success:
                print(f"      ✅ کاربر ادمین اولیه ساخته شد.")
                print(f"         نام کاربری: {DEFAULT_ADMIN_USERNAME}")
                print(f"         رمز عبور:   {DEFAULT_ADMIN_PASSWORD}")
                print("         ⚠️  حتماً بعد از اولین ورود این رمز رو عوض کن.")
            else:
                print(f"      ❌ ساخت کاربر ادمین شکست خورد: {message}")
    except Exception as exc:
        print(f"      ❌ بررسی/ساخت کاربر ادمین شکست خورد: {exc}")
        sys.exit(1)

    print("\n🎉 دیتابیس آماده‌ی استفاده است.")


if __name__ == "__main__":
    main()
