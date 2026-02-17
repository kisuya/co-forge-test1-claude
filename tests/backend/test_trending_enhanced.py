"""Tests for enhanced trending/popular APIs (trending-002)."""
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

TEST_DB_URL = "sqlite:///test_trending_enhanced.db"


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
    if os.path.exists("test_trending_enhanced.db"):
        os.remove("test_trending_enhanced.db")


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


def _get_us_stocks(count=1) -> list[Stock]:
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    stocks = list(
        session.execute(
            select(Stock).where(Stock.market.in_(("NYSE", "NASDAQ"))).limit(count)
        ).scalars().all()
    )
    session.close()
    return stocks


def _create_user(email="enhanced@example.com") -> User:
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


_SENTINEL = object()


def _create_report(stock_id, change_pct, hours_ago=1, summary=_SENTINEL) -> Report:
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    now = datetime.now(timezone.utc)
    report = Report(
        stock_id=stock_id,
        trigger_price=Decimal("10000"),
        trigger_change_pct=change_pct,
        status="completed",
        summary="Test report summary" if summary is _SENTINEL else summary,
        created_at=now - timedelta(hours=hours_ago),
    )
    session.add(report)
    session.commit()
    session.refresh(report)
    session.close()
    return report


# ── Market filter tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trending_market_filter_kr() -> None:
    """GET /api/trending?market=KR returns only KRX stocks."""
    _setup()
    try:
        kr_stocks = _get_kr_stocks(1)
        us_stocks = _get_us_stocks(1)
        if not us_stocks:
            pytest.skip("No US stocks seeded")

        _create_report(kr_stocks[0].id, 5.0, hours_ago=1)
        _create_report(us_stocks[0].id, 8.0, hours_ago=1)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending?market=KR")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["market"] == "KRX"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_market_filter_us() -> None:
    """GET /api/trending?market=US returns only NYSE/NASDAQ stocks."""
    _setup()
    try:
        kr_stocks = _get_kr_stocks(1)
        us_stocks = _get_us_stocks(1)
        if not us_stocks:
            pytest.skip("No US stocks seeded")

        _create_report(kr_stocks[0].id, 5.0, hours_ago=1)
        _create_report(us_stocks[0].id, 8.0, hours_ago=1)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending?market=US")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["market"] in ("NYSE", "NASDAQ")
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_market_filter_all() -> None:
    """GET /api/trending?market=ALL returns all markets (default)."""
    _setup()
    try:
        kr_stocks = _get_kr_stocks(1)
        us_stocks = _get_us_stocks(1)
        if not us_stocks:
            pytest.skip("No US stocks seeded")

        _create_report(kr_stocks[0].id, 5.0, hours_ago=1)
        _create_report(us_stocks[0].id, 8.0, hours_ago=1)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending?market=ALL")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_popular_market_filter_kr() -> None:
    """GET /api/popular?market=KR returns only KRX stocks."""
    _setup()
    try:
        kr_stocks = _get_kr_stocks(1)
        us_stocks = _get_us_stocks(1)
        if not us_stocks:
            pytest.skip("No US stocks seeded")

        user1 = _create_user("u1@example.com")
        user2 = _create_user("u2@example.com")
        _track_stock(user1.id, kr_stocks[0].id)
        _track_stock(user2.id, kr_stocks[0].id)
        _track_stock(user1.id, us_stocks[0].id)
        _track_stock(user2.id, us_stocks[0].id)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/popular?market=KR")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["market"] == "KRX"
    finally:
        _teardown()


# ── Period filter tests ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trending_period_daily() -> None:
    """GET /api/trending?period=daily returns only last 24h events."""
    _setup()
    try:
        stocks = _get_kr_stocks(2)
        _create_report(stocks[0].id, 5.0, hours_ago=1)   # within 24h
        _create_report(stocks[1].id, 10.0, hours_ago=25)  # older than 24h

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending?period=daily")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["change_pct"] == 5.0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_period_weekly() -> None:
    """GET /api/trending?period=weekly returns last 7 days events."""
    _setup()
    try:
        stocks = _get_kr_stocks(3)
        _create_report(stocks[0].id, 5.0, hours_ago=1)     # within 24h
        _create_report(stocks[1].id, 8.0, hours_ago=72)    # 3 days ago (within 7d)
        _create_report(stocks[2].id, 10.0, hours_ago=200)  # 8+ days ago (outside 7d)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending?period=weekly")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
    finally:
        _teardown()


# ── Minimum tracking count tests ─────────────────────────────────────


@pytest.mark.asyncio
async def test_popular_min_tracking_count() -> None:
    """GET /api/popular?min_count=2 excludes stocks with tracking_count < 2."""
    _setup()
    try:
        stocks = _get_kr_stocks(2)
        user1 = _create_user("u1@example.com")
        user2 = _create_user("u2@example.com")

        # Stock 0: 2 trackers (included)
        _track_stock(user1.id, stocks[0].id)
        _track_stock(user2.id, stocks[0].id)
        # Stock 1: 1 tracker (excluded)
        _track_stock(user1.id, stocks[1].id)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/popular?min_count=2")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["tracking_count"] >= 2
    finally:
        _teardown()


# ── Summary data tests ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_trending_mini_summary() -> None:
    """GET /api/trending response includes mini_summary field."""
    _setup()
    try:
        stocks = _get_kr_stocks(1)
        _create_report(stocks[0].id, 5.0, hours_ago=1, summary="반도체 수요 급증")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert "mini_summary" in data[0]
            assert data[0]["mini_summary"] == "반도체 수요 급증"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_mini_summary_null() -> None:
    """GET /api/trending mini_summary is null when report has no summary."""
    _setup()
    try:
        stocks = _get_kr_stocks(1)
        _create_report(stocks[0].id, 5.0, hours_ago=1, summary=None)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            data = resp.json()
            assert data[0]["mini_summary"] is None
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_popular_latest_change_reason() -> None:
    """GET /api/popular response includes latest_change_reason field."""
    _setup()
    try:
        stocks = _get_kr_stocks(1)
        user1 = _create_user("u1@example.com")
        user2 = _create_user("u2@example.com")
        _track_stock(user1.id, stocks[0].id)
        _track_stock(user2.id, stocks[0].id)
        _create_report(stocks[0].id, 3.0, hours_ago=2, summary="실적 발표 영향")
        _create_report(stocks[0].id, 5.0, hours_ago=1, summary="외국인 매수세")

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/popular")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert "latest_change_reason" in data[0]
            # Should be most recent report summary
            assert data[0]["latest_change_reason"] == "외국인 매수세"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_popular_latest_change_reason_null() -> None:
    """GET /api/popular latest_change_reason is null when no reports."""
    _setup()
    try:
        stocks = _get_kr_stocks(1)
        user1 = _create_user("u1@example.com")
        user2 = _create_user("u2@example.com")
        _track_stock(user1.id, stocks[0].id)
        _track_stock(user2.id, stocks[0].id)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/popular")
            data = resp.json()
            assert len(data) == 1
            assert data[0]["latest_change_reason"] is None
    finally:
        _teardown()


# ── Default behavior tests ───────────────────────────────────────────


@pytest.mark.asyncio
async def test_trending_default_market_all() -> None:
    """GET /api/trending without market param defaults to ALL."""
    _setup()
    try:
        kr_stocks = _get_kr_stocks(1)
        us_stocks = _get_us_stocks(1)
        if not us_stocks:
            pytest.skip("No US stocks seeded")

        _create_report(kr_stocks[0].id, 5.0, hours_ago=1)
        _create_report(us_stocks[0].id, 8.0, hours_ago=1)

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_trending_default_period_daily() -> None:
    """GET /api/trending without period param defaults to daily."""
    _setup()
    try:
        stocks = _get_kr_stocks(2)
        _create_report(stocks[0].id, 5.0, hours_ago=1)
        _create_report(stocks[1].id, 10.0, hours_ago=48)  # 2 days ago

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/trending")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
    finally:
        _teardown()
