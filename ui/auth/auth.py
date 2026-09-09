import hashlib
import hmac
import secrets

import streamlit as st

from auth.users import (
    get_user,
    update_user
)


# =========================================================
# PASSWORD HASHING
# =========================================================

def hash_password(password):
    """
    Hash a password using PBKDF2-HMAC-SHA256.

    The generated value contains:
        algorithm + iterations + salt + hash
    """

    if not password:
        return None

    salt = secrets.token_bytes(16)

    iterations = 600_000

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        iterations
    )

    return (
        f"pbkdf2_sha256${iterations}$"
        f"{salt.hex()}$"
        f"{password_hash.hex()}"
    )


def verify_password(password, stored_hash):
    """
    Verify a plain-text password against its stored hash.
    """

    if not password or not stored_hash:
        return False

    try:
        algorithm, iterations, salt_hex, hash_hex = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations)

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        actual_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations
        )

        return hmac.compare_digest(
            actual_hash,
            expected_hash
        )

    except (ValueError, TypeError):
        return False


# =========================================================
# TEMPORARY DEFAULT ADMIN
# =========================================================

def _initialize_default_admin():
    """
    Temporary development helper.

    If the admin user exists but has no password hash,
    initialize it with the old test password: 1234.

    This is only for the current MVP.
    """

    admin = get_user("admin")

    if admin is None:
        return

    if admin.get("password_hash"):
        return

    password_hash = hash_password("1234")

    update_user(
        username="admin",
        password_hash=password_hash
    )


_initialize_default_admin()


# =========================================================
# LOGIN
# =========================================================

def login(username, password):
    """
    Authenticate a user using users.json.

    Returns:
        True  -> successful login
        False -> failed login
    """

    username = username.strip()

    if not username or not password:
        return False

    user = get_user(username)

    if user is None:
        return False


    if not user.get("active", True):
        return False

    stored_hash = user.get("password_hash")

    if not verify_password(
        password,
        stored_hash
    ):
        return False

    # -----------------------------------------
    # Save authenticated user
    # -----------------------------------------

    st.session_state.is_authenticated = True

    st.session_state.user = {
        "username": user["username"],
        "name": user.get("name", ""),
        "department": user.get("department", ""),
        "role": user.get("role", ""),
        "level": user.get("level", 1)
    }

    return True


# =========================================================
# CURRENT USER
# =========================================================

def get_current_user():
    """
    Return currently authenticated user.
    """

    return st.session_state.get("user")


# =========================================================
# USER LEVEL
# =========================================================

def get_current_user_level():
    """
    Return current user's access level.
    """

    user = get_current_user()

    if user is None:
        return None

    return user.get("level")


# =========================================================
# PERMISSION CHECK
# =========================================================

def has_permission(required_level):
    """
    Check whether the current user has enough access.

    Example:
        has_permission(3)

    means:
        user must have level 3 or higher.
    """

    current_level = get_current_user_level()

    if current_level is None:
        return False

    return current_level >= required_level


def is_manager():
    """
    Check whether the current user is level 3.
    """

    return has_permission(3)


# =========================================================
# CHANGE PASSWORD
# =========================================================

def change_password(
    username,
    current_password,
    new_password
):
    """
    Change user's password.

    Returns:
        (success, message)
    """

    if not current_password:
        return False, "رمز عبور فعلی را وارد کنید."

    if not new_password:
        return False, "رمز عبور جدید را وارد کنید."

    if len(new_password) < 8:
        return False, (
            "رمز عبور جدید باید حداقل ۸ کاراکتر باشد."
        )

    user = get_user(username)

    if user is None:
        return False, "کاربر موردنظر یافت نشد."

    stored_hash = user.get("password_hash")

    if not verify_password(
        current_password,
        stored_hash
    ):
        return False, "رمز عبور فعلی اشتباه است."

    if verify_password(
        new_password,
        stored_hash
    ):
        return False, (
            "رمز عبور جدید باید با رمز عبور فعلی متفاوت باشد."
        )

    new_hash = hash_password(new_password)

    success, message = update_user(
        username=username,
        password_hash=new_hash
    )

    if not success:
        return False, message

    return True, "رمز عبور با موفقیت تغییر کرد."


# =========================================================
# LOGOUT
# =========================================================

def logout():
    """
    Logout current user.
    """

    st.session_state.is_authenticated = False

    if "user" in st.session_state:
        del st.session_state.user
