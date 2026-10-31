"""Engine, session factory, the FastAPI session dependency and a transaction helper."""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    return create_engine(get_settings().sqlalchemy_database_uri, pool_pre_ping=True)


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Provide one session per request; injected into services via FastAPI Depends."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def transaction(session: Session) -> Iterator[Session]:
    """Commit everything done inside the block atomically, or roll it all back."""
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
