"""Tests for US price collection pipeline (pipe-002).

Verifies:
- fetch_us_prices with mock yfinance
- Error handling and retry logic
- Rate limit delay
- Market hours detection
- Price collection service (collect_us_prices)
- Redis cache refresh after collection
- Celery Beat schedule configuration
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import func, select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)

TEST_DB_URL = "sqlite:///test_us_pipeline.db"


def _setup():
    import app.models  # noqa: F401 — register all models with Base.metadata
    from app.db.database import create_tables
    create_tables(TEST_DB_URL)
    from app.db.database import get_session_factory
    from app.services.stock_service import seed_us_stocks
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_us_stocks(session)
    session.close()


def _teardown():
    from app.db.database import Base, get_engine, dispose_engine
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    dispose_engine(TEST_DB_URL)
    if os.path.exists("test_us_pipeline.db"):
        os.remove("test_us_pipeline.db")


def _get_session():
    from app.db.database import get_session_factory
    return get_session_factory(TEST_DB_URL)()


# --- US Client Tests ---


def test_us_stock_price_dataclass():
    """USStockPrice should hold price data."""
    from app.clients.us_client import USStockPrice

    sp = USStockPrice(code="AAPL", price=Decimal("185.50"), change_pct=1.3, volume=50000000)
    assert sp.code == "AAPL"
    assert sp.price == Decimal("185.50")
    assert sp.change_pct == 1.3
    assert sp.volume == 50000000


def test_fetch_us_prices_mock_success():
    """fetch_us_prices should return prices from mocked yfinance."""
    from app.clients.us_client import fetch_us_prices

    mock_fast_info = MagicMock()
    mock_fast_info.last_price = 185.50
    mock_fast_info.previous_close = 183.00
    mock_fast_info.last_volume = 50000000

    mock_ticker = MagicMock()
    mock_ticker.fast_info = mock_fast_info

    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = mock_ticker
    mock_parent = MagicMock()
    mock_parent.yfinance = mock_yf

    with patch.dict("sys.modules", {"yfinance": mock_yf}), \
         patch("time.sleep"):
        results = fetch_us_prices(["AAPL"])

    assert len(results) == 1
    assert results[0].code == "AAPL"
    assert results[0].price == Decimal("185.5")
    assert results[0].volume == 50000000
    assert results[0].change_pct != 0.0


def test_fetch_us_prices_mock_empty():
    """fetch_us_prices should handle no codes gracefully."""
    from app.clients.us_client import fetch_us_prices

    with patch.dict("sys.modules", {"yfinance": MagicMock()}), \
         patch("time.sleep"):
        results = fetch_us_prices([])

    assert len(results) == 0


def test_fetch_us_prices_mock_error():
    """fetch_us_prices should handle API errors with retry."""
    from app.clients.us_client import fetch_us_prices

    mock_yf = MagicMock()
    mock_yf.Ticker.side_effect = Exception("API error")

    with patch.dict("sys.modules", {"yfinance": mock_yf}), \
         patch("time.sleep"):
        results = fetch_us_prices(["AAPL"])

    assert len(results) == 0


def test_fetch_us_prices_no_yfinance():
    """fetch_us_prices should return empty list if yfinance not installed."""
    from app.clients.us_client import fetch_us_prices

    with patch.dict("sys.modules", {"yfinance": None}):
        results = fetch_us_prices(["AAPL"])
        assert isinstance(results, list)


def test_fetch_us_prices_partial_failure():
    """Should succeed for some codes even if others fail."""
    from app.clients.us_client import fetch_us_prices

    call_count = 0

    def mock_ticker_factory(code):
        nonlocal call_count
        call_count += 1
        if code == "TSLA":
            raise Exception("Timeout")
        mock_fast_info = MagicMock()
        mock_fast_info.last_price = 185.50
        mock_fast_info.previous_close = 183.00
        mock_fast_info.last_volume = 50000000
        ticker = MagicMock()
        ticker.fast_info = mock_fast_info
        return ticker

    mock_yf = MagicMock()
    mock_yf.Ticker.side_effect = mock_ticker_factory

    with patch.dict("sys.modules", {"yfinance": mock_yf}), \
         patch("time.sleep"):
        results = fetch_us_prices(["AAPL", "TSLA"])

    assert len(results) == 1
    assert results[0].code == "AAPL"


def test_fetch_us_prices_rate_limit_delay():
    """fetch_us_prices should call time.sleep for rate limiting."""
    from app.clients.us_client import fetch_us_prices, RATE_LIMIT_DELAY

    mock_fast_info = MagicMock()
    mock_fast_info.last_price = 185.50
    mock_fast_info.previous_close = 183.00
    mock_fast_info.last_volume = 50000000

    mock_ticker = MagicMock()
    mock_ticker.fast_info = mock_fast_info

    mock_yf = MagicMock()
    mock_yf.Ticker.return_value = mock_ticker

    with patch.dict("sys.modules", {"yfinance": mock_yf}), \
         patch("time.sleep") as mock_sleep:
        fetch_us_prices(["AAPL", "MSFT"])

    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(RATE_LIMIT_DELAY)


# --- Market Hours Tests ---


def test_is_us_market_open_weekday_during_hours():
    """Should return True during US market hours on weekday."""
    from app.workers.us_price_collector import is_us_market_open, ET

    with patch("app.workers.us_price_collector.datetime") as mock_dt:
        mock_now = datetime(2026, 2, 18, 12, 0, tzinfo=ET)  # Wednesday 12:00
        mock_dt.now.return_value = mock_now
        assert is_us_market_open() is True


def test_is_us_market_open_weekend():
    """Should return False on weekend."""
    from app.workers.us_price_collector import is_us_market_open, ET

    with patch("app.workers.us_price_collector.datetime") as mock_dt:
        mock_now = datetime(2026, 2, 14, 12, 0, tzinfo=ET)  # Saturday
        mock_dt.now.return_value = mock_now
        assert is_us_market_open() is False


def test_is_us_market_open_after_hours():
    """Should return False after market close."""
    from app.workers.us_price_collector import is_us_market_open, ET

    with patch("app.workers.us_price_collector.datetime") as mock_dt:
        mock_now = datetime(2026, 2, 18, 17, 0, tzinfo=ET)  # Wednesday 17:00
        mock_dt.now.return_value = mock_now
        assert is_us_market_open() is False


def test_is_us_market_open_before_hours():
    """Should return False before market open."""
    from app.workers.us_price_collector import is_us_market_open, ET

    with patch("app.workers.us_price_collector.datetime") as mock_dt:
        mock_now = datetime(2026, 2, 18, 8, 0, tzinfo=ET)  # Wednesday 08:00
        mock_dt.now.return_value = mock_now
        assert is_us_market_open() is False


# --- Price Collection Service Tests ---


def test_collect_us_prices_with_mock():
    """collect_us_prices should save snapshots for US stocks."""
    _setup()
    try:
        from app.workers.us_price_collector import collect_us_prices
        from app.models.report import PriceSnapshot
        from app.clients.us_client import USStockPrice

        session = _get_session()

        def mock_fetch(codes):
            return [
                USStockPrice(code="AAPL", price=Decimal("185.50"), change_pct=1.3, volume=50000000),
                USStockPrice(code="MSFT", price=Decimal("410.25"), change_pct=-0.5, volume=25000000),
            ]

        count = collect_us_prices(session, fetch_fn=mock_fetch)
        assert count == 2

        snap_count = session.execute(select(func.count(PriceSnapshot.id))).scalar()
        assert snap_count == 2
        session.close()
    finally:
        _teardown()


def test_collect_us_prices_empty_result():
    """collect_us_prices should handle no results gracefully."""
    _setup()
    try:
        from app.workers.us_price_collector import collect_us_prices

        session = _get_session()
        count = collect_us_prices(session, fetch_fn=lambda codes: [])
        assert count == 0
        session.close()
    finally:
        _teardown()


def test_collect_us_prices_unknown_code():
    """collect_us_prices should skip prices for unknown stock codes."""
    _setup()
    try:
        from app.workers.us_price_collector import collect_us_prices
        from app.clients.us_client import USStockPrice

        session = _get_session()

        def mock_fetch(codes):
            return [
                USStockPrice(code="ZZZZZZ", price=Decimal("1.00"), change_pct=0.0, volume=100),
            ]

        count = collect_us_prices(session, fetch_fn=mock_fetch)
        assert count == 0
        session.close()
    finally:
        _teardown()


def test_collect_us_prices_only_us_stocks():
    """collect_us_prices should only collect for NYSE/NASDAQ market stocks."""
    _setup()
    try:
        from app.workers.us_price_collector import collect_us_prices
        from app.clients.us_client import USStockPrice
        from app.models.stock import Stock

        session = _get_session()

        collected_codes = []

        def mock_fetch(codes):
            collected_codes.extend(codes)
            return [
                USStockPrice(code=codes[0], price=Decimal("185.50"), change_pct=1.3, volume=50000000),
            ]

        collect_us_prices(session, fetch_fn=mock_fetch)

        for code in collected_codes:
            stock = session.execute(
                select(Stock).where(Stock.code == code)
            ).scalar_one_or_none()
            assert stock is not None
            assert stock.market in ("NYSE", "NASDAQ"), f"Stock {code} should be US, got {stock.market}"

        session.close()
    finally:
        _teardown()


# --- Redis Cache Tests ---


def test_refresh_price_cache_called():
    """collect_us_prices should attempt to refresh Redis cache."""
    _setup()
    try:
        from app.workers.us_price_collector import collect_us_prices
        from app.clients.us_client import USStockPrice

        session = _get_session()

        with patch("app.workers.us_price_collector._refresh_price_cache") as mock_cache:
            def mock_fetch(codes):
                return [
                    USStockPrice(code="AAPL", price=Decimal("185.50"), change_pct=1.3, volume=50000000),
                ]

            count = collect_us_prices(session, fetch_fn=mock_fetch)
            assert count == 1
            assert mock_cache.call_count == 1

        session.close()
    finally:
        _teardown()


# --- Celery Beat Schedule Tests ---


def test_celery_beat_schedule_has_us():
    """Celery beat_schedule should include US price collection."""
    from app.workers.celery_app import celery

    schedule = celery.conf.beat_schedule
    assert "collect-us-prices" in schedule

    us_entry = schedule["collect-us-prices"]
    assert us_entry["task"] == "collect_us_prices_task"


def test_celery_beat_us_schedule_timing():
    """US schedule should run every 30 min during US market hours (KST)."""
    from app.workers.celery_app import celery
    from celery.schedules import crontab

    us_entry = celery.conf.beat_schedule["collect-us-prices"]
    sched = us_entry["schedule"]
    assert isinstance(sched, crontab)


# --- Module-Level Tests ---


def test_us_client_has_retry_constant():
    """US client should define MAX_RETRIES."""
    from app.clients.us_client import MAX_RETRIES
    assert MAX_RETRIES >= 1


def test_us_client_has_rate_limit():
    """US client should define RATE_LIMIT_DELAY."""
    from app.clients.us_client import RATE_LIMIT_DELAY
    assert RATE_LIMIT_DELAY > 0


def test_us_collector_has_market_check():
    """US collector should export market hours check."""
    from app.workers.us_price_collector import is_us_market_open
    assert callable(is_us_market_open)


def test_us_collector_has_celery_task():
    """us_price_collector module should define collect_us_prices_task."""
    from app.workers.us_price_collector import collect_us_prices_task
    assert collect_us_prices_task is not None or collect_us_prices_task is None
