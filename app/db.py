from __future__ import annotations

from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.models import Base

_engine: Optional[Engine] = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)


def _build_engine(db_url: str) -> Engine:
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    return create_engine(db_url, connect_args=connect_args)


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = _build_engine(settings.normalized_database_url)
        SessionLocal.configure(bind=_engine)
    return _engine


def configure_database(db_url: str) -> None:
    global _engine
    _engine = _build_engine(db_url)
    SessionLocal.configure(bind=_engine)


def init_db() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
