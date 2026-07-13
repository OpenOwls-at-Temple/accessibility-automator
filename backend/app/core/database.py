"""SQLAlchemy engine + session, used only for the auth/user allowlist.

Everything else (workspaces, remediation output, reports) lives on the
filesystem — the database's sole job is who is allowed to sign in. Local dev
uses SQLite (``DATABASE_URL`` default); production points at Supabase Postgres.
"""

from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.settings import load_settings


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


def _engine_kwargs(database_url: str) -> dict:
    # SQLite needs this because FastAPI may touch a session from different
    # threads within one request lifecycle.
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {}


_settings = load_settings()
engine = create_engine(_settings.database_url, **_engine_kwargs(_settings.database_url))
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
