"""Tests for US stock price collector (data-004)."""
from __future__ import annotations

import os
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy.orm import Session

from app.clients.us_client import USStockPrice, RATE_LIMIT_DELAY
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot
from app.models.stock import Stock
from app.services.stock_service import seed_us_stocks
from app.workers.us_price_collector import (
    US_MARKETS,
    collect_us_prices,
    is_us_market_open,
)

TEST_DB_URL = "sqlite:///test_us_price_collector.db"


def _setup() -> Session:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_us_stocks(session)
    return session


def _teardown(session: Session | None = None) -> None:
    if session:
        session.close()
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_us_price_collector.db"):
        os.remove("test_us_price_collector.db")


def _mock_fetch(codes: list[str]) -> list[USStockPrice]:
    """Mock price fetcher returning fake prices."""
    return [
        USStockPrice(code=c, price=Decimal("150.00"), change_pct=1.5, volume=1000000)
        for c in codes
    ]


# --- is_us_market_open ---


def test_market_open_weekday_during_hours() -> None:
    """Market should be open on weekday during trading hours (ET)."""
    # Monday 10:00 ET
    et = ZoneInfo("America/New_York")
    with patch("app.workers.us_price_collector.datetime") as mock_dt:
        mock_now = datetime(2024, 1, 8, 10, 0, 0, tzinfo=et)  # Monday
        mock_dt.now.return_value = mock_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        assert is_us_market_open() is True


def test_market_closed_weekend() -> None:
    """Market should be closed on weekends."""
    et = ZoneInfo("America/New_York")
    with patch("app.workers.us_price_collector.datetime") as mock_dt:
        mock_now = datetime(2024, 1, 6, 10, 0, 0, tzinfo=et)  # Saturday
        mock_dt.now.return_value = mock_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        assert is_us_market_open() is False


def test_market_closed_before_open() -> None:
    """Market should be closed before 09:30 ET."""
    et = ZoneInfo("America/New_York")
    with patch("app.workers.us_price_collector.datetime") as mock_dt:
        mock_now = datetime(2024, 1, 8, 9, 0, 0, tzinfo=et)  # Monday 09:00
        mock_dt.now.return_value = mock_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        assert is_us_market_open() is False


def test_market_closed_after_close() -> None:
    """Market should be closed after 16:00 ET."""
    et = ZoneInfo("America/New_York")
    with patch("app.workers.us_price_collector.datetime") as mock_dt:
        mock_now = datetime(2024, 1, 8, 16, 30, 0, tzinfo=et)  # Monday 16:30
        mock_dt.now.return_value = mock_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
        assert is_us_market_open() is False


# --- collect_us_prices ---


def test_collect_us_prices_with_mock() -> None:
    """collect_us_prices should save snapshots for US stocks."""
    session = _setup()
    try:
        count = collect_us_prices(session, fetch_fn=_mock_fetch)
        assert count >= 100
        snapshots = session.query(PriceSnapshot).count()
        assert snapshots == count
    finally:
        _teardown(session)


def test_collect_us_prices_only_us_markets() -> None:
    """collect_us_prices should only fetch US market stocks."""
    session = _setup()
    try:
        # Add a KRX stock to verify it's not collected
        from app.services.stock_service import seed_stocks
        seed_stocks(session)

        collected_codes: list[str] = []

        def tracking_fetch(codes: list[str]) -> list[USStockPrice]:
            collected_codes.extend(codes)
            return _mock_fetch(codes)

        collect_us_prices(session, fetch_fn=tracking_fetch)

        # No KRX codes should be in the collected list
        from app.data.us_stocks import SAMPLE_US_STOCKS
        us_codes = {s[0] for s in SAMPLE_US_STOCKS}
        for code in collected_codes:
            assert code in us_codes
    finally:
        _teardown(session)


def test_collect_us_prices_empty_db() -> None:
    """Empty database should return 0."""
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        count = collect_us_prices(session, fetch_fn=_mock_fetch)
        assert count == 0
    finally:
        _teardown(session)


def test_collect_us_prices_creates_price_snapshots() -> None:
    """Snapshots should have correct price data."""
    session = _setup()
    try:
        collect_us_prices(session, fetch_fn=_mock_fetch)
        snap = session.query(PriceSnapshot).first()
        assert snap is not None
        assert snap.price == Decimal("150.00")
        assert snap.change_pct == 1.5
        assert snap.volume == 1000000
    finally:
        _teardown(session)


def test_collect_skips_unknown_codes() -> None:
    """Prices for unknown codes should be skipped."""
    session = _setup()
    try:
        def fetch_with_unknown(codes: list[str]) -> list[USStockPrice]:
            result = _mock_fetch(codes)
            result.append(USStockPrice(
                code="UNKNOWN", price=Decimal("1.00"),
                change_pct=0.0, volume=0,
            ))
            return result

        count = collect_us_prices(session, fetch_fn=fetch_with_unknown)
        us_count = session.query(Stock).filter(
            Stock.market.in_(US_MARKETS)
        ).count()
        assert count == us_count
    finally:
        _teardown(session)


# --- US client ---


def test_us_stock_price_dataclass() -> None:
    """USStockPrice should hold correct fields."""
    p = USStockPrice(code="AAPL", price=Decimal("195.50"), change_pct=2.1, volume=50000)
    assert p.code == "AAPL"
    assert p.price == Decimal("195.50")
    assert p.change_pct == 2.1
    assert p.volume == 50000


def test_rate_limit_delay() -> None:
    """Rate limit delay should be 100ms."""
    assert RATE_LIMIT_DELAY == 0.1


def test_fetch_us_prices_handles_import_error() -> None:
    """fetch_us_prices should return empty list if yfinance not installed."""
    with patch.dict("sys.modules", {"yfinance": None}):
        from importlib import reload
        from app.clients import us_client
        reload(us_client)
        result = us_client.fetch_us_prices(["AAPL"])
        assert result == []
        reload(us_client)


# --- Independent from KRX collector ---


def test_independent_from_krx_collector() -> None:
    """US collector should be independent from KRX collector."""
    session = _setup()
    try:
        from app.services.stock_service import seed_stocks
        seed_stocks(session)

        us_count = collect_us_prices(session, fetch_fn=_mock_fetch)
        assert us_count >= 100

        from app.workers.price_collector import collect_prices as collect_krx
        krx_prices = [
            type("SP", (), {"code": "005930", "price": Decimal("70000"),
                            "change_pct": 1.0, "volume": 100})()
        ]
        krx_count = collect_krx(session, fetch_fn=lambda _: krx_prices)
        assert krx_count == 1

        total = session.query(PriceSnapshot).count()
        assert total == us_count + krx_count
    finally:
        _teardown(session)


# --- Celery task ---


def test_celery_task_registered() -> None:
    """collect_us_prices_task should be a registered Celery task."""
    celery_mod = pytest.importorskip("celery")
    from app.workers.us_price_collector import collect_us_prices_task
    assert hasattr(collect_us_prices_task, "delay")
    assert collect_us_prices_task.name == "collect_us_prices_task"
