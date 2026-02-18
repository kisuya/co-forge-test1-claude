from __future__ import annotations

import threading

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

# Connection pool settings
POOL_SIZE = 10
MAX_OVERFLOW = 20
POOL_TIMEOUT = 30
POOL_RECYCLE = 1800  # 30 minutes


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


_engine_cache: dict[str, object] = {}
_engine_lock = threading.Lock()


def _sync_url(database_url: str) -> str:
    """Convert async database URL to sync."""
    return database_url.replace("+asyncpg", "").replace("+aiosqlite", "")


def _pool_kwargs(url: str) -> dict:
    """Return pool kwargs appropriate for the URL (no pooling for SQLite)."""
    if url.startswith("sqlite"):
        return {}
    return {
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
        "pool_timeout": POOL_TIMEOUT,
        "pool_recycle": POOL_RECYCLE,
        "pool_pre_ping": True,
    }


def get_engine(database_url: str) -> object:
    """Get or create a cached SQLAlchemy engine with connection pool settings.

    Engines are cached per URL to avoid recreating pools on every request.
    """
    sync = _sync_url(database_url)

    if sync not in _engine_cache:
        with _engine_lock:
            if sync not in _engine_cache:
                _engine_cache[sync] = create_engine(sync, **_pool_kwargs(sync))

    return _engine_cache[sync]


def get_session_factory(database_url: str) -> sessionmaker[Session]:
    """Create a session factory bound to the cached engine."""
    engine = get_engine(database_url)
    return sessionmaker(bind=engine)


def create_tables(database_url: str) -> None:
    """Create all tables defined by models."""
    engine = get_engine(database_url)
    Base.metadata.create_all(bind=engine)


def dispose_engine(database_url: str) -> None:
    """Dispose the engine for the given URL, releasing all pool connections."""
    sync = _sync_url(database_url)
    with _engine_lock:
        engine = _engine_cache.pop(sync, None)
        if engine is not None:
            engine.dispose()


def dispose_all_engines() -> None:
    """Dispose all cached engines. Call on app shutdown."""
    with _engine_lock:
        for engine in _engine_cache.values():
            engine.dispose()
        _engine_cache.clear()


def check_db_connection(database_url: str) -> bool:
    """Check if the database is reachable by executing SELECT 1."""
    try:
        engine = get_engine(database_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
