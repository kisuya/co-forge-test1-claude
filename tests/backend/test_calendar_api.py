"""Tests for calendar API endpoints (calendar-002)."""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.calendar_event import CalendarEvent
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_calendar_api.db"


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
    if os.path.exists("test_calendar_api.db"):
        os.remove("test_calendar_api.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


def _get_kr_stock(session) -> Stock:
    return session.execute(
        select(Stock).where(Stock.market == "KRX")
    ).scalars().first()


def _create_user(session) -> User:
    user = User(
        email="calapi@test.com",
        password_hash="hashed",
        nickname="calapi",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _make_token(user_id: str) -> str:
    from app.config import get_settings
    settings = get_settings()
    return jwt.encode(
        {"sub": user_id, "type": "access", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        settings.jwt_secret_key,
        algorithm="HS256",
    )


def _seed_events() -> None:
    """Seed sample calendar events for testing."""
    factory = get_session_factory(TEST_DB_URL)
    session = factory()

    stock = _get_kr_stock(session)

    events = [
        CalendarEvent(
            event_type="central_bank",
            title="FOMC 금리 결정",
            event_date=date(2026, 3, 18),
            market="US",
            source="Federal Reserve",
        ),
        CalendarEvent(
            event_type="central_bank",
            title="한국은행 금통위",
            event_date=date(2026, 2, 27),
            market="KR",
            source="한국은행",
        ),
        CalendarEvent(
            event_type="economic",
            title="미국 CPI 발표",
            event_date=date(2026, 3, 11),
            market="US",
            source="BLS",
        ),
        CalendarEvent(
            event_type="earnings",
            title=f"{stock.name} 실적 발표",
            event_date=date(2026, 3, 15),
            market="KR",
            stock_id=stock.id,
            source="KRX",
        ),
        CalendarEvent(
            event_type="dividend",
            title="배당락일",
            event_date=date(2026, 6, 15),
            market="KR",
            source="KRX",
        ),
    ]
    session.add_all(events)
    session.commit()
    session.close()


# --- Date range query ---

@pytest.mark.asyncio
async def test_list_events_date_range() -> None:
    """GET /api/calendar returns events in date range."""
    _setup()
    _seed_events()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-02-01&end_date=2026-03-31"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert isinstance(data, list)
            assert len(data) >= 3  # BOK, FOMC, CPI, earnings
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_list_events_sorted_by_date() -> None:
    """Events are returned in ascending date order."""
    _setup()
    _seed_events()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-02-01&end_date=2026-04-30"
            )
            assert resp.status_code == 200
            data = resp.json()
            dates = [d["event_date"] for d in data]
            assert dates == sorted(dates)
    finally:
        _teardown()


# --- Market filter ---

@pytest.mark.asyncio
async def test_list_events_market_kr() -> None:
    """GET /api/calendar?market=KR returns only KR events."""
    _setup()
    _seed_events()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-02-01&end_date=2026-04-30&market=KR"
            )
            assert resp.status_code == 200
            data = resp.json()
            for item in data:
                assert item["market"] == "KR"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_list_events_market_us() -> None:
    """GET /api/calendar?market=US returns only US events."""
    _setup()
    _seed_events()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-02-01&end_date=2026-03-31&market=US"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 1
            for item in data:
                assert item["market"] == "US"
    finally:
        _teardown()


# --- Event type filter ---

@pytest.mark.asyncio
async def test_list_events_type_filter() -> None:
    """GET /api/calendar?event_type=central_bank returns only central bank events."""
    _setup()
    _seed_events()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-02-01&end_date=2026-04-30&event_type=central_bank"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 1
            for item in data:
                assert item["event_type"] == "central_bank"
    finally:
        _teardown()


# --- is_tracked flag ---

@pytest.mark.asyncio
async def test_is_tracked_unauthenticated() -> None:
    """Unauthenticated users always get is_tracked=false."""
    _setup()
    _seed_events()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-02-01&end_date=2026-04-30"
            )
            assert resp.status_code == 200
            data = resp.json()
            for item in data:
                assert item["is_tracked"] is False
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_is_tracked_authenticated() -> None:
    """Authenticated users get is_tracked=true for watchlisted stock events."""
    _setup()
    _seed_events()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        user = _create_user(session)
        stock = _get_kr_stock(session)
        wl = Watchlist(user_id=user.id, stock_id=stock.id)
        session.add(wl)
        session.commit()
        token = _make_token(str(user.id))
        session.close()

        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-03-01&end_date=2026-03-31",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert resp.status_code == 200
            data = resp.json()
            # The earnings event for the tracked stock should have is_tracked=True
            earnings = [d for d in data if d["event_type"] == "earnings"]
            assert len(earnings) >= 1
            assert earnings[0]["is_tracked"] is True

            # Non-stock events should have is_tracked=False
            non_stock = [d for d in data if d["stock_name"] is None]
            for item in non_stock:
                assert item["is_tracked"] is False
    finally:
        _teardown()


# --- Validation errors ---

@pytest.mark.asyncio
async def test_date_range_exceeds_90_days() -> None:
    """Date range > 90 days returns 422."""
    _setup()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-01-01&end_date=2026-12-31"
            )
            assert resp.status_code == 422
            data = resp.json()
            assert "90일" in data.get("message", "")
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_start_after_end_date() -> None:
    """start_date > end_date returns 422."""
    _setup()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-03-31&end_date=2026-03-01"
            )
            assert resp.status_code == 422
    finally:
        _teardown()


# --- Response format ---

@pytest.mark.asyncio
async def test_event_response_format() -> None:
    """Event response has all required fields."""
    _setup()
    _seed_events()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-02-01&end_date=2026-03-31"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 1
            item = data[0]
            assert "id" in item
            assert "event_type" in item
            assert "title" in item
            assert "description" in item
            assert "event_date" in item
            assert "market" in item
            assert "stock_name" in item
            assert "is_tracked" in item
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_stock_name_populated() -> None:
    """Events with stock_id should have stock_name populated."""
    _setup()
    _seed_events()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-03-01&end_date=2026-03-31"
            )
            assert resp.status_code == 200
            data = resp.json()
            earnings = [d for d in data if d["event_type"] == "earnings"]
            assert len(earnings) >= 1
            assert earnings[0]["stock_name"] is not None
    finally:
        _teardown()


# --- /week endpoint ---

@pytest.mark.asyncio
async def test_week_events() -> None:
    """GET /api/calendar/week returns this week's events."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        # Add an event for today (which is in this week)
        today = date.today()
        event = CalendarEvent(
            event_type="economic",
            title="이번 주 이벤트",
            event_date=today,
            market="KR",
            source="test",
        )
        session.add(event)
        session.commit()
        session.close()

        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/calendar/week")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) >= 1
            assert data[0]["title"] == "이번 주 이벤트"
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_week_events_empty() -> None:
    """GET /api/calendar/week returns empty when no events this week."""
    _setup()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/calendar/week")
            assert resp.status_code == 200
            data = resp.json()
            assert data == []
    finally:
        _teardown()


# --- No auth required ---

@pytest.mark.asyncio
async def test_no_auth_required() -> None:
    """Calendar API does not require authentication."""
    _setup()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2026-02-01&end_date=2026-02-28"
            )
            assert resp.status_code == 200

            resp = await client.get("/api/calendar/week")
            assert resp.status_code == 200
    finally:
        _teardown()


# --- Empty result ---

@pytest.mark.asyncio
async def test_empty_date_range() -> None:
    """Returns empty list when no events in date range."""
    _setup()
    try:
        app = _make_app()
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get(
                "/api/calendar?start_date=2020-01-01&end_date=2020-01-31"
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data == []
    finally:
        _teardown()
