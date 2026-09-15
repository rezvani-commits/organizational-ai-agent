"""
DB
--
اتصال مرکزی به Postgres برای کل اپلیکیشن (کاربران، سشن‌های چت، و هر چیز
دیگه‌ای که بعداً لازم شد).

نکته‌ی مهم: DialogueManager از قبل خودش یک Engine جدا برای تاریخچه‌ی چت
می‌سازه (روی همون Config.CHAT_HISTORY_DB_URL). اگه هر دو رو به یک دیتابیس
وصل کنی مشکلی نیست (فقط دو تا connection pool جدا می‌سازن)، ولی اگه
می‌خوای همه از یک Engine واحد استفاده کنن، می‌تونی DialogueManager رو هم
بعداً به همین ماژول وصل کنی (پایین توضیح دادم چطور).

استفاده:
    from back.db import get_db_session, init_db

    def get_users():
        with get_db_session() as db:
            return db.query(User).all()
"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from back.config import Config

Base = declarative_base()

# ---------------------------------------------------------------------
# Engine مشترک - یک بار برای کل عمر پروسه ساخته می‌شه
# ---------------------------------------------------------------------
engine = create_engine(
    Config.DB_URL,
    pool_size=getattr(Config, "DB_POOL_SIZE", 5),
    max_overflow=getattr(Config, "DB_MAX_OVERFLOW", 10),
    pool_pre_ping=True,  # اگه connection قطع شده بود (idle timeout سمت DB)، خودکار reconnect می‌کنه
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_db_session():
    """
    Context manager برای یک تراکنش دیتابیس. در پایان بلوک، خودکار commit
    می‌کنه؛ اگه خطایی رخ بده rollback می‌کنه.

    مثال:
        with get_db_session() as db:
            db.add(User(...))
        # اینجا خودکار commit شده
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    """جدول‌هایی که تو back/models.py تعریف شدن رو (اگه از قبل وجود نداشته
    باشن) تو دیتابیس می‌سازه. این تابع idempotent هست - اجرای دوباره‌اش
    مشکلی ایجاد نمی‌کنه."""
    from back import models  # noqa: F401  (فقط برای register شدن مدل‌ها روی Base)

    Base.metadata.create_all(bind=engine)
