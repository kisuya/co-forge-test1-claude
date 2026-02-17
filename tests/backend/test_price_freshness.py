"""Tests for price data freshness management (data-007)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot
from app.models.stock import Stock
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_price_freshness.db"


def _get_test_db() -> Session:  # type: ignore[misc]
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


def _setup() -> None:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_stocks(session)
    session.close()


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os as _os
    if _os.path.exists("test_price_freshness.db"):
        _os.remove("test_price_freshness.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient) -> str:
    await client.post(
        "/api/auth/signup",
        json={"email": "freshtest@example.com", "password": "pass1234"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "freshtest@example.com", "password": "pass1234"},
    )
    return resp.json()["access_token"]


def _get_stock_by_code(db_url: str, code: str) -> Stock:
    factory = get_session_factory(db_url)
    session = factory()
    from sqlalchemy import select
    stock = session.execute(
        select(Stock).where(Stock.code == code)
    ).scalar_one()
    session.close()
    return stock


def _add_price_snapshot(
    db_url: str, stock_id: uuid.UUID, price: float, change_pct: float,
    captured_at: datetime | None = None,
) -> None:
    factory = get_session_factory(db_url)
    session = factory()
    snapshot = PriceSnapshot(
        stock_id=stock_id,
        price=Decimal(str(price)),
        change_pct=change_pct,
        volume=1000,
    )
    if captured_at:
        snapshot.captured_at = captured_at
    session.add(snapshot)
    session.commit()
    session.close()


@pytest.mark.asyncio
async def test_freshness_live() -> None:
    """Data captured within 30 minutes has freshness='live'."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        now = datetime.now(timezone.utc)
        _add_price_snapshot(
            TEST_DB_URL, stock.id, 65300.0, 3.3,
            captured_at=now - timedelta(minutes=5),
        )

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )
            resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["price_freshness"] == "live"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_freshness_delayed() -> None:
    """Data captured 30min-6h ago has freshness='delayed'."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        now = datetime.now(timezone.utc)
        _add_price_snapshot(
            TEST_DB_URL, stock.id, 65300.0, 3.3,
            captured_at=now - timedelta(hours=2),
        )

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )
            resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["price_freshness"] == "delayed"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_freshness_stale() -> None:
    """Data captured more than 6 hours ago has freshness='stale'."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        now = datetime.now(timezone.utc)
        _add_price_snapshot(
            TEST_DB_URL, stock.id, 65300.0, 3.3,
            captured_at=now - timedelta(hours=12),
        )

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )
            resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["price_freshness"] == "stale"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_freshness_unavailable() -> None:
    """No price data returns freshness='unavailable'."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )
            resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["price_freshness"] == "unavailable"
        assert item["is_price_available"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_redis_cache_hit() -> None:
    """Price data from Redis cache is used when available."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        now = datetime.now(timezone.utc)

        # Prepare mock Redis client
        mock_redis = MagicMock()
        import json
        cached_data = json.dumps({
            "stock_id": str(stock.id),
            "price": "70000",
            "change_pct": 5.5,
            "volume": 2000,
            "captured_at": (now - timedelta(minutes=10)).isoformat(),
        })
        mock_redis.get.return_value = cached_data

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )

            with patch("app.api.watchlist.get_redis_client", return_value=mock_redis):
                resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["latest_price"] == 70000.0
        assert item["price_change_pct"] == 5.5
        assert item["is_price_available"] is True
        assert item["price_freshness"] == "live"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_redis_cache_miss_falls_back_to_db() -> None:
    """When Redis cache misses, data is fetched from DB and cached."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        now = datetime.now(timezone.utc)
        _add_price_snapshot(
            TEST_DB_URL, stock.id, 65300.0, 3.3,
            captured_at=now - timedelta(minutes=5),
        )

        # Redis returns None (cache miss) but accepts writes
        mock_redis = MagicMock()
        mock_redis.get.return_value = None

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )

            with patch("app.api.watchlist.get_redis_client", return_value=mock_redis):
                resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["latest_price"] == 65300.0
        # Verify cache was set
        mock_redis.setex.assert_called_once()
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_redis_down_graceful_fallback() -> None:
    """When Redis is down, price data is still served from DB."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        now = datetime.now(timezone.utc)
        _add_price_snapshot(
            TEST_DB_URL, stock.id, 65300.0, 3.3,
            captured_at=now - timedelta(minutes=5),
        )

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )

            # Redis client returns None (connection failed)
            with patch("app.api.watchlist.get_redis_client", return_value=None):
                resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        item = resp.json()[0]
        assert item["latest_price"] == 65300.0
        assert item["is_price_available"] is True
    finally:
        _teardown()
