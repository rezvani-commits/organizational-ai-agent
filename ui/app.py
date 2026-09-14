import os
import time
import streamlit as st

from styles.style import load_css


# =========================================================
# PAGE CONFIG (فقط یک‌بار، فقط همین‌جا)
# =========================================================
st.set_page_config(
    page_title="دستیار هوشمند",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# HIDE STREAMLIT DEFAULT UI
# =========================================================
st.markdown(
    """
    <style>
    #MainMenu,
    header,
    footer,
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    .block-container {
        padding-top: 0 !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# =========================================================
# SESSION STATE
# =========================================================
if "loading_done" not in st.session_state:
    st.session_state.loading_done = False

if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False


# =========================================================
# LOADING PAGE (فقط یک بار)
# =========================================================
if not st.session_state.loading_done:

    st.markdown(
        """
        <style>
        .loading-page {
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            direction: rtl;
            background: #212121;
        }

        .loading-container {
            text-align: center;
        }

        .loading-logo {
            width: 72px;
            height: 72px;
            margin: 0 auto 24px;
            border-radius: 20px;
            background: #2F2F2F;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
        }

        .loading-title {
            color: #FFFFFF;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
        }

        .loading-subtitle {
            color: #A0A0A0;
            font-size: 14px;
            margin-bottom: 28px;
        }

        .spinner {
            width: 32px;
            height: 32px;
            margin: 0 auto;
            border: 3px solid #3A3A3A;
            border-top: 3px solid #3B82F6;
            border-radius: 50%;
            animation: spin 0.9s linear infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        </style>

        <div class="loading-page">
            <div class="loading-container">
                <div class="loading-logo">🤖</div>
                <div class="loading-title">در حال آماده‌سازی دستیار</div>
                <div class="loading-subtitle">لطفاً چند لحظه صبر کنید...</div>
                <div class="spinner"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    time.sleep(2)

    st.session_state.loading_done = True
    st.rerun()
    st.stop()


# =========================================================
# NAVIGATION (تنها جایی که صفحات تعریف می‌شوند)
# =========================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(CURRENT_DIR, "app_pages")

pages = [
    st.Page(os.path.join(PAGES_DIR, "login.py"), title="ورود"),
    st.Page(os.path.join(PAGES_DIR, "chat.py"), title="گفتگو"),
    st.Page(os.path.join(PAGES_DIR, "user_management.py"), title="مدیریت کاربران"),
    ]

pg = st.navigation(pages, position="hidden")
pg.run()