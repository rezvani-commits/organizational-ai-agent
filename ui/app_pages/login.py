import streamlit as st

from auth.auth import login
from styles.style import load_css


load_css(show_sidebar=False)

# -----------------------
# Session State
# -----------------------

if "is_authenticated" not in st.session_state:
    st.session_state.is_authenticated = False


# -----------------------
# Login Container
# -----------------------
st.html(
    """
    <div class="login-header">

        <div class="login-title">
            دستیار هوشمند
        </div>

        <div class="login-subtitle">
            برای ادامه وارد حساب کاربری خود شوید
        </div>

    </div>
    """
)
st.markdown(
    """
    <style>
    [data-testid="stSidebar"] {
        display: none !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)
# -----------------------
# Login Form
# -----------------------

left, center, right = st.columns([0.8, 1, 0.8])
with center:

    with st.form("login_form"):

        username = st.text_input(
            "نام کاربری",
            placeholder="نام کاربری خود را وارد کنید",
            autocomplete="off"
        )

        password = st.text_input(
            "رمز عبور",
            type="password",
            placeholder="رمز عبور خود را وارد کنید",
            autocomplete="new-password"
        )

        submitted = st.form_submit_button(
            "ورود",
            use_container_width=True
        )


# -----------------------
# Authentication
# -----------------------

if submitted:

    if login(username, password):

        st.session_state.is_authenticated = True
        st.switch_page("app_pages/chat.py")

    else:

        st.error(
            "نام کاربری یا رمز عبور اشتباه است."
        )