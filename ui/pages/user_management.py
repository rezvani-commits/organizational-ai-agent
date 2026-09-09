import streamlit as st

from auth.auth import is_manager, hash_password
from auth.users import (
    get_users,
    create_user,
    update_user,
    set_user_active,
)
from components.sidebar import render_sidebar
from styles.style import load_css


# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(
    page_title="مدیریت کاربران",
    page_icon="👥",
    layout="wide",
)

load_css()


# =========================================================
# SIDEBAR
# =========================================================

chats = st.session_state.get(
    "recent_chats",
    [
        "شرایط دریافت مجوز نیروگاه",
        "تعرفه‌های صنعتی",
        "قوانین اتصال به شبکه",
    ],
)

render_sidebar(chats)


# =========================================================
# ACCESS CONTROL
# =========================================================

if not st.session_state.get("is_authenticated", False):
    st.error("ابتدا وارد حساب کاربری شوید.")
    st.stop()

if not is_manager():
    st.error("شما دسترسی لازم برای مشاهده این صفحه را ندارید.")
    st.stop()


# =========================================================
# SESSION STATE
# =========================================================

if "editing_user" not in st.session_state:
    st.session_state.editing_user = None

if "show_add_user" not in st.session_state:
    st.session_state.show_add_user = False

if "search_query" not in st.session_state:
    st.session_state.search_query = ""


# =========================================================
# HELPERS
# =========================================================

def get_level_name(level):
    levels = {
        1: "کاربر",
        2: "مدیر",
        3: "مدیر سیستم",
    }
    return levels.get(level, f"سطح {level}")


def clear_form_keys(keys):
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]


# =========================================================
# PAGE WRAPPER
# =========================================================

with st.container(key="admin_page"):

    # =====================================================
    # HEADER
    # =====================================================

    st.markdown(
        """
        <div class="admin-header-title">
            مدیریت کاربران
        </div>

        <div class="admin-header-subtitle">
            ایجاد، ویرایش و مدیریت کاربران سامانه
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write("")

    # =====================================================
    # ADD USER BUTTON
    # =====================================================

    top_left, top_right = st.columns([7, 1])

    with top_right:
        button_label = (
            "بستن"
            if st.session_state.show_add_user
            else "افزودن کاربر"
        )

        if st.button(
            button_label,
            key="add_user_button",
            use_container_width=True,
        ):
            st.session_state.show_add_user = (
                not st.session_state.show_add_user
            )

            if st.session_state.show_add_user:
                st.session_state.editing_user = None

            st.rerun()

    # =====================================================
    # ADD USER FORM
    # =====================================================

    if st.session_state.show_add_user:

        with st.container(key="admin_add_form"):

            st.markdown(
                """
                <div class="admin-form-title">
                    افزودن کاربر جدید
                </div>

                <div class="admin-form-subtitle">
                    اطلاعات کاربر جدید را وارد کنید.
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")

            with st.form("add_user_form", clear_on_submit=False):

                col1, col2 = st.columns(2)

                with col1:
                    username = st.text_input(
                        "نام کاربری",
                        placeholder="مثلاً ali123",
                        key="new_username",
                    )

                    name = st.text_input(
                        "نام و نام خانوادگی",
                        placeholder="نام کاربر",
                        key="new_name",
                    )

                    department = st.text_input(
                        "واحد سازمانی",
                        placeholder="مثلاً معاونت منابع انسانی",
                        key="new_department",
                    )

                with col2:
                    role = st.text_input(
                        "سمت",
                        placeholder="مثلاً کارشناس",
                        key="new_role",
                    )

                    level = st.selectbox(
                        "سطح دسترسی",
                        options=[1, 2, 3],
                        format_func=get_level_name,
                        key="new_level",
                    )

                    password = st.text_input(
                        "رمز عبور",
                        type="password",
                        placeholder="حداقل ۸ کاراکتر",
                        key="new_password",
                    )

                st.write("")

                submit_col, cancel_col = st.columns([1, 1])

                with submit_col:
                    submitted = st.form_submit_button(
                        "ایجاد کاربر",
                        use_container_width=True,
                    )

                with cancel_col:
                    cancel = st.form_submit_button(
                        "انصراف",
                        use_container_width=True,
                    )

                if cancel:
                    st.session_state.show_add_user = False

                    clear_form_keys(
                        [
                            "new_username",
                            "new_name",
                            "new_department",
                            "new_role",
                            "new_level",
                            "new_password",
                        ]
                    )

                    st.rerun()

                if submitted:
                    username = username.strip()
                    name = name.strip()
                    department = department.strip()
                    role = role.strip()

                    if not username:
                        st.error("نام کاربری الزامی است.")

                    elif len(username) < 3:
                        st.error(
                            "نام کاربری باید حداقل ۳ کاراکتر باشد."
                        )

                    elif not name:
                        st.error(
                            "نام و نام خانوادگی الزامی است."
                        )

                    elif not department:
                        st.error(
                            "واحد سازمانی الزامی است."
                        )

                    elif not role:
                        st.error("سمت کاربر الزامی است.")

                    elif not password:
                        st.error("رمز عبور الزامی است.")

                    elif len(password) < 8:
                        st.error(
                            "رمز عبور باید حداقل ۸ کاراکتر باشد."
                        )

                    else:
                        hashed_password = hash_password(password)

                        success, message = create_user(
                            username=username,
                            name=name,
                            department=department,
                            role=role,
                            level=level,
                            password=hashed_password,
                        )

                        if success:
                            st.success(
                                message or
                                "کاربر با موفقیت ایجاد شد."
                            )

                            st.session_state.show_add_user = False

                            clear_form_keys(
                                [
                                    "new_username",
                                    "new_name",
                                    "new_department",
                                    "new_role",
                                    "new_level",
                                    "new_password",
                                ]
                            )

                            st.rerun()

                        else:
                            st.error(
                                message or
                                "ایجاد کاربر انجام نشد."
                            )

    # =====================================================
    # STATISTICS
    # =====================================================

    users = get_users()

    total_users = len(users)

    active_users = sum(
        1
        for user in users
        if user.get("active", True)
    )

    inactive_users = total_users - active_users

    admin_users = sum(
        1
        for user in users
        if user.get("level", 1) == 3
    )

    with st.container(key="admin_stats"):

        stat1, stat2, stat3, stat4 = st.columns(4)

        with stat1:
            st.markdown(
                f"""
                <div class="admin-stat-card">
                    <div class="admin-stat-label">
                        کل کاربران
                    </div>
                    <div class="admin-stat-value">
                        {total_users}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with stat2:
            st.markdown(
                f"""
                <div class="admin-stat-card">
                    <div class="admin-stat-label">
                        کاربران فعال
                    </div>
                    <div class="admin-stat-value">
                        {active_users}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with stat3:
            st.markdown(
                f"""
                <div class="admin-stat-card">
                    <div class="admin-stat-label">
                        کاربران غیرفعال
                    </div>
                    <div class="admin-stat-value">
                        {inactive_users}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with stat4:
            st.markdown(
                f"""
                <div class="admin-stat-card">
                    <div class="admin-stat-label">
                        مدیران سیستم
                    </div>
                    <div class="admin-stat-value">
                        {admin_users}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # =====================================================
    # USERS SECTION
    # =====================================================

    with st.container(key="admin_user_section"):

        st.markdown(
            """
            <div class="admin-section-title">
                کاربران سامانه
            </div>

            <div class="admin-section-subtitle">
                مشاهده و مدیریت حساب‌های کاربری
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")

        search_query = st.text_input(
            "جستجوی کاربر",
            placeholder="نام، نام کاربری یا واحد سازمانی...",
            key="search_query",
        )

        search_query = search_query.strip().lower()

        # =================================================
        # FILTER
        # =================================================

        filtered_users = []

        for user in users:
            searchable_text = " ".join(
                [
                    str(user.get("username", "")),
                    str(user.get("name", "")),
                    str(user.get("department", "")),
                    str(user.get("role", "")),
                ]
            ).lower()

            if (
                not search_query
                or search_query in searchable_text
            ):
                filtered_users.append(user)

        # =================================================
        # USERS LIST
        # =================================================

        with st.container(key="admin_users_list"):

            if not filtered_users:

                st.markdown(
                    """
                    <div class="admin-empty-state">
                        <div class="admin-empty-title">
                            کاربری پیدا نشد
                        </div>

                        <div class="admin-empty-subtitle">
                            نتیجه‌ای مطابق جستجوی شما وجود ندارد.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                for user in filtered_users:

                    username = user.get("username", "")
                    name = user.get("name", "بدون نام")
                    department = user.get("department", "بدون واحد")
                    role = user.get("role", "بدون سمت")
                    level = user.get("level", 1)
                    active = user.get("active", True)

                    # =============================================
                    # USER CARD
                    # =============================================

                    with st.container(key=f"admin_user_{username}"):

                        # -----------------------------------------
                        # MAIN ROW
                        # -----------------------------------------

                        info_col, status_col, action_col = st.columns(
                            [6, 1.2, 2.2]
                        )

                        # -----------------------------------------
                        # USER INFO
                        # -----------------------------------------

                        with info_col:

                            (
                                user_name_col,
                                username_col,
                                department_col,
                                role_col,
                                level_col,
                            ) = st.columns(
                                [1.25, 1, 1.25, 0.9, 1]
                            )

                            with user_name_col:
                                st.markdown(
                                    f"""
                                    <div class="admin-user-info">
                                        <div class="admin-user-name">
                                            {name}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            with username_col:
                                st.markdown(
                                    f"""
                                    <div class="admin-user-info">
                                        <div class="admin-user-label">
                                            نام کاربری
                                        </div>
                                        <div class="admin-user-username">
                                            @{username}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            with department_col:
                                st.markdown(
                                    f"""
                                    <div class="admin-user-info">
                                        <div class="admin-user-label">
                                            واحد سازمانی
                                        </div>
                                        <div class="admin-user-detail">
                                            {department}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            with role_col:
                                st.markdown(
                                    f"""
                                    <div class="admin-user-info">
                                        <div class="admin-user-label">
                                            سمت
                                        </div>
                                        <div class="admin-user-detail">
                                            {role}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                            with level_col:
                                st.markdown(
                                    f"""
                                    <div class="admin-user-info">
                                        <div class="admin-user-label">
                                            سطح دسترسی
                                        </div>
                                        <div class="admin-user-level">
                                            {get_level_name(level)}
                                        </div>
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                        # -----------------------------------------
                        # STATUS
                        # -----------------------------------------

                        with status_col:

                            status_class = (
                                "admin-status admin-status-active"
                                if active
                                else
                                "admin-status admin-status-inactive"
                            )

                            status_text = (
                                "فعال"
                                if active
                                else
                                "غیرفعال"
                            )

                            st.markdown(
                                f"""
                                <div class="{status_class}">
                                    {status_text}
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )

                        # -----------------------------------------
                        # ACTIONS
                        # -----------------------------------------

                        with action_col:

                            edit_col, toggle_col = st.columns(2)

                            with edit_col:

                                if st.button(
                                    "ویرایش",
                                    key=f"edit_{username}",
                                    use_container_width=True,
                                ):
                                    st.session_state.editing_user = username
                                    st.session_state.show_add_user = False
                                    st.rerun()

                            with toggle_col:

                                toggle_label = (
                                    "غیرفعال"
                                    if active
                                    else
                                    "فعال"
                                )

                                if st.button(
                                    toggle_label,
                                    key=f"toggle_{username}",
                                    use_container_width=True,
                                ):

                                    success, message = set_user_active(
                                        username=username,
                                        active=not active,
                                    )

                                    if not success:
                                        st.error(
                                            message or
                                            "تغییر وضعیت کاربر انجام نشد."
                                        )
                                    else:
                                        st.rerun()

                        # =============================================
                        # EDIT FORM
                        # =============================================
                        # فرم داخل همان container کاربر است تا
                        # مستقیماً زیر همان ردیف باز شود.

                        if st.session_state.editing_user == username:

                            with st.container(
                                key=f"admin_edit_form_{username}"
                            ):

                                st.markdown(
                                    """
                                    <div class="admin-form-title">
                                        ویرایش کاربر
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                st.markdown(
                                    f"""
                                    <div class="admin-edit-username">
                                        @{username}
                                    </div>
                                    """,
                                    unsafe_allow_html=True,
                                )

                                st.write("")

                                with st.form(
                                    f"edit_user_form_{username}"
                                ):

                                    col1, col2 = st.columns(2)

                                    with col1:

                                        edit_name = st.text_input(
                                            "نام و نام خانوادگی",
                                            value=name,
                                        )

                                        edit_department = st.text_input(
                                            "واحد سازمانی",
                                            value=department,
                                        )

                                    with col2:

                                        edit_role = st.text_input(
                                            "سمت",
                                            value=role,
                                        )

                                        try:
                                            current_level = int(level)
                                        except (
                                            TypeError,
                                            ValueError,
                                        ):
                                            current_level = 1

                                        current_level = max(
                                            1,
                                            min(current_level, 3),
                                        )

                                        edit_level = st.selectbox(
                                            "سطح دسترسی",
                                            options=[1, 2, 3],
                                            index=current_level - 1,
                                            format_func=get_level_name,
                                        )

                                    st.write("")

                                    save_col, cancel_col = st.columns(2)

                                    with save_col:

                                        save_edit = (
                                            st.form_submit_button(
                                                "ذخیره تغییرات",
                                                use_container_width=True,
                                            )
                                        )

                                    with cancel_col:

                                        cancel_edit = (
                                            st.form_submit_button(
                                                "انصراف",
                                                use_container_width=True,
                                            )
                                        )

                                    # ---------------------------------
                                    # CANCEL
                                    # ---------------------------------

                                    if cancel_edit:

                                        st.session_state.editing_user = None
                                        st.rerun()

                                    # ---------------------------------
                                    # SAVE
                                    # ---------------------------------

                                    if save_edit:

                                        edit_name = edit_name.strip()
                                        edit_department = edit_department.strip()
                                        edit_role = edit_role.strip()

                                        if not edit_name:

                                            st.error(
                                                "نام و نام خانوادگی الزامی است."
                                            )

                                        elif not edit_department:

                                            st.error(
                                                "واحد سازمانی الزامی است."
                                            )

                                        elif not edit_role:

                                            st.error(
                                                "سمت کاربر الزامی است."
                                            )

                                        else:

                                            success, message = update_user(
                                                username=username,
                                                name=edit_name,
                                                department=edit_department,
                                                role=edit_role,
                                                level=edit_level,
                                            )

                                            if success:

                                                st.success(
                                                    message or
                                                    "اطلاعات کاربر به‌روزرسانی شد."
                                                )

                                                st.session_state.editing_user = None
                                                st.rerun()

                                            else:

                                                st.error(
                                                    message or
                                                    "ویرایش کاربر انجام نشد."
                                                )
