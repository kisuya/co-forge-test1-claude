"""Tests for Watchlist API price data integration (data-006)."""
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

TEST_DB_URL = "sqlite:///test_watchlist_price.db"


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
    if _os.path.exists("test_watchlist_price.db"):
        _os.remove("test_watchlist_price.db")


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
        json={"email": "pricetest@example.com", "password": "pass1234"},
    )
    resp = await client.post(
        "/api/auth/login",
        json={"email": "pricetest@example.com", "password": "pass1234"},
    )
    return resp.json()["access_token"]


def _add_price_snapshot(
    db_url: str, stock_id: uuid.UUID, price: float, change_pct: float,
    captured_at: datetime | None = None,
) -> None:
    """Insert a PriceSnapshot directly into the DB."""
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


def _get_stock_by_code(db_url: str, code: str) -> Stock:
    factory = get_session_factory(db_url)
    session = factory()
    from sqlalchemy import select
    stock = session.execute(
        select(Stock).where(Stock.code == code)
    ).scalar_one()
    session.close()
    return stock


@pytest.mark.asyncio
async def test_watchlist_with_price_data() -> None:
    """GET /api/watchlist returns price fields when PriceSnapshot exists."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")  # 삼성전자 KRX
        _add_price_snapshot(TEST_DB_URL, stock.id, 65300.0, 3.3)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            # Add stock to watchlist
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )

            # Get watchlist
            resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

        item = data[0]
        assert item["latest_price"] == 65300.0
        assert item["price_change_pct"] == 3.3
        assert item["price_change"] is not None
        assert item["price_currency"] == "KRW"
        assert item["price_updated_at"] is not None
        assert item["is_price_available"] is True
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_watchlist_without_price_data() -> None:
    """GET /api/watchlist returns null price fields when no PriceSnapshot exists."""
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
        data = resp.json()
        assert len(data) == 1

        item = data[0]
        assert item["latest_price"] is None
        assert item["price_change"] is None
        assert item["price_change_pct"] is None
        assert item["price_currency"] is None
        assert item["price_updated_at"] is None
        assert item["is_price_available"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_watchlist_usd_currency_for_us_stocks() -> None:
    """US stocks (NYSE/NASDAQ) return USD as price_currency."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "AAPL")  # Apple, NASDAQ
        _add_price_snapshot(TEST_DB_URL, stock.id, 189.45, -1.2)

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
        assert item["latest_price"] == 189.45
        assert item["price_change_pct"] == -1.2
        assert item["price_currency"] == "USD"
        assert item["is_price_available"] is True
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_watchlist_multiple_stocks_single_query() -> None:
    """Multiple stocks should each have their correct price data."""
    _setup()
    try:
        samsung = _get_stock_by_code(TEST_DB_URL, "005930")
        sk = _get_stock_by_code(TEST_DB_URL, "000660")

        _add_price_snapshot(TEST_DB_URL, samsung.id, 65300.0, 3.3)
        _add_price_snapshot(TEST_DB_URL, sk.id, 120000.0, -2.1)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            await client.post(
                "/api/watchlist",
                json={"stock_id": str(samsung.id)},
                headers=headers,
            )
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(sk.id)},
                headers=headers,
            )

            resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

        prices = {d["stock_code"]: d for d in data}
        assert prices["005930"]["latest_price"] == 65300.0
        assert prices["005930"]["price_change_pct"] == 3.3
        assert prices["000660"]["latest_price"] == 120000.0
        assert prices["000660"]["price_change_pct"] == -2.1
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_watchlist_latest_snapshot_used() -> None:
    """When multiple snapshots exist, the most recent one is used."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")

        # Older snapshot
        _add_price_snapshot(
            TEST_DB_URL, stock.id, 60000.0, 1.0,
            captured_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        # Newer snapshot
        _add_price_snapshot(
            TEST_DB_URL, stock.id, 65300.0, 3.3,
            captured_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
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
        assert item["latest_price"] == 65300.0
        assert item["price_change_pct"] == 3.3
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_watchlist_mixed_price_availability() -> None:
    """Some stocks with price, some without — each returns correct is_price_available."""
    _setup()
    try:
        samsung = _get_stock_by_code(TEST_DB_URL, "005930")
        naver = _get_stock_by_code(TEST_DB_URL, "035420")

        # Only samsung has price
        _add_price_snapshot(TEST_DB_URL, samsung.id, 65300.0, 3.3)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            await client.post(
                "/api/watchlist",
                json={"stock_id": str(samsung.id)},
                headers=headers,
            )
            await client.post(
                "/api/watchlist",
                json={"stock_id": str(naver.id)},
                headers=headers,
            )

            resp = await client.get("/api/watchlist", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        items = {d["stock_code"]: d for d in data}

        assert items["005930"]["is_price_available"] is True
        assert items["005930"]["latest_price"] == 65300.0

        assert items["035420"]["is_price_available"] is False
        assert items["035420"]["latest_price"] is None
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_watchlist_zero_change() -> None:
    """Zero percent change returns change_pct=0 and change=0."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        _add_price_snapshot(TEST_DB_URL, stock.id, 65000.0, 0.0)

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
        assert item["price_change_pct"] == 0.0
        assert item["price_change"] == 0.0
        assert item["is_price_available"] is True
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_post_watchlist_includes_price() -> None:
    """POST /api/watchlist response includes price data when available."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        _add_price_snapshot(TEST_DB_URL, stock.id, 65300.0, 3.3)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )

        assert resp.status_code == 201
        item = resp.json()
        assert item["latest_price"] == 65300.0
        assert item["is_price_available"] is True
        assert item["price_currency"] == "KRW"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_patch_watchlist_includes_price() -> None:
    """PATCH /api/watchlist/{id} response includes price data."""
    _setup()
    try:
        stock = _get_stock_by_code(TEST_DB_URL, "005930")
        _add_price_snapshot(TEST_DB_URL, stock.id, 65300.0, 3.3)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            token = await _signup_login(client)
            headers = {"Authorization": f"Bearer {token}"}

            add_resp = await client.post(
                "/api/watchlist",
                json={"stock_id": str(stock.id)},
                headers=headers,
            )
            item_id = add_resp.json()["id"]

            resp = await client.patch(
                f"/api/watchlist/{item_id}",
                json={"threshold": 5.0},
                headers=headers,
            )

        assert resp.status_code == 200
        item = resp.json()
        assert item["threshold"] == 5.0
        assert item["latest_price"] == 65300.0
        assert item["is_price_available"] is True
    finally:
        _teardown()
