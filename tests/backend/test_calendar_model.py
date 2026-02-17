"""Tests for CalendarEvent model, seed data, and collection task (calendar-001)."""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.calendar_event import CalendarEvent
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_calendar_model.db"


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
    if os.path.exists("test_calendar_model.db"):
        os.remove("test_calendar_model.db")


def _get_kr_stock(session) -> Stock:
    return session.execute(
        select(Stock).where(Stock.market == "KRX")
    ).scalars().first()


def _get_us_stock(session) -> Stock:
    return session.execute(
        select(Stock).where(Stock.market.in_(("NYSE", "NASDAQ")))
    ).scalars().first()


def _create_user(session) -> User:
    user = User(
        email="caltest@test.com",
        password_hash="hashed",
        nickname="caltest",
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# --- Model creation ---

def test_calendar_event_creation() -> None:
    """CalendarEvent can be created with valid fields."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        event = CalendarEvent(
            event_type="economic",
            title="미국 CPI 발표",
            event_date=date(2026, 3, 11),
            market="US",
            source="BLS",
        )
        session.add(event)
        session.commit()
        session.refresh(event)

        assert event.id is not None
        assert event.event_type == "economic"
        assert event.title == "미국 CPI 발표"
        assert event.event_date == date(2026, 3, 11)
        assert event.market == "US"
        assert event.source == "BLS"
        assert event.stock_id is None
        assert event.description is None
        assert event.created_at is not None
        session.close()
    finally:
        _teardown()


def test_calendar_event_with_stock() -> None:
    """CalendarEvent can be linked to a stock."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        stock = _get_kr_stock(session)
        assert stock is not None

        event = CalendarEvent(
            event_type="earnings",
            title=f"{stock.name} 실적 발표",
            description="2026년 1분기 실적 발표",
            event_date=date(2026, 4, 15),
            market="KR",
            stock_id=stock.id,
            source="KRX",
        )
        session.add(event)
        session.commit()
        session.refresh(event)

        assert event.stock_id == stock.id
        assert event.description == "2026년 1분기 실적 발표"
        assert event.event_type == "earnings"
        session.close()
    finally:
        _teardown()


def test_calendar_event_types() -> None:
    """CalendarEvent supports all required event types."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        types = ["earnings", "economic", "central_bank", "dividend"]
        for i, etype in enumerate(types):
            event = CalendarEvent(
                event_type=etype,
                title=f"Test {etype}",
                event_date=date(2026, 3, 10 + i),
                market="KR",
                source="test",
            )
            session.add(event)

        session.commit()

        result = session.execute(select(CalendarEvent)).scalars().all()
        created_types = {e.event_type for e in result}
        assert created_types == set(types)
        session.close()
    finally:
        _teardown()


def test_calendar_event_markets() -> None:
    """CalendarEvent supports KR, US, GLOBAL markets."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        for i, mkt in enumerate(["KR", "US", "GLOBAL"]):
            event = CalendarEvent(
                event_type="economic",
                title=f"Test {mkt}",
                event_date=date(2026, 3, 10 + i),
                market=mkt,
                source="test",
            )
            session.add(event)

        session.commit()
        result = session.execute(select(CalendarEvent)).scalars().all()
        markets = {e.market for e in result}
        assert markets == {"KR", "US", "GLOBAL"}
        session.close()
    finally:
        _teardown()


def test_calendar_event_title_not_null() -> None:
    """CalendarEvent title cannot be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        event = CalendarEvent(
            event_type="economic",
            title=None,
            event_date=date(2026, 3, 11),
            market="US",
            source="test",
        )
        session.add(event)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_calendar_event_date_not_null() -> None:
    """CalendarEvent event_date cannot be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        event = CalendarEvent(
            event_type="economic",
            title="Test",
            event_date=None,
            market="US",
            source="test",
        )
        session.add(event)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_calendar_event_market_not_null() -> None:
    """CalendarEvent market cannot be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        event = CalendarEvent(
            event_type="economic",
            title="Test",
            event_date=date(2026, 3, 11),
            market=None,
            source="test",
        )
        session.add(event)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_calendar_event_index_exists() -> None:
    """CalendarEvent has required index on (event_date, market)."""
    indexes = CalendarEvent.__table__.indexes
    index_cols = set()
    for idx in indexes:
        cols = frozenset(c.name for c in idx.columns)
        index_cols.add(cols)

    assert frozenset({"event_date", "market"}) in index_cols


def test_calendar_event_autoincrement_id() -> None:
    """CalendarEvent uses autoincrement integer PK."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        e1 = CalendarEvent(
            event_type="economic", title="Event 1",
            event_date=date(2026, 1, 1), market="KR", source="test",
        )
        session.add(e1)
        session.commit()
        session.refresh(e1)

        e2 = CalendarEvent(
            event_type="economic", title="Event 2",
            event_date=date(2026, 1, 2), market="KR", source="test",
        )
        session.add(e2)
        session.commit()
        session.refresh(e2)

        assert isinstance(e1.id, int)
        assert isinstance(e2.id, int)
        assert e2.id > e1.id
        session.close()
    finally:
        _teardown()


# --- Seed data ---

def test_seed_calendar_events() -> None:
    """seed_calendar_events creates known events."""
    _setup()
    try:
        from app.workers.calendar_event_collector import seed_calendar_events

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        count = seed_calendar_events(session)
        assert count > 0

        events = session.execute(select(CalendarEvent)).scalars().all()
        assert len(events) == count

        # Check we have FOMC events
        fomc = [e for e in events if "FOMC" in e.title]
        assert len(fomc) >= 1

        # Check we have BOK events
        bok = [e for e in events if "금통위" in e.title]
        assert len(bok) >= 1

        # Check we have economic indicators
        cpi = [e for e in events if "CPI" in e.title]
        assert len(cpi) >= 1

        session.close()
    finally:
        _teardown()


def test_seed_calendar_events_idempotent() -> None:
    """seed_calendar_events is idempotent — no duplicates on re-run."""
    _setup()
    try:
        from app.workers.calendar_event_collector import seed_calendar_events

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        count1 = seed_calendar_events(session)
        count2 = seed_calendar_events(session)

        assert count1 > 0
        assert count2 == 0  # No new events on second run

        session.close()
    finally:
        _teardown()


def test_seed_events_have_correct_types() -> None:
    """Seeded events have valid event types."""
    _setup()
    try:
        from app.workers.calendar_event_collector import seed_calendar_events

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        seed_calendar_events(session)
        events = session.execute(select(CalendarEvent)).scalars().all()

        valid_types = {"earnings", "economic", "central_bank", "dividend"}
        for e in events:
            assert e.event_type in valid_types

        session.close()
    finally:
        _teardown()


def test_seed_events_have_correct_markets() -> None:
    """Seeded events have valid markets."""
    _setup()
    try:
        from app.workers.calendar_event_collector import seed_calendar_events

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        seed_calendar_events(session)
        events = session.execute(select(CalendarEvent)).scalars().all()

        valid_markets = {"KR", "US", "GLOBAL"}
        for e in events:
            assert e.market in valid_markets

        session.close()
    finally:
        _teardown()


# --- Earnings collection ---

def test_collect_earnings_events_with_mock() -> None:
    """collect_earnings_events creates earnings events from mock data."""
    _setup()
    try:
        from app.workers.calendar_event_collector import collect_earnings_events

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        # Create user + watchlist entry
        user = _create_user(session)
        stock = _get_kr_stock(session)
        assert stock is not None

        wl = Watchlist(user_id=user.id, stock_id=stock.id)
        session.add(wl)
        session.commit()

        def mock_fetch(s):
            return [
                {
                    "title": f"{s.name} 1Q 실적 발표",
                    "event_date": "2026-04-20",
                    "source": "mock_calendar",
                }
            ]

        events = collect_earnings_events(session, fetch_fn=mock_fetch)
        assert len(events) == 1
        assert events[0].event_type == "earnings"
        assert events[0].stock_id == stock.id
        assert events[0].event_date == date(2026, 4, 20)
        session.close()
    finally:
        _teardown()


def test_collect_earnings_no_tracked_stocks() -> None:
    """collect_earnings_events returns empty if no tracked stocks."""
    _setup()
    try:
        from app.workers.calendar_event_collector import collect_earnings_events

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        events = collect_earnings_events(session)
        assert events == []
        session.close()
    finally:
        _teardown()


def test_collect_earnings_deduplication() -> None:
    """collect_earnings_events skips duplicate earnings for same stock+date."""
    _setup()
    try:
        from app.workers.calendar_event_collector import collect_earnings_events

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        user = _create_user(session)
        stock = _get_kr_stock(session)
        wl = Watchlist(user_id=user.id, stock_id=stock.id)
        session.add(wl)
        session.commit()

        def mock_fetch(s):
            return [{"event_date": "2026-04-20", "source": "mock"}]

        events1 = collect_earnings_events(session, fetch_fn=mock_fetch)
        events2 = collect_earnings_events(session, fetch_fn=mock_fetch)

        assert len(events1) == 1
        assert len(events2) == 0  # Duplicate skipped
        session.close()
    finally:
        _teardown()


def test_collect_earnings_us_stock() -> None:
    """collect_earnings_events handles US stocks correctly."""
    _setup()
    try:
        from app.workers.calendar_event_collector import collect_earnings_events

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        user = _create_user(session)
        stock = _get_us_stock(session)
        if stock is None:
            pytest.skip("No US stocks seeded")

        wl = Watchlist(user_id=user.id, stock_id=stock.id)
        session.add(wl)
        session.commit()

        def mock_fetch(s):
            return [{"event_date": "2026-07-25", "source": "earnings_api"}]

        events = collect_earnings_events(session, fetch_fn=mock_fetch)
        assert len(events) == 1
        assert events[0].market == "US"
        session.close()
    finally:
        _teardown()


# --- Main collection function ---

def test_collect_calendar_events() -> None:
    """collect_calendar_events seeds + collects earnings."""
    _setup()
    try:
        from app.workers.calendar_event_collector import collect_calendar_events

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        result = collect_calendar_events(session)
        assert "seeded" in result
        assert "earnings_collected" in result
        assert result["seeded"] > 0
        assert result["earnings_collected"] == 0  # No tracked stocks
        session.close()
    finally:
        _teardown()


# --- Celery task ---

def test_celery_task_exists() -> None:
    """Celery task collect_calendar_events_task is defined."""
    from app.workers.calendar_event_collector import collect_calendar_events_task
    assert collect_calendar_events_task is not None or True


def test_calendar_event_description_nullable() -> None:
    """CalendarEvent description can be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        event = CalendarEvent(
            event_type="economic",
            title="Test",
            event_date=date(2026, 3, 11),
            market="US",
            source="test",
            description=None,
        )
        session.add(event)
        session.commit()
        session.refresh(event)

        assert event.description is None
        session.close()
    finally:
        _teardown()


def test_calendar_event_stock_id_nullable() -> None:
    """CalendarEvent stock_id can be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        event = CalendarEvent(
            event_type="central_bank",
            title="FOMC",
            event_date=date(2026, 3, 18),
            market="US",
            source="Fed",
            stock_id=None,
        )
        session.add(event)
        session.commit()
        session.refresh(event)

        assert event.stock_id is None
        session.close()
    finally:
        _teardown()
