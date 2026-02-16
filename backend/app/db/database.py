from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_engine(database_url: str) -> object:
    """Create a SQLAlchemy engine from the given URL.

    Converts async URLs to sync for standard engine usage.
    """
    sync_url = database_url.replace("+asyncpg", "").replace("+aiosqlite", "")
    return create_engine(sync_url)


def get_session_factory(database_url: str) -> sessionmaker[Session]:
    """Create a session factory bound to the given database URL."""
    engine = get_engine(database_url)
    return sessionmaker(bind=engine)


def create_tables(database_url: str) -> None:
    """Create all tables defined by models."""
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)
