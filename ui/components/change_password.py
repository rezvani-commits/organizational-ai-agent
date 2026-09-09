import streamlit as st

from auth.auth import change_password


@st.dialog("تغییر رمز عبور")
def change_password_dialog(username):
    """
    Change password modal.
    """

    current_password = st.text_input(
        "رمز عبور فعلی",
        type="password",
        key="dialog_current_password"
    )

    new_password = st.text_input(
        "رمز عبور جدید",
        type="password",
        key="dialog_new_password"
    )

    confirm_password = st.text_input(
        "تکرار رمز عبور جدید",
        type="password",
        key="dialog_confirm_password"
    )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
            "ذخیره",
            use_container_width=True,
            key="save_password"
        ):

            # -----------------------------------------
            # Confirm password
            # -----------------------------------------

            if new_password != confirm_password:

                st.error(
                    "تکرار رمز عبور با رمز عبور جدید مطابقت ندارد."
                )

            else:

                # -----------------------------------------
                # Change password
                # -----------------------------------------

                success, message = change_password(
                    username=username,
                    current_password=current_password,
                    new_password=new_password
                )

                if success:

                    # Tell the main page that the password
                    # was successfully changed.
                    st.session_state.password_change_success = True

                    # Close dialog by rerunning the app.
                    st.rerun()

                else:

                    st.error(message)

    with col2:

        if st.button(
            "انصراف",
            use_container_width=True,
            key="cancel_password"
        ):
            st.rerun()