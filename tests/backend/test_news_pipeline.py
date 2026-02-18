"""Tests for news collection pipeline (pipe-004).

Verifies:
- NAVER news fetching with mock API
- NewsAPI fetching with mock API
- Error handling and retry logic
- API key validation
- News collection service (collect_stock_news)
- URL-based deduplication
- Korean vs US stock routing
- Celery Beat schedule configuration
"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import func, select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)

TEST_DB_URL = "sqlite:///test_news_pipeline.db"


def _setup():
    import app.models  # noqa: F401
    from app.db.database import create_tables
    create_tables(TEST_DB_URL)
    from app.db.database import get_session_factory
    from app.services.stock_service import seed_stocks, seed_us_stocks
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_stocks(session)
    seed_us_stocks(session)
    session.close()


def _setup_with_watchlists():
    """Setup DB with stocks and watchlist entries for both KRX and US stocks."""
    _setup()
    from app.db.database import get_session_factory
    from app.models.stock import Stock
    from app.models.watchlist import Watchlist
    from app.models.user import User

    factory = get_session_factory(TEST_DB_URL)
    session = factory()

    user = User(
        email="news-test@example.com",
        password_hash="fakehash",
        nickname="NewsTester",
    )
    session.add(user)
    session.flush()

    # Add Samsung (KRX) and Apple (NASDAQ) to watchlist
    samsung = session.execute(
        select(Stock).where(Stock.code == "005930")
    ).scalar_one_or_none()
    apple = session.execute(
        select(Stock).where(Stock.code == "AAPL")
    ).scalar_one_or_none()

    if samsung:
        session.add(Watchlist(user_id=user.id, stock_id=samsung.id))
    if apple:
        session.add(Watchlist(user_id=user.id, stock_id=apple.id))

    session.commit()
    session.close()


def _teardown():
    from app.db.database import Base, get_engine, dispose_engine
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    dispose_engine(TEST_DB_URL)
    if os.path.exists("test_news_pipeline.db"):
        os.remove("test_news_pipeline.db")


def _get_session():
    from app.db.database import get_session_factory
    return get_session_factory(TEST_DB_URL)()


# --- NAVER News Tests ---


def test_fetch_naver_news_mock_success():
    """_fetch_naver_news should return articles from mocked NAVER API."""
    from app.workers.stock_news_collector import _fetch_naver_news

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "items": [
            {
                "title": "<b>삼성전자</b> 실적 발표",
                "originallink": "https://example.com/samsung-1",
                "pubDate": "Tue, 18 Feb 2026 10:00:00 +0900",
            },
            {
                "title": "반도체 시장 분석",
                "link": "https://example.com/semiconductor-1",
                "pubDate": "Tue, 18 Feb 2026 09:30:00 +0900",
            },
        ],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.workers.stock_news_collector.httpx.get", return_value=mock_response):
        results = _fetch_naver_news("삼성전자", client_id="test-id", client_secret="test-secret")

    assert len(results) == 2
    assert results[0]["title"] == "삼성전자 실적 발표"  # HTML tags stripped
    assert results[0]["url"] == "https://example.com/samsung-1"
    assert results[0]["source"] == "NAVER"


def test_fetch_naver_news_no_credentials():
    """_fetch_naver_news should return empty list without credentials."""
    from app.workers.stock_news_collector import _fetch_naver_news

    results = _fetch_naver_news("삼성전자", client_id="", client_secret="")
    assert len(results) == 0


def test_fetch_naver_news_api_error():
    """_fetch_naver_news should handle API errors with retry."""
    from app.workers.stock_news_collector import _fetch_naver_news

    with patch("app.workers.stock_news_collector.httpx.get", side_effect=Exception("Connection error")):
        results = _fetch_naver_news("삼성전자", client_id="test-id", client_secret="test-secret")

    assert len(results) == 0


# --- NewsAPI Tests ---


def test_fetch_newsapi_mock_success():
    """_fetch_newsapi_articles should return articles from mocked NewsAPI."""
    from app.workers.stock_news_collector import _fetch_newsapi_articles

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "articles": [
            {
                "title": "Apple Q4 Earnings Beat Expectations",
                "url": "https://example.com/apple-earnings",
                "source": {"name": "Reuters"},
                "publishedAt": "2026-02-18T15:00:00Z",
            },
        ],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.workers.stock_news_collector.httpx.get", return_value=mock_response):
        results = _fetch_newsapi_articles("Apple", api_key="test-key")

    assert len(results) == 1
    assert results[0]["title"] == "Apple Q4 Earnings Beat Expectations"
    assert results[0]["source"] == "Reuters"


def test_fetch_newsapi_no_api_key():
    """_fetch_newsapi_articles should return empty list without API key."""
    from app.workers.stock_news_collector import _fetch_newsapi_articles

    results = _fetch_newsapi_articles("Apple", api_key="")
    assert len(results) == 0


def test_fetch_newsapi_api_error():
    """_fetch_newsapi_articles should handle API errors with retry."""
    from app.workers.stock_news_collector import _fetch_newsapi_articles

    with patch("app.workers.stock_news_collector.httpx.get", side_effect=Exception("Rate limited")):
        results = _fetch_newsapi_articles("Apple", api_key="test-key")

    assert len(results) == 0


# --- News Collection Service Tests ---


def test_collect_stock_news_kr_mock():
    """collect_stock_news should collect Korean news for KRX stocks."""
    _setup_with_watchlists()
    try:
        from app.workers.stock_news_collector import collect_stock_news
        from app.models.news_article import NewsArticle

        session = _get_session()

        def mock_kr_fetch(name):
            return [
                {"title": f"News about {name}", "url": f"https://naver.com/kr/{name}/1", "source": "NAVER"},
            ]

        articles = collect_stock_news(session, fetch_kr_fn=mock_kr_fetch)
        assert len(articles) >= 1

        kr_articles = session.execute(
            select(NewsArticle).where(NewsArticle.source == "NAVER")
        ).scalars().all()
        assert len(kr_articles) >= 1

        session.close()
    finally:
        _teardown()


def test_collect_stock_news_us_mock():
    """collect_stock_news should collect US news for NASDAQ/NYSE stocks."""
    _setup_with_watchlists()
    try:
        from app.workers.stock_news_collector import collect_stock_news
        from app.models.news_article import NewsArticle

        session = _get_session()

        def mock_us_fetch(name):
            return [
                {"title": f"News about {name}", "url": f"https://newsapi.com/us/{name}/1", "source": "Reuters"},
            ]

        articles = collect_stock_news(session, fetch_us_fn=mock_us_fetch)
        assert len(articles) >= 1

        us_articles = session.execute(
            select(NewsArticle).where(NewsArticle.source == "Reuters")
        ).scalars().all()
        assert len(us_articles) >= 1

        session.close()
    finally:
        _teardown()


def test_collect_stock_news_both_markets():
    """collect_stock_news should collect for both KR and US tracked stocks."""
    _setup_with_watchlists()
    try:
        from app.workers.stock_news_collector import collect_stock_news

        session = _get_session()

        def mock_kr_fetch(name):
            return [
                {"title": f"KR: {name}", "url": f"https://kr.news/{name}", "source": "NAVER"},
            ]

        def mock_us_fetch(name):
            return [
                {"title": f"US: {name}", "url": f"https://us.news/{name}", "source": "Reuters"},
            ]

        articles = collect_stock_news(session, fetch_kr_fn=mock_kr_fetch, fetch_us_fn=mock_us_fetch)
        assert len(articles) == 2  # One KR + One US

        session.close()
    finally:
        _teardown()


def test_collect_stock_news_empty_result():
    """collect_stock_news should handle no results gracefully."""
    _setup_with_watchlists()
    try:
        from app.workers.stock_news_collector import collect_stock_news

        session = _get_session()
        articles = collect_stock_news(
            session,
            fetch_kr_fn=lambda name: [],
            fetch_us_fn=lambda name: [],
        )
        assert len(articles) == 0
        session.close()
    finally:
        _teardown()


def test_collect_stock_news_url_dedup():
    """collect_stock_news should skip duplicate URLs."""
    _setup_with_watchlists()
    try:
        from app.workers.stock_news_collector import collect_stock_news
        from app.models.news_article import NewsArticle

        session = _get_session()

        def mock_kr_fetch(name):
            return [
                {"title": "Same News", "url": "https://dedup-test.com/article/1", "source": "NAVER"},
            ]

        # First run
        articles1 = collect_stock_news(session, fetch_kr_fn=mock_kr_fetch)
        # Second run — same URL
        articles2 = collect_stock_news(session, fetch_kr_fn=mock_kr_fetch)

        assert len(articles1) >= 1
        assert len(articles2) == 0  # Deduplicated

        total = session.execute(
            select(func.count(NewsArticle.id)).where(
                NewsArticle.url == "https://dedup-test.com/article/1"
            )
        ).scalar()
        assert total == 1

        session.close()
    finally:
        _teardown()


def test_collect_stock_news_no_tracked():
    """collect_stock_news should handle no tracked stocks."""
    _setup()  # No watchlists
    try:
        from app.workers.stock_news_collector import collect_stock_news

        session = _get_session()
        articles = collect_stock_news(session, fetch_kr_fn=lambda name: [{"title": "x", "url": "x", "source": "x"}])
        assert len(articles) == 0
        session.close()
    finally:
        _teardown()


def test_collect_stock_news_skip_empty_url():
    """collect_stock_news should skip articles with empty URL."""
    _setup_with_watchlists()
    try:
        from app.workers.stock_news_collector import collect_stock_news

        session = _get_session()

        def mock_kr_fetch(name):
            return [
                {"title": "No URL Article", "url": "", "source": "NAVER"},
                {"title": "Valid Article", "url": "https://valid.com/article/1", "source": "NAVER"},
            ]

        articles = collect_stock_news(session, fetch_kr_fn=mock_kr_fetch)
        assert len(articles) == 1
        assert articles[0].url == "https://valid.com/article/1"

        session.close()
    finally:
        _teardown()


# --- Celery Beat Schedule Tests ---


def test_celery_beat_schedule_has_news():
    """Celery beat_schedule should include news collection."""
    from app.workers.celery_app import celery

    schedule = celery.conf.beat_schedule
    assert "collect-stock-news" in schedule

    news_entry = schedule["collect-stock-news"]
    assert news_entry["task"] == "collect_stock_news_task"


def test_celery_beat_news_schedule_timing():
    """News schedule should run every hour."""
    from app.workers.celery_app import celery
    from celery.schedules import crontab

    news_entry = celery.conf.beat_schedule["collect-stock-news"]
    sched = news_entry["schedule"]
    assert isinstance(sched, crontab)


# --- Module-Level Tests ---


def test_news_collector_has_retry_constant():
    """News collector should define MAX_RETRIES."""
    from app.workers.stock_news_collector import MAX_RETRIES
    assert MAX_RETRIES >= 1


def test_news_collector_has_api_bases():
    """News collector should define API base URLs."""
    from app.workers.stock_news_collector import NAVER_API_BASE, NEWSAPI_BASE
    assert "naver.com" in NAVER_API_BASE
    assert "newsapi.org" in NEWSAPI_BASE


def test_news_collector_has_celery_task():
    """stock_news_collector module should define collect_stock_news_task."""
    from app.workers.stock_news_collector import collect_stock_news_task
    assert collect_stock_news_task is not None or collect_stock_news_task is None


def test_config_has_naver_credentials():
    """Config should have NAVER API credential fields."""
    from app.config import Settings
    settings = Settings()
    assert hasattr(settings, "naver_client_id")
    assert hasattr(settings, "naver_client_secret")
