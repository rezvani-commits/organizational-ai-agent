"""
Cookie Manager (shared)
------------------------
یک نمونه‌ی مشترک از CookieManager برای کل اپ.

چرا این فایل لازم بود:
ساختن `stx.CookieManager()` جدید هر جا که لازم شد (توی chat.py برای
خوندن، توی sidebar.py برای ست‌کردن) باعث می‌شه چندتا نمونه‌ی جدا از
کامپوننت رندر بشه که هر کدوم برای خودشون باید یک دور رفت‌وبرگشت با
مرورگر انجام بدن تا مقدار کوکی رو برگردونن. این هم کند می‌کنه، هم باعث
می‌شه مقدار کوکی توی بعضی رران‌ها هنوز None باشه (چون اون نمونه‌ی خاص
هنوز sync نشده) - که دقیقاً همون دلیلیه که هر رفرش یک سشن خالی جدید
ساخته می‌شد.

با یک نمونه‌ی مشترک (که در session_state کش می‌شه) این مشکل حل می‌شه.
"""

import streamlit as st
import extra_streamlit_components as stx


def get_cookie_manager():
    """نمونه‌ی مشترک CookieManager رو برمی‌گردونه (یک‌بار می‌سازه، بقیه‌ی
    اوقات همون رو reuse می‌کنه)."""
    if "cookie_manager" not in st.session_state:
        st.session_state.cookie_manager = stx.CookieManager(
            key="app_cookie_manager"
        )
    return st.session_state.cookie_manager
