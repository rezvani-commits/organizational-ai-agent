import streamlit as st
import time


def render_status():
    """
    Render a minimal GPT-like processing status.

    نسخه‌ی قدیمی (انیمیشن ثابت با time.sleep). دیگه از چت اصلی صدا زده
    نمی‌شه، ولی نگهش داشتیم برای سازگاری با هر جای دیگه‌ای که شاید
    بهش وابسته باشه.
    """

    steps = [
        "جستجو در اسناد",
        "بازیابی اطلاعات مرتبط",
        "تولید پاسخ",
        "ارزیابی پاسخ"
    ]

    status_placeholder = st.empty()

    for current_step in range(len(steps)):

        html = """
        <div class="chat-status">
            <div class="chat-status-title">
                <span class="status-spinner"></span>
                <span>در حال پردازش...</span>
            </div>
            <div class="chat-status-steps">
        """

        for index, step in enumerate(steps):
            if index < current_step:
                icon = '<span class="status-check">✓</span>'
                text_color = "#AFAFAF"
            elif index == current_step:
                icon = '<span class="status-spinner-small"></span>'
                text_color = "#FFFFFF"
            else:
                icon = '<span class="status-pending"></span>'
                text_color = "#666666"

            html += f"""
                <div class="chat-status-step" style="color:{text_color};">
                    {icon}
                    <span>{step}</span>
                </div>
            """

        html += "</div></div>"

        status_placeholder.html(html)
        time.sleep(0.7)

    final_html = """
    <div class="chat-status chat-status-final">
        <div class="chat-status-title">
            <span class="status-check">✓</span>
            <span>پردازش کامل شد</span>
        </div>
    </div>
    """
    status_placeholder.html(final_html)


def render_status_live(placeholder, current_label: str, is_error: bool = False, error_message: str = ""):
    """
    نسخه‌ی «زنده»ی ویجت وضعیت - مرحله‌ی واقعی‌ای که از status_store خونده
    شده رو نمایش می‌ده. هر بار که وضعیت جدید از polling می‌رسه، این تابع
    دوباره صدا زده می‌شه (نه در حلقه‌ی خودش).

    نکته: rewrite_query و analyze_query برای *همه‌ی* مسیرها اجرا می‌شن
    (چون تا analyze_query تموم نشه، intent مشخص نیست قراره بریم سمت RAG
    یا مسیر سریع مثل greeting/calculator). به همین دلیل این دو مرحله
    همیشه به‌شکل یک خط ساده نشون داده می‌شن، نه چک‌لیست کامل - وگرنه برای
    یه "سلام" ساده هم چک‌لیست کامل RAG (با آیتم‌های pending) لحظه‌ای فلش
    می‌زد و گمراه‌کننده بود.

    چک‌لیست کامل فقط وقتی نشون داده می‌شه که واقعاً وارد مسیر RAG شدیم.
    """

    RAG_LOOP_STEPS = [
        "جستجو در اسناد", "آماده‌سازی اطلاعات مرتبط",
        "تولید پاسخ", "ارزیابی پاسخ",
    ]

    if is_error:
        html = f"""
        <div class="chat-status chat-status-error">
            <div class="chat-status-title">
                <span class="status-error-icon">⚠</span>
                <span>خطا در پردازش{': ' + error_message if error_message else ''}</span>
            </div>
        </div>
        """
        placeholder.html(html)
        return

    show_full_checklist = current_label in RAG_LOOP_STEPS
    current_index = RAG_LOOP_STEPS.index(current_label) if show_full_checklist else -1

    html = """
    <div class="chat-status">
        <div class="chat-status-title">
            <span class="status-spinner"></span>
            <span>در حال پردازش...</span>
        </div>
        <div class="chat-status-steps">
    """

    if not show_full_checklist:
        display_label = current_label if current_label else "در حال پردازش"
        html += f"""
            <div class="chat-status-step" style="color:#FFFFFF;">
                <span class="status-spinner-small"></span>
                <span>{display_label}</span>
            </div>
        """
    else:
        for index, step in enumerate(RAG_LOOP_STEPS):
            if index < current_index:
                icon = '<span class="status-check">✓</span>'
                text_color = "#AFAFAF"
            elif index == current_index:
                icon = '<span class="status-spinner-small"></span>'
                text_color = "#FFFFFF"
            else:
                icon = '<span class="status-pending"></span>'
                text_color = "#666666"
            html += f"""
                <div class="chat-status-step" style="color:{text_color};">
                    {icon}
                    <span>{step}</span>
                </div>
            """

    html += "</div></div>"
    placeholder.html(html)


def render_status_final(placeholder):
    """حالت پایانی موفق - دقیقاً همون HTML قبلی."""
    final_html = """
    <div class="chat-status chat-status-final">
        <div class="chat-status-title">
            <span class="status-check">✓</span>
            <span>پردازش کامل شد</span>
        </div>
    </div>
    """
    placeholder.html(final_html)