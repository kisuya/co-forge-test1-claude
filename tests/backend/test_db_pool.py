"""Tests for DB connection pool stabilization (fix-004).

Verifies:
- Connection pool settings are properly configured
- Engine caching works (same URL returns same engine)
- Engine disposal works on shutdown
- Health endpoint reflects DB status
- check_db_connection works
"""
from __future__ import annotations

import os
import sys

import pytest
from httpx import ASGITransport, AsyncClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)


def test_pool_constants_defined():
    """Connection pool constants should be properly defined."""
    from app.db.database import MAX_OVERFLOW, POOL_RECYCLE, POOL_SIZE, POOL_TIMEOUT

    assert POOL_SIZE == 10
    assert MAX_OVERFLOW == 20
    assert POOL_TIMEOUT == 30
    assert POOL_RECYCLE == 1800


def test_engine_caching():
    """Same URL should return the same engine instance."""
    from app.db.database import dispose_engine, get_engine

    url = "sqlite:///test_pool_cache.db"
    try:
        engine1 = get_engine(url)
        engine2 = get_engine(url)
        assert engine1 is engine2, "Same URL should return cached engine"
    finally:
        dispose_engine(url)
        if os.path.exists("test_pool_cache.db"):
            os.remove("test_pool_cache.db")


def test_different_urls_different_engines():
    """Different URLs should return different engine instances."""
    from app.db.database import dispose_engine, get_engine

    url1 = "sqlite:///test_pool_diff1.db"
    url2 = "sqlite:///test_pool_diff2.db"
    try:
        engine1 = get_engine(url1)
        engine2 = get_engine(url2)
        assert engine1 is not engine2, "Different URLs should have different engines"
    finally:
        dispose_engine(url1)
        dispose_engine(url2)
        for f in ["test_pool_diff1.db", "test_pool_diff2.db"]:
            if os.path.exists(f):
                os.remove(f)


def test_dispose_engine():
    """dispose_engine should remove the engine from cache."""
    from app.db.database import _engine_cache, _sync_url, dispose_engine, get_engine

    url = "sqlite:///test_pool_dispose.db"
    try:
        get_engine(url)
        sync = _sync_url(url)
        assert sync in _engine_cache

        dispose_engine(url)
        assert sync not in _engine_cache
    finally:
        if os.path.exists("test_pool_dispose.db"):
            os.remove("test_pool_dispose.db")


def test_dispose_all_engines():
    """dispose_all_engines should clear all cached engines."""
    from app.db.database import _engine_cache, dispose_all_engines, get_engine

    url1 = "sqlite:///test_pool_all1.db"
    url2 = "sqlite:///test_pool_all2.db"
    try:
        get_engine(url1)
        get_engine(url2)
        assert len(_engine_cache) >= 2

        dispose_all_engines()
        assert len(_engine_cache) == 0
    finally:
        for f in ["test_pool_all1.db", "test_pool_all2.db"]:
            if os.path.exists(f):
                os.remove(f)


def test_check_db_connection_success():
    """check_db_connection should return True for a valid SQLite database."""
    from app.db.database import check_db_connection, create_tables, dispose_engine

    url = "sqlite:///test_pool_check.db"
    try:
        create_tables(url)
        assert check_db_connection(url) is True
    finally:
        dispose_engine(url)
        if os.path.exists("test_pool_check.db"):
            os.remove("test_pool_check.db")


def test_check_db_connection_failure():
    """check_db_connection should return False for unreachable database."""
    from app.db.database import check_db_connection, dispose_engine

    # Use a PostgreSQL URL that won't connect
    url = "postgresql://baduser:badpass@localhost:59999/nonexistent"
    result = check_db_connection(url)
    assert result is False
    dispose_engine(url)


def test_pool_kwargs_for_postgres():
    """PostgreSQL URLs should get pool configuration."""
    from app.db.database import _pool_kwargs

    kwargs = _pool_kwargs("postgresql://user:pass@localhost/db")
    assert kwargs["pool_size"] == 10
    assert kwargs["max_overflow"] == 20
    assert kwargs["pool_timeout"] == 30
    assert kwargs["pool_recycle"] == 1800
    assert kwargs["pool_pre_ping"] is True


def test_pool_kwargs_for_sqlite():
    """SQLite URLs should not get pool configuration."""
    from app.db.database import _pool_kwargs

    kwargs = _pool_kwargs("sqlite:///test.db")
    assert kwargs == {}


@pytest.mark.asyncio
async def test_health_endpoint_basic():
    """GET /health should return status ok."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_endpoint_with_detail():
    """GET /health?detail=true should include database status."""
    from app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health?detail=true")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "database" in data
    # In test env, DB might be up or down depending on setup
    assert data["database"] in ("up", "down")


def test_session_factory_uses_cached_engine():
    """get_session_factory should use the cached engine."""
    from app.db.database import _engine_cache, _sync_url, dispose_engine, get_session_factory

    url = "sqlite:///test_pool_factory.db"
    try:
        factory = get_session_factory(url)
        sync = _sync_url(url)
        assert sync in _engine_cache, "Session factory should trigger engine caching"
        assert factory is not None
    finally:
        dispose_engine(url)
        if os.path.exists("test_pool_factory.db"):
            os.remove("test_pool_factory.db")


def test_create_tables_uses_cached_engine():
    """create_tables should use the cached engine."""
    from app.db.database import _engine_cache, _sync_url, create_tables, dispose_engine

    url = "sqlite:///test_pool_tables.db"
    try:
        create_tables(url)
        sync = _sync_url(url)
        assert sync in _engine_cache, "create_tables should use cached engine"
    finally:
        dispose_engine(url)
        if os.path.exists("test_pool_tables.db"):
            os.remove("test_pool_tables.db")
