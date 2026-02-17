"""Tests for briefing API endpoints (briefing-003)."""
from __future__ import annotations

import os
from datetime import date, datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.market_briefing import MarketBriefing
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_briefing_api.db"


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
    if os.path.exists("test_briefing_api.db"):
        os.remove("test_briefing_api.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


def _seed_briefings() -> None:
    """Seed sample briefings for testing."""
    factory = get_session_factory(TEST_DB_URL)
    session = factory()

    from zoneinfo import ZoneInfo
    today = datetime.now(ZoneInfo("Asia/Seoul")).date()

    # Today KR
    b1 = MarketBriefing(
        market="KR",
        date=today,
        content={
            "market": "KR",
            "date": str(today),
            "summary": "오늘 한국 시장은 상승세.",
            "key_issues": [
                {"title": "반도체 호조", "description": "수출 증가"},
            ],
            "top_movers": [
                {"stock_name": "삼성전자", "change_pct": 3.5, "reason": "HBM 기대"},
            ],
            "market_stats": {"stocks_up": 6, "stocks_down": 3, "stocks_flat": 1},
        },
    )

    # Yesterday KR
    yesterday = today - timedelta(days=1)
    b2 = MarketBriefing(
        market="KR",
        date=yesterday,
        content={
            "market": "KR",
            "date": str(yesterday),
            "summary": "어제 한국 시장은 하락세.",
            "key_issues": [],
            "top_movers": [],
            "market_stats": {"stocks_up": 2, "stocks_down": 7, "stocks_flat": 1},
        },
    )

    # Today US
    b3 = MarketBriefing(
        market="US",
        date=today,
        content={
            "market": "US",
            "date": str(today),
            "summary": "US market rose today.",
            "key_issues": [
                {"title": "Fed decision", "description": "Rate hold"},
            ],
            "top_movers": [
                {"stock_name": "Apple", "change_pct": 2.3, "reason": "Earnings beat"},
            ],
            "market_stats": {"stocks_up": 4, "stocks_down": 1, "stocks_flat": 0},
        },
    )

    session.add_all([b1, b2, b3])
    session.commit()
    session.close()


@pytest.mark.asyncio
async def test_list_briefings_default() -> None:
    """GET /api/briefings returns latest KR briefing by default."""
    _setup()
    _seed_briefings()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings")
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) == 1  # default limit=1
            assert data[0]["market"] == "KR"
            assert data[0]["summary"] is not None
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_list_briefings_limit() -> None:
    """GET /api/briefings?limit=5 returns multiple briefings."""
    _setup()
    _seed_briefings()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings?limit=5")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 2  # 2 KR briefings
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_list_briefings_us_market() -> None:
    """GET /api/briefings?market=US returns US briefings."""
    _setup()
    _seed_briefings()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings?market=US")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 1
            assert data[0]["market"] == "US"
            assert data[0]["summary"] == "US market rose today."
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_list_briefings_empty() -> None:
    """GET /api/briefings returns empty list when no data."""
    _setup()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings")
            assert resp.status_code == 200
            data = resp.json()
            assert data == []
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_today_briefing_exists() -> None:
    """GET /api/briefings/today returns today's briefing with is_today=true."""
    _setup()
    _seed_briefings()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings/today")
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_today"] is True
            assert data["market"] == "KR"
            assert data["summary"] is not None
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_today_briefing_fallback() -> None:
    """GET /api/briefings/today falls back to most recent when no today's briefing."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        # Only yesterday's briefing
        yesterday = date.today() - timedelta(days=1)
        b = MarketBriefing(
            market="KR",
            date=yesterday,
            content={
                "market": "KR",
                "date": str(yesterday),
                "summary": "Yesterday's briefing.",
                "key_issues": [],
                "top_movers": [],
            },
        )
        session.add(b)
        session.commit()
        session.close()

        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings/today")
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_today"] is False
            assert data["summary"] == "Yesterday's briefing."
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_today_briefing_none() -> None:
    """GET /api/briefings/today returns empty response when no briefings exist."""
    _setup()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings/today")
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_today"] is False
            assert data["summary"] is None
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_today_briefing_us() -> None:
    """GET /api/briefings/today?market=US returns US briefing."""
    _setup()
    _seed_briefings()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings/today?market=US")
            assert resp.status_code == 200
            data = resp.json()
            assert data["market"] == "US"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_briefing_response_format() -> None:
    """Briefing response has correct format with all fields."""
    _setup()
    _seed_briefings()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings")
            assert resp.status_code == 200
            data = resp.json()
            item = data[0]

            assert "id" in item
            assert "market" in item
            assert "date" in item
            assert "summary" in item
            assert "key_issues" in item
            assert "top_movers" in item
            assert "created_at" in item

            # key_issues structure
            if item["key_issues"]:
                issue = item["key_issues"][0]
                assert "title" in issue
                assert "description" in issue
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_no_auth_required() -> None:
    """Briefing API does not require authentication."""
    _setup()
    _seed_briefings()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # No Authorization header
            resp = await client.get("/api/briefings")
            assert resp.status_code == 200

            resp = await client.get("/api/briefings/today")
            assert resp.status_code == 200
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_briefing_date_ordering() -> None:
    """Briefings are returned in descending date order."""
    _setup()
    _seed_briefings()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings?limit=10")
            assert resp.status_code == 200
            data = resp.json()
            if len(data) >= 2:
                assert data[0]["date"] >= data[1]["date"]
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_invalid_market_param() -> None:
    """Invalid market parameter returns 422."""
    _setup()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/briefings?market=INVALID")
            assert resp.status_code == 422
    finally:
        _teardown()
