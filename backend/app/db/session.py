"""Database engine and session factory (SQLAlchemy).

Works with both SQLite (local default) and PostgreSQL (Docker / hosting).
- ``get_db`` is a FastAPI dependency that yields a session and always closes it.
- ``init_db`` creates every table (demo convenience; use Alembic in production).

The declarative ``Base`` lives in ``app.models.base``; it is re-exported here so
callers can do ``from app.db.session import Base``.
"""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.models.base import Base

settings = get_settings()

# SQLite needs check_same_thread=False when used from FastAPI's threadpool.
# Postgres does not, so only add it for sqlite URLs.
connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db() -> None:
    """Create all tables. Import models first so they register on the metadata."""
    # Imported for their side effect of registering tables on Base.metadata.
    from app.models import document, user  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
