import json
from pathlib import Path


# =========================================================
# FILE PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
USERS_FILE = BASE_DIR / "data" / "users.json"


# =========================================================
# READ / WRITE
# =========================================================

def _read_users():
    """Read all users from users.json."""

    if not USERS_FILE.exists():
        return []

    try:
        with open(
            USERS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return []


def _write_users(users):
    """Write users to users.json."""

    USERS_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        USERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            users,
            file,
            ensure_ascii=False,
            indent=4
        )


# =========================================================
# GET USERS
# =========================================================

def get_users():
    """
    Return all users.

    Also makes sure old users that don't have
    the 'active' field are treated as active.
    """

    users = _read_users()

    for user in users:

        if "active" not in user:
            user["active"] = True

    return users


# =========================================================
# GET SINGLE USER
# =========================================================

def get_user(username):
    """
    Find a user by username.

    Returns:
        user dictionary or None
    """

    users = _read_users()

    for user in users:

        if user.get("username") == username:

            # ---------------------------------------------
            # Backward compatibility
            # ---------------------------------------------

            if "active" not in user:
                user["active"] = True

            return user

    return None


# =========================================================
# CHECK USER EXISTS
# =========================================================

def user_exists(username):
    """
    Check whether a username already exists.
    """

    return get_user(username) is not None


# =========================================================
# CREATE USER
# =========================================================

def create_user(
    username,
    name,
    department,
    role,
    level,
    password_hash
):
    """
    Create a new user.

    New users are active by default.

    Returns:
        (success, message)
    """

    username = username.strip()
    name = name.strip()
    department = department.strip()
    role = role.strip()

    if not username:
        return False, "نام کاربری را وارد کنید."

    if not name:
        return False, "نام و نام خانوادگی را وارد کنید."

    if not department:
        return False, "واحد سازمانی را وارد کنید."

    if not role:
        return False, "سمت کاربر را وارد کنید."

    if level not in [1, 2, 3]:
        return False, "سطح دسترسی نامعتبر است."

    if not password_hash:
        return False, "رمز عبور معتبر نیست."

    if user_exists(username):
        return False, "این نام کاربری قبلاً ثبت شده است."

    users = _read_users()

    new_user = {
        "username": username,
        "name": name,
        "department": department,
        "role": role,
        "level": level,
        "password_hash": password_hash,
        "active": True
    }

    users.append(new_user)

    _write_users(users)

    return True, "کاربر با موفقیت ایجاد شد."


# =========================================================
# UPDATE USER
# =========================================================

def update_user(
    username,
    name=None,
    department=None,
    role=None,
    level=None,
    password_hash=None,
    active=None
):
    """
    Update an existing user.

    Any argument that is None will remain unchanged.

    Returns:
        (success, message)
    """

    users = _read_users()

    for user in users:

        if user.get("username") != username:
            continue

        # ---------------------------------------------
        # Name
        # ---------------------------------------------

        if name is not None:
            user["name"] = name.strip()

        # ---------------------------------------------
        # Department
        # ---------------------------------------------

        if department is not None:
            user["department"] = department.strip()

        # ---------------------------------------------
        # Role
        # ---------------------------------------------

        if role is not None:
            user["role"] = role.strip()

        # ---------------------------------------------
        # Level
        # ---------------------------------------------

        if level is not None:

            if level not in [1, 2, 3]:
                return False, "سطح دسترسی نامعتبر است."

            user["level"] = level

        # ---------------------------------------------
        # Password
        # ---------------------------------------------

        if password_hash is not None:
            user["password_hash"] = password_hash

        # ---------------------------------------------
        # Active
        # ---------------------------------------------

        if active is not None:

            if not isinstance(active, bool):
                return False, "وضعیت کاربر نامعتبر است."

            user["active"] = active

        # ---------------------------------------------
        # Backward compatibility
        # ---------------------------------------------

        if "active" not in user:
            user["active"] = True

        _write_users(users)

        return True, "اطلاعات کاربر با موفقیت بروزرسانی شد."

    return False, "کاربر موردنظر یافت نشد."


# =========================================================
# ACTIVATE / DEACTIVATE USER
# =========================================================

def set_user_active(username, active):
    """
    Activate or deactivate a user.

    Args:
        username: username of target user
        active: True or False

    Returns:
        (success, message)
    """

    if not isinstance(active, bool):
        return False, "وضعیت کاربر نامعتبر است."

    return update_user(
        username=username,
        active=active
    )


# =========================================================
# DELETE USER
# =========================================================

def delete_user(username):
    """
    Delete a user permanently.

    This function is kept for future administrative use,
    but the UI should preferably use deactivate instead.
    """

    users = _read_users()

    updated_users = [
        user
        for user in users
        if user.get("username") != username
    ]

    if len(updated_users) == len(users):
        return False, "کاربر موردنظر یافت نشد."

    _write_users(updated_users)

    return True, "کاربر با موفقیت حذف شد."


# =========================================================
# GET USER LEVEL
# =========================================================

def get_user_level(username):
    """
    Return user's access level.
    """

    user = get_user(username)

    if user is None:
        return None

    return user.get("level")


# =========================================================
# GET USER STATUS
# =========================================================

def is_user_active(username):
    """
    Return whether a user is active.

    Old users without the 'active' field
    are considered active.
    """

    user = get_user(username)

    if user is None:
        return False

    return user.get("active", True)


# =========================================================
# GET USERS BY LEVEL
# =========================================================

def get_users_by_level(level):
    """
    Return users with a specific access level.
    """

    users = get_users()

    return [
        user
        for user in users
        if user.get("level") == level
    ]


# =========================================================
# GET ACTIVE USERS
# =========================================================

def get_active_users():
    """
    Return only active users.
    """

    users = get_users()

    return [
        user
        for user in users
        if user.get("active", True)
    ]


# =========================================================
# GET INACTIVE USERS
# =========================================================

def get_inactive_users():
    """
    Return only inactive users.
    """

    users = get_users()

    return [
        user
        for user in users
        if not user.get("active", True)
    ]
