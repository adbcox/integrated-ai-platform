"""Database engine and session factory for RGC."""

from __future__ import annotations

import os
from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

_DEFAULT_DB_URL = "sqlite:///rgc.db"


def get_db_url() -> str:
    return os.environ.get("RGC_DATABASE_URL", _DEFAULT_DB_URL)


def make_engine(url: Optional[str] = None) -> Engine:
    resolved = url or get_db_url()
    kwargs: dict = {}
    if resolved.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(resolved, **kwargs)


def make_session_factory(engine: Engine) -> sessionmaker:
    return sessionmaker(bind=engine, expire_on_commit=False)


# Module-level singletons; replaced in tests via dependency override.
_engine: Optional[Engine] = None
_factory: Optional[sessionmaker] = None


def _get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = make_engine()
    return _engine


def _get_factory() -> sessionmaker:
    global _factory
    if _factory is None:
        _factory = make_session_factory(_get_engine())
    return _factory


def get_db_dep() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a DB session."""
    db = _get_factory()()
    try:
        yield db
    finally:
        db.close()
