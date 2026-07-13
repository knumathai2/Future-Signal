"""SQLAlchemy engine/session setup.

Lazy-initialized: importing this module must not fail when DATABASE_URL is
unset (e.g. during scaffold/local work before TASK-002's schema is applied).
"""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_engine = None
_SessionLocal = None


def _engine_options(database_url: str) -> dict:
    """Return conservative pool settings without affecting SQLite fixtures."""
    options = {"pool_pre_ping": True}
    if not database_url.startswith("sqlite"):
        options.update(
            {
                "pool_size": settings.db_pool_size,
                "max_overflow": settings.db_max_overflow,
                "pool_timeout": settings.db_pool_timeout_seconds,
                "pool_recycle": 300,
            }
        )
    return options


def get_engine():
    global _engine
    if _engine is None:
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is not set")
        _engine = create_engine(
            settings.database_url,
            **_engine_options(settings.database_url),
        )
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autoflush=False, autocommit=False
        )
    return _SessionLocal


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a request-scoped DB session."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()
