# import streamlit as st
# from components.change_password import change_password_dialog
# from auth.auth import logout, is_manager, get_current_user


# def render_sidebar(sessions, current_session_id):
#     """
#     Sidebar component with list of chat sessions.

#     Args:
#         sessions: لیست دیکشنری‌های {'id': session_id, 'title': title}
#         current_session_id: شناسه سِشن فعال

#     Returns:
#         session_id اگر کاربر روی یک سِشن کلیک کند، در غیر این صورت None
#     """

#     # =====================================================
#     # USER MENU STATE
#     # =====================================================

#     if "user_menu_open" not in st.session_state:
#         st.session_state.user_menu_open = False

#     # =====================================================
#     # CURRENT USER
#     # =====================================================

#     user = get_current_user()

#     if user is None:
#         return None  # <-- باید None برگرداند

#     # =====================================================
#     # SIDEBAR
#     # =====================================================

#     with st.sidebar:

#         # -------------------------------------------------
#         # NEW CHAT BUTTON
#         # -------------------------------------------------

#         if st.button(
#             "➕ گفتگوی جدید",
#             use_container_width=True
#         ):
#             import uuid
#             from back.session_store import create_session

#             new_session_id = str(uuid.uuid4())

#             # ثبت سشن جدید در دیتابیس - بدون این خط، عنوان و
#             # آخرین فعالیت این سشن هیچ‌وقت ذخیره نمی‌شه چون
#             # ردیفی توی جدول ChatSession براش وجود نداره
#             create_session(new_session_id, user["username"])

#             # تغییر به سِشن جدید
#             st.session_state.current_session_id = new_session_id
#             st.session_state.messages = []

#             # به‌روزرسانی کوکی
#             from components.cookie_manager import get_cookie_manager
#             cookie_manager = get_cookie_manager()
#             cookie_manager.set("current_session_id", new_session_id)

#             st.rerun()

#         st.divider()

#         # -------------------------------------------------
#         # SESSIONS TITLE
#         # -------------------------------------------------

#         st.markdown(
#             """
#             <div class="sidebar-history-title">
#                 💬 گفتگوهای اخیر
#             </div>
#             """,
#             unsafe_allow_html=True
#         )

#         # -------------------------------------------------
#         # LIST OF SESSIONS
#         # -------------------------------------------------

#         # متغیر برای نگهداری سِشن انتخاب شده
#         selected_session_id = None

#         with st.container(key="session_list"):

#             if sessions:
#                 for session in sessions:
#                     session_id = session["id"]
#                     title = session["title"]

#                     # مشخص کردن سِشن فعال
#                     is_active = (session_id == current_session_id)

#                     # استایل متفاوت برای سِشن فعال
#                     if is_active:
#                         st.markdown(
#                             f"""
#                             <div class="chat-item active-session">
#                                 ▶️ {title}
#                             </div>
#                             """,
#                             unsafe_allow_html=True
#                         )
#                     else:
#                         # دکمه برای انتخاب سِشن
#                         if st.button(
#                             f"💬 {title}",
#                             key=f"session_{session_id}",
#                             use_container_width=True
#                         ):
#                             selected_session_id = session_id  # <-- ذخیره در متغیر
#             else:
#                 st.info("📭 هیچ گفتگویی وجود ندارد.")

#         # -------------------------------------------------
#         # USER SECTION
#         # -------------------------------------------------

#         with st.container(key="sidebar_user_section"):

#             st.divider()

#             # ---------------------------------------------
#             # USER BUTTON
#             # ---------------------------------------------

#             if st.button(
#                 f"👤  {user.get('name', '')}",
#                 key="user_profile_button",
#                 use_container_width=True
#             ):
#                 st.session_state.user_menu_open = (
#                     not st.session_state.user_menu_open
#                 )

#             # ---------------------------------------------
#             # USER ROLE / DEPARTMENT
#             # ---------------------------------------------

#             st.markdown(
#                 f"""
#                 <div class="sidebar-user-department">
#                     {user.get('role', '')}
#                     ·
#                     {user.get('department', '')}
#                 </div>
#                 """,
#                 unsafe_allow_html=True
#             )

#             # ---------------------------------------------
#             # USER MENU
#             # ---------------------------------------------

#             if st.session_state.user_menu_open:

#                 # -----------------------------------------
#                 # CHANGE PASSWORD
#                 # -----------------------------------------

#                 if st.button(
#                     "🔑 تغییر رمز عبور",
#                     key="user_change_password",
#                     use_container_width=True
#                 ):
#                     change_password_dialog(
#                         user["username"]
#                     )

#                 # -----------------------------------------
#                 # USER MANAGEMENT (LEVEL 3 ONLY)
#                 # -----------------------------------------

#                 if is_manager():

#                     if st.button(
#                         "👥 مدیریت کاربران",
#                         key="user_management_button",
#                         use_container_width=True
#                     ):
#                         st.switch_page(
#                             "app_pages/user_management.py"
#                         )

#                 # -----------------------------------------
#                 # LOGOUT
#                 # -----------------------------------------

#                 if st.button(
#                     "🚪 خروج",
#                     key="user_logout_button",
#                     use_container_width=True
#                 ):
#                     logout()

#                     st.session_state.user_menu_open = False
#                     st.session_state.messages = []

#                     st.switch_page(
#                         "app_pages/login.py"
#                     )

#     # برگرداندن سِشن انتخاب شده
#     return selected_session_id  # <-- اینجا باید برگردانده شود

import streamlit as st
from components.change_password import change_password_dialog
from auth.auth import logout, is_manager, get_current_user


def render_sidebar(sessions=None, current_session_id=None):
    """
    Sidebar component with list of chat sessions.

    Args:
        sessions: لیست دیکشنری‌های {'id': session_id, 'title': title}
        current_session_id: شناسه سِشن فعال

    Returns:
        session_id اگر کاربر روی یک سِشن کلیک کند، در غیر این صورت None
    """

    # =====================================================
    # USER MENU STATE
    # =====================================================

    if "user_menu_open" not in st.session_state:
        st.session_state.user_menu_open = False

    # =====================================================
    # CURRENT USER
    # =====================================================

    user = get_current_user()

    if user is None:
        return None  # <-- باید None برگرداند

    # =====================================================
    # SIDEBAR
    # =====================================================

    with st.sidebar:

        # -------------------------------------------------
        # NEW CHAT BUTTON
        # -------------------------------------------------

        if st.button(
            "➕ گفتگوی جدید",
            use_container_width=True
        ):
            import uuid
            from back.session_store import create_session

            new_session_id = str(uuid.uuid4())

            # ثبت سشن جدید در دیتابیس - بدون این خط، عنوان و
            # آخرین فعالیت این سشن هیچ‌وقت ذخیره نمی‌شه چون
            # ردیفی توی جدول ChatSession براش وجود نداره
            create_session(new_session_id, user["username"])

            # تغییر به سِشن جدید
            st.session_state.current_session_id = new_session_id
            st.session_state.messages = []

            # به‌روزرسانی کوکی
            from components.cookie_manager import get_cookie_manager
            cookie_manager = get_cookie_manager()
            cookie_manager.set("current_session_id", new_session_id)

            st.rerun()

        st.divider()

        # -------------------------------------------------
        # SESSIONS TITLE
        # -------------------------------------------------

        st.markdown(
            """
            <div class="sidebar-history-title">
                💬 گفتگوهای اخیر
            </div>
            """,
            unsafe_allow_html=True
        )

        # -------------------------------------------------
        # LIST OF SESSIONS
        # -------------------------------------------------

        # متغیر برای نگهداری سِشن انتخاب شده
        selected_session_id = None

        with st.container(key="session_list"):

            if sessions:
                for session in sessions:
                    session_id = session["id"]
                    title = session["title"]

                    # مشخص کردن سِشن فعال
                    is_active = (session_id == current_session_id)

                    select_col, delete_col = st.columns([5, 1])

                    with select_col:
                        # استایل متفاوت برای سِشن فعال
                        if is_active:
                            st.markdown(
                                f"""
                                <div class="chat-item active-session">
                                    ▶️ {title}
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                        else:
                            # دکمه برای انتخاب سِشن
                            if st.button(
                                f"💬 {title}",
                                key=f"session_{session_id}",
                                use_container_width=True
                            ):
                                selected_session_id = session_id  # <-- ذخیره در متغیر

                    with delete_col:
                        # دکمه‌ی حذف سِشن
                        if st.button(
                            "🗑️",
                            key=f"delete_{session_id}",
                            use_container_width=True
                        ):
                            from back.session_store import delete_session
                            delete_session(session_id)

                            # اگه سشنی که حذف شد، همون سشن فعلی/بازه بود،
                            # باید state و کوکی رو هم پاک کنیم تا دفعه‌ی
                            # بعد یک سشن جدید و سالم ساخته بشه (وگرنه اپ
                            # سعی می‌کنه یه سشن حذف‌شده رو لود کنه)
                            if session_id == current_session_id:
                                st.session_state.pop("current_session_id", None)
                                st.session_state.messages = []

                                from components.cookie_manager import get_cookie_manager
                                cookie_manager = get_cookie_manager()
                                cookie_manager.delete("current_session_id")

                            st.rerun()
            else:
                st.info("📭 هیچ گفتگویی وجود ندارد.")

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
                    "🔑 تغییر رمز عبور",
                    key="user_change_password",
                    use_container_width=True
                ):
                    change_password_dialog(
                        user["username"]
                    )

                # -----------------------------------------
                # USER MANAGEMENT (LEVEL 3 ONLY)
                # -----------------------------------------

                if is_manager():

                    if st.button(
                        "👥 مدیریت کاربران",
                        key="user_management_button",
                        use_container_width=True
                    ):
                        st.switch_page(
                            "app_pages/user_management.py"
                        )

                # -----------------------------------------
                # LOGOUT
                # -----------------------------------------

                if st.button(
                    "🚪 خروج",
                    key="user_logout_button",
                    use_container_width=True
                ):
                    logout()

                    st.session_state.user_menu_open = False
                    st.session_state.messages = []

                    st.switch_page(
                        "app_pages/login.py"
                    )

    # برگرداندن سِشن انتخاب شده
    return selected_session_id  # <-- اینجا باید برگردانده شود