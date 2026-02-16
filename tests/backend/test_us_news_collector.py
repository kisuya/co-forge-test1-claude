"""Tests for US news collector client (data-005)."""
from __future__ import annotations

import os
import time
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.clients.us_news_client import (
    CACHE_TTL_SECONDS,
    USNewsItem,
    clear_cache,
    fetch_us_news,
    _get_cache,
    _set_cache,
)
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import Report, ReportSource
from app.models.stock import Stock
from app.services.stock_service import seed_us_stocks

TEST_DB_URL = "sqlite:///test_us_news_collector.db"


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
    clear_cache()
    if os.path.exists("test_us_news_collector.db"):
        os.remove("test_us_news_collector.db")


# --- USNewsItem dataclass ---


def test_us_news_item_fields() -> None:
    """USNewsItem should hold correct fields."""
    item = USNewsItem(
        title="Apple hits record",
        url="https://news.example.com/1",
        source="Reuters",
        published_at=datetime(2024, 1, 15),
        summary="Apple stock rises on strong earnings.",
    )
    assert item.title == "Apple hits record"
    assert item.source == "Reuters"
    assert item.summary == "Apple stock rises on strong earnings."


def test_us_news_item_defaults() -> None:
    """USNewsItem optional fields should have defaults."""
    item = USNewsItem(title="Test", url="https://test.com", source="Test")
    assert item.published_at is None
    assert item.summary == ""


# --- Cache ---


def test_cache_stores_and_retrieves() -> None:
    """Cache should store and retrieve items within TTL."""
    clear_cache()
    items = [USNewsItem(title="cached", url="https://c.com", source="s")]
    _set_cache("AAPL", items)
    cached = _get_cache("AAPL")
    assert cached is not None
    assert len(cached) == 1
    assert cached[0].title == "cached"
    clear_cache()


def test_cache_expires_after_ttl() -> None:
    """Cache should expire after CACHE_TTL_SECONDS."""
    clear_cache()
    items = [USNewsItem(title="old", url="https://o.com", source="s")]
    _set_cache("TSLA", items)
    with patch("app.clients.us_news_client.time") as mock_time:
        mock_time.time.return_value = time.time() + CACHE_TTL_SECONDS + 1
        cached = _get_cache("TSLA")
    assert cached is None
    clear_cache()


def test_cache_ttl_is_1_hour() -> None:
    """Cache TTL should be 3600 seconds (1 hour)."""
    assert CACHE_TTL_SECONDS == 3600


def test_clear_cache() -> None:
    """clear_cache should remove all entries."""
    _set_cache("X", [])
    clear_cache()
    assert _get_cache("X") is None


# --- fetch_us_news ---


def test_fetch_returns_empty_without_api_key() -> None:
    """fetch_us_news should return empty list if NEWS_API_KEY not set."""
    clear_cache()
    with patch("app.clients.us_news_client.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(news_api_key="")
        result = fetch_us_news("AAPL", "Apple Inc.")
    assert result == []
    clear_cache()


def test_fetch_returns_cached_on_second_call() -> None:
    """Second call should return cached result without API call."""
    clear_cache()
    items = [USNewsItem(title="cached_hit", url="https://c.com", source="s")]
    _set_cache("MSFT", items)

    with patch("app.clients.us_news_client.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(news_api_key="test-key")
        result = fetch_us_news("MSFT", "Microsoft Corp.")

    assert len(result) == 1
    assert result[0].title == "cached_hit"
    clear_cache()


def test_fetch_parses_newsapi_response() -> None:
    """fetch_us_news should parse NewsAPI response correctly."""
    clear_cache()
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "ok",
        "articles": [
            {
                "title": "Apple earnings beat",
                "url": "https://news.example.com/apple",
                "source": {"name": "CNBC"},
                "publishedAt": "2024-01-15T10:30:00Z",
                "description": "Apple posted strong Q4 results.",
            },
            {
                "title": "Tech rally continues",
                "url": "https://news.example.com/tech",
                "source": {"name": "Reuters"},
                "publishedAt": "2024-01-15T08:00:00Z",
                "description": None,
            },
        ],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.clients.us_news_client.get_settings") as mock_settings, \
         patch("app.clients.us_news_client.httpx.get", return_value=mock_response):
        mock_settings.return_value = MagicMock(news_api_key="test-key")
        result = fetch_us_news("AAPL", "Apple Inc.")

    assert len(result) == 2
    assert result[0].title == "Apple earnings beat"
    assert result[0].source == "CNBC"
    assert result[0].summary == "Apple posted strong Q4 results."
    assert result[1].summary == ""
    clear_cache()


def test_fetch_returns_empty_on_api_failure() -> None:
    """fetch_us_news should return empty list on API failure."""
    clear_cache()
    with patch("app.clients.us_news_client.get_settings") as mock_settings, \
         patch("app.clients.us_news_client.httpx.get", side_effect=Exception("timeout")):
        mock_settings.return_value = MagicMock(news_api_key="test-key")
        result = fetch_us_news("AAPL", "Apple Inc.")

    assert result == []
    clear_cache()


# --- Config ---


def test_news_api_key_in_settings() -> None:
    """Settings should have news_api_key field."""
    from app.config import Settings
    import dataclasses
    field_names = [f.name for f in dataclasses.fields(Settings)]
    assert "news_api_key" in field_names


# --- ReportSource integration ---


def test_us_news_stored_as_report_source() -> None:
    """US news items should be storable as ReportSource with source_type='us_news'."""
    session = _setup()
    try:
        stock = session.query(Stock).filter(Stock.code == "AAPL").first()
        assert stock is not None

        from decimal import Decimal
        report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("195.50"),
            trigger_change_pct=5.0,
            status="pending",
        )
        session.add(report)
        session.flush()

        src = ReportSource(
            report_id=report.id,
            source_type="us_news",
            title="Apple hits record high",
            url="https://news.example.com/apple",
        )
        session.add(src)
        session.commit()

        saved = session.query(ReportSource).filter_by(
            report_id=report.id, source_type="us_news",
        ).first()
        assert saved is not None
        assert saved.title == "Apple hits record high"
    finally:
        _teardown(session)


# --- Daily limit consideration ---


def test_cache_prevents_redundant_api_calls() -> None:
    """Cache should prevent redundant API calls within 1 hour."""
    clear_cache()
    call_count = [0]
    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "ok", "articles": []}
    mock_response.raise_for_status = MagicMock()

    def counting_get(*args, **kwargs):
        call_count[0] += 1
        return mock_response

    with patch("app.clients.us_news_client.get_settings") as mock_settings, \
         patch("app.clients.us_news_client.httpx.get", side_effect=counting_get):
        mock_settings.return_value = MagicMock(news_api_key="test-key")
        fetch_us_news("NVDA", "NVIDIA Corp.")
        fetch_us_news("NVDA", "NVIDIA Corp.")
        fetch_us_news("NVDA", "NVIDIA Corp.")

    assert call_count[0] == 1
    clear_cache()
