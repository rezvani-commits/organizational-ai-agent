import streamlit as st

from components.change_password import change_password_dialog
from auth.auth import logout, is_manager


def render_sidebar(chats):
    """
    Sidebar component.

    User information is loaded from:
        st.session_state.user

    Access level 3:
        Can access user management.
    """

    # =====================================================
    # USER MENU STATE
    # =====================================================

    if "user_menu_open" not in st.session_state:
        st.session_state.user_menu_open = False

    # =====================================================
    # CURRENT USER
    # =====================================================

    user = st.session_state.get("user")

    if user is None:
        return

    # =====================================================
    # SIDEBAR
    # =====================================================

    with st.sidebar:

        # -------------------------------------------------
        # NEW CHAT
        # -------------------------------------------------

        if st.button(
            "+ گفتگوی جدید",
            use_container_width=True
        ):
            st.session_state.messages = []
            st.rerun()

        st.divider()

        # -------------------------------------------------
        # RECENT CHATS TITLE
        # -------------------------------------------------

        st.markdown(
            """
            <div class="sidebar-history-title">
                گفتگوهای اخیر
            </div>
            """,
            unsafe_allow_html=True
        )

        # -------------------------------------------------
        # RECENT CHATS
        # -------------------------------------------------

        with st.container(key="recent_history"):

            for chat in chats:

                st.markdown(
                    f"""
                    <div class="chat-item">
                        {chat}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # -------------------------------------------------
        # USER SECTION
        # -------------------------------------------------

        with st.container(key="sidebar_user_section"):

            st.divider()

            # ---------------------------------------------
            # USER BUTTON
            # ---------------------------------------------

            if st.button(
                f"👤  {user.get('name', '')}",
                key="user_profile_button",
                use_container_width=True
            ):
                st.session_state.user_menu_open = (
                    not st.session_state.user_menu_open
                )

            # ---------------------------------------------
            # USER ROLE / DEPARTMENT
            # ---------------------------------------------

            st.markdown(
                f"""
                <div class="sidebar-user-department">
                    {user.get('role', '')}
                    ·
                    {user.get('department', '')}
                </div>
                """,
                unsafe_allow_html=True
            )

            # ---------------------------------------------
            # USER MENU
            # ---------------------------------------------

            if st.session_state.user_menu_open:

                # -----------------------------------------
                # CHANGE PASSWORD
                # -----------------------------------------

                if st.button(
                    "تغییر رمز عبور",
                    key="user_change_password",
                    use_container_width=True
                ):
                    change_password_dialog(
                        user["username"]
                    )

                # -----------------------------------------
                # USER MANAGEMENT
                # LEVEL 3 ONLY
                # -----------------------------------------

                if is_manager():

                    if st.button(
                        "مدیریت کاربران",
                        key="user_management_button",
                        use_container_width=True
                    ):
                        st.switch_page(
                            "pages/user_management.py"
                        )

                # -----------------------------------------
                # LOGOUT
                # -----------------------------------------

                if st.button(
                    "خروج",
                    key="user_logout_button",
                    use_container_width=True
                ):
                    logout()

                    st.session_state.user_menu_open = False
                    st.session_state.messages = []

                    st.switch_page(
                        "pages/login.py"
                    )