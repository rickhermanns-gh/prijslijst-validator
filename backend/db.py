"""
Database connection — SQLAlchemy sync engine
Gebruik get_db als FastAPI Depends() dependency in routes.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

# Railway levert postgres://, SQLAlchemy verwacht postgresql://
_raw_url = os.getenv("DATABASE_URL", "")
if not _raw_url:
    raise RuntimeError("DATABASE_URL environment variable is not set")

DATABASE_URL = _raw_url.replace("postgres://", "postgresql://", 1) if _raw_url.startswith("postgres://") else _raw_url

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,   # Reconnect bij verlopen connecties
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — levert een DB sessie, sluit altijd af na request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
