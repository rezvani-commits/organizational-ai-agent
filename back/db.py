
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from back.config import Config

Base = declarative_base()

engine = create_engine(
    Config.DB_URL,
    pool_size=getattr(Config, "DB_POOL_SIZE", 5),
    max_overflow=getattr(Config, "DB_MAX_OVERFLOW", 10),
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


@contextmanager
def get_db_session():
   
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
    
    from back import models

    Base.metadata.create_all(bind=engine)
