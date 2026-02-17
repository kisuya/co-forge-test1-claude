"""Tests for stock detail API (history-006)."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot
from app.models.stock import Stock
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_stock_detail_api.db"


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
    seed_us_stocks(session)
    session.close()


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os as _os
    if _os.path.exists("test_stock_detail_api.db"):
        _os.remove("test_stock_detail_api.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(client: AsyncClient, email: str = "detailtest@example.com") -> str:
    await client.post(
        "/api/auth/signup",
        json={"email": email, "password": "pass1234"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "pass1234"},
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
async def test_stock_detail_basic() -> None:
    """GET /api/stocks/{id} returns stock detail info."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        _add_price_snapshot(TEST_DB_URL, stock.id, 65300.0, 3.3)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(f"/api/stocks/{stock.id}", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(stock.id)
        assert data["name"] == stock.name
        assert data["code"] == stock.code
        assert data["market"] == stock.market
        assert data["latest_price"] == 65300.0
        assert data["price_change_pct"] == 3.3
        assert data["price_currency"] == "KRW"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_detail_is_tracked_by_me_true() -> None:
    """is_tracked_by_me is true when user tracks the stock."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Add to watchlist
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )

            resp = await client.get(f"/api/stocks/{stock.id}", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_tracked_by_me"] is True
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_detail_is_tracked_by_me_false() -> None:
    """is_tracked_by_me is false when user does not track the stock."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(f"/api/stocks/{stock.id}", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["is_tracked_by_me"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_detail_tracking_count() -> None:
    """tracking_count reflects number of users tracking."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # User 1
            t1 = await _signup_login(client, "user1@example.com")
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers={"Authorization": f"Bearer {t1}"},
            )

            # User 2
            t2 = await _signup_login(client, "user2@example.com")
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers={"Authorization": f"Bearer {t2}"},
            )

            resp = await client.get(
                f"/api/stocks/{stock.id}",
                headers={"Authorization": f"Bearer {t1}"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["tracking_count"] == 2
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_detail_404() -> None:
    """GET /api/stocks/{nonexistent} returns 404."""
    _setup()
    try:
        fake_id = str(uuid.uuid4())
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(f"/api/stocks/{fake_id}", headers=headers)

        assert resp.status_code == 404
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_detail_no_price() -> None:
    """Stock without price data returns null price fields."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}
            resp = await client.get(f"/api/stocks/{stock.id}", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["latest_price"] is None
        assert data["price_change_pct"] is None
        assert data["price_currency"] is None
        assert data["price_freshness"] == "unavailable"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_detail_requires_auth() -> None:
    """Stock detail endpoint requires authentication."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(f"/api/stocks/{stock.id}")

        assert resp.status_code in (401, 403)
    finally:
        _teardown()
