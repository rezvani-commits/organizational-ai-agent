import streamlit as st
from components.change_password import change_password_dialog
from auth.auth import logout, is_manager


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
    
    user = st.session_state.get("user")
    
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
            # ایجاد سِشن جدید
            import uuid
            new_session_id = str(uuid.uuid4())
            
            # اضافه کردن به لیست سِشن‌ها
            st.session_state.user_sessions.append(new_session_id)
            
            # تغییر به سِشن جدید
            st.session_state.current_session_id = new_session_id
            st.session_state.messages = []
            
            # به‌روزرسانی کوکی
            from extra_streamlit_components import CookieManager
            cookie_manager = CookieManager()
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