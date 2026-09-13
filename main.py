"""
نقطه‌ی ورود اصلی پروژه.

این فایل دیگه خودش منطق تست RAG رو اجرا نمی‌کنه (اون رفته توی tst.py) -
فقط مسئولشه که اپلیکیشن Streamlit (ui/app.py) رو با تنظیمات درست راه بندازه.

طوری نوشته شده که از هر جایی اجراش کنی (چه از ریشه‌ی پروژه، چه از یه
مسیر دیگه) درست کار کنه، چون ریشه‌ی پروژه رو خودش محاسبه و به PYTHONPATH
اضافه می‌کنه - دیگه نیازی نیست دستی $env:PYTHONPATH بزنی.

اجرا:
    python main.py
"""

import os
import sys
import subprocess

# آفلاین نگه‌داشتن HuggingFace/Transformers (برای embedding محلی)
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
APP_PATH = os.path.join(PROJECT_ROOT, "ui", "app.py")

# نکته مهم: main.py فقط یک launcher است که ui/app.py را در یک
# ساب‌پروسه‌ی جداگانه اجرا می‌کند. هر منطق مربوط به navigation
# (مثل st.navigation / st.Page) باید داخل خودِ ui/app.py نوشته شود،
# نه اینجا - چون این فایل هیچ‌وقت توسط Streamlit به‌عنوان صفحه
# رندر نمی‌شود و import کردن streamlit در اینجا هم لازم نیست.


def main():

    # ---------------------------------------------------------------
    # اعتبارسنجی Config قبل از راه‌اندازی UI (مثل GROQ_API_KEY و مسیرها)
    # ---------------------------------------------------------------
    sys.path.insert(0, PROJECT_ROOT)  # تا خودِ این پروسه هم back رو پیدا کنه
    from back.config import Config
    Config.validate()

    if not os.path.exists(APP_PATH):
        print(f"❌ فایل اپ پیدا نشد: {APP_PATH}")
        sys.exit(1)

    # ---------------------------------------------------------------
    # ست کردن PYTHONPATH برای ساب‌پروسه‌ی Streamlit (تا ui/app.py هم
    # بتونه back.* رو ایمپورت کنه، حتی از راه دور)
    # ---------------------------------------------------------------
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = PROJECT_ROOT + (os.pathsep + existing if existing else "")

    print("🚀 در حال راه‌اندازی اپلیکیشن Streamlit...")
    print(f"📁 ریشه‌ی پروژه: {PROJECT_ROOT}")
    print(f"📄 اپ: {APP_PATH}")

    try:
        subprocess.run(
            [sys.executable, "-m", "streamlit", "run", APP_PATH],
            cwd=PROJECT_ROOT,
            env=env,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ اجرای Streamlit با خطا متوقف شد (کد {e.returncode}).")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n👋 متوقف شد.")


if __name__ == "__main__":
    main()