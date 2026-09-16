from auth.auth import hash_password
from back.db import get_db_session
from back.models import User

from ui.auth.auth import hash_password


USERNAME = "admin"
PASSWORD = "admin123"
NAME = "مدیر سیستم"
DEPARTMENT = "مدیریت"
ROLE = "مدیر سیستم"
LEVEL = 3


def create_admin():
    with get_db_session() as db:
        existing = db.query(User).filter(
            User.username == USERNAME
        ).first()

        if existing:
            print(f"کاربر '{USERNAME}' از قبل وجود دارد.")
            return

        admin = User(
            username=USERNAME,
            name=NAME,
            department=DEPARTMENT,
            role=ROLE,
            level=LEVEL,
            password_hash=hash_password(PASSWORD),
            active=True,
        )

        db.add(admin)

    print("Admin user created successfully!")
    print(f"Username: {USERNAME}")
    print(f"Password: {PASSWORD}")


if __name__ == "__main__":
    create_admin()
