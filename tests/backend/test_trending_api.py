"""Tests for trending and popular stock APIs (trending-001)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot, Report
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_trending_api.db"


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
    if os.path.exists("test_trending_api.db"):
        os.remove("test_trending_api.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


def _get_kr_stocks(count=3) -> list[Stock]:
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    stocks = list(
        session.execute(
            select(Stock).where(Stock.market == "KRX").limit(count)
        ).scalars().all()
    )
    session.close()
    return stocks


def _create_user(email="trend@example.com") -> User:
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    user = User(
        email=email,
        password_hash="hashed",
        settings={"threshold": 3.0},
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    session.close()
    return user


def _track_stock(user_id, stock_id) -> None:
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    wl = Watchlist(user_id=user_id, stock_id=stock_id)
    session.add(wl)
    session.commit()
    session.close()


def _create_report(stock_id, change_pct, hours_ago=1) -> Report:
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    now = datetime.now(timezone.utc)
    report = Report(
        stock_id=stock_id,
        trigger_price=Decimal("10000"),
        trigger_change_pct=change_pct,
        status="completed",
        summary="Test report",
        created_at=now - timedelta(hours=hours_ago),
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    session.close()
    return report


def _create_price_snapshot(stock_id, price, change_pct) -> None:
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    snap = PriceSnapshot(
        stock_id=stock_id,
        price=Decimal(str(price)),
        change_pct=change_pct,
        volume=1000000,
    )
    session.add(snap)
    session.commit()
    session.close()


# ── Trending API tests ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trending_with_events() -> None:
    """GET /api/trending returns stocks with recent events sorted by abs change_pct."""
    _setup()
    try:
        stocks = _get_kr_stocks(3)
        # Create reports with different change_pct
        _create_report(stocks[0].id, 5.0, hours_ago=1)  # highest
        _create_report(stocks[1].id, -3.0, hours_ago=2)  # 2nd
        _create_report(stocks[2].id, 1.5, hours_ago=3)   # 3rd

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 3

            # Sorted by abs change_pct DESC
            assert data[0]["change_pct"] == 5.0
            assert data[1]["change_pct"] == 3.0  # abs(-3.0)
            assert data[2]["change_pct"] == 1.5

            # Check fields
            assert "stock_id" in data[0]
            assert "stock_name" in data[0]
            assert "stock_code" in data[0]
            assert "market" in data[0]
            assert "event_count" in data[0]
            assert data[0]["event_count"] == 1
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_no_auth_required() -> None:
    """GET /api/trending works without authentication."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            assert resp.status_code == 200
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_empty() -> None:
    """GET /api/trending returns empty array when no events."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            assert resp.status_code == 200
            assert resp.json() == []
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_max_10() -> None:
    """GET /api/trending returns max 10 stocks."""
    _setup()
    try:
        stocks = _get_kr_stocks(10)
        if len(stocks) < 10:
            pytest.skip("Not enough stocks seeded")

        for i, stock in enumerate(stocks):
            _create_report(stock.id, float(i + 1), hours_ago=1)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) <= 10
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_excludes_old_events() -> None:
    """GET /api/trending excludes events older than 24 hours."""
    _setup()
    try:
        stocks = _get_kr_stocks(2)
        _create_report(stocks[0].id, 5.0, hours_ago=1)   # within 24h
        _create_report(stocks[1].id, 10.0, hours_ago=25)  # older than 24h

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["change_pct"] == 5.0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_event_count() -> None:
    """GET /api/trending correctly counts multiple events per stock."""
    _setup()
    try:
        stocks = _get_kr_stocks(1)
        _create_report(stocks[0].id, 5.0, hours_ago=1)
        _create_report(stocks[0].id, 3.0, hours_ago=2)
        _create_report(stocks[0].id, -2.0, hours_ago=3)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["event_count"] == 3
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_latest_report_id() -> None:
    """GET /api/trending includes latest_report_id."""
    _setup()
    try:
        stocks = _get_kr_stocks(1)
        report = _create_report(stocks[0].id, 5.0, hours_ago=1)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            data = resp.json()
            assert data[0]["latest_report_id"] == str(report.id)
    finally:
        _teardown()


# ── Popular API tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_popular_with_tracking() -> None:
    """GET /api/popular returns stocks sorted by tracking count."""
    _setup()
    try:
        stocks = _get_kr_stocks(3)
        user1 = _create_user("u1@example.com")
        user2 = _create_user("u2@example.com")
        user3 = _create_user("u3@example.com")

        # Stock 0: 3 trackers, stock 1: 2 trackers, stock 2: 1 tracker
        _track_stock(user1.id, stocks[0].id)
        _track_stock(user2.id, stocks[0].id)
        _track_stock(user3.id, stocks[0].id)
        _track_stock(user1.id, stocks[1].id)
        _track_stock(user2.id, stocks[1].id)
        _track_stock(user1.id, stocks[2].id)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/popular")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 3
            assert data[0]["tracking_count"] == 3
            assert data[1]["tracking_count"] == 2
            assert data[2]["tracking_count"] == 1

            # Check fields
            assert "stock_id" in data[0]
            assert "stock_name" in data[0]
            assert "stock_code" in data[0]
            assert "market" in data[0]
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_popular_no_auth_required() -> None:
    """GET /api/popular works without authentication."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/popular")
            assert resp.status_code == 200
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_popular_empty() -> None:
    """GET /api/popular returns empty array when no tracking data."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/popular")
            assert resp.status_code == 200
            assert resp.json() == []
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_popular_with_price_data() -> None:
    """GET /api/popular includes latest price data when available."""
    _setup()
    try:
        stocks = _get_kr_stocks(1)
        user = _create_user()
        _track_stock(user.id, stocks[0].id)
        _create_price_snapshot(stocks[0].id, 65300, 3.5)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/popular")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["latest_price"] == 65300.0
            assert data[0]["price_change_pct"] == 3.5
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_popular_without_price_data() -> None:
    """GET /api/popular returns null prices when no snapshots."""
    _setup()
    try:
        stocks = _get_kr_stocks(1)
        user = _create_user()
        _track_stock(user.id, stocks[0].id)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/popular")
            data = resp.json()
            assert data[0]["latest_price"] is None
            assert data[0]["price_change_pct"] is None
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_popular_max_10() -> None:
    """GET /api/popular returns max 10 stocks."""
    _setup()
    try:
        stocks = _get_kr_stocks(10)
        if len(stocks) < 10:
            pytest.skip("Not enough stocks seeded")

        user = _create_user()
        for stock in stocks:
            _track_stock(user.id, stock.id)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/popular")
            assert resp.status_code == 200
            assert len(resp.json()) <= 10
    finally:
        _teardown()


# ── Cache tests ──────────────────────────────────────────────────────


def test_cache_ttl_constant() -> None:
    """CACHE_TTL is set to 300 seconds (5 minutes)."""
    from app.api.trending import CACHE_TTL
    assert CACHE_TTL == 300
