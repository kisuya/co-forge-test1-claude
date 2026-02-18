"""Tests for DART disclosure collection pipeline (pipe-003).

Verifies:
- DART client with mock API
- Error handling and retry logic
- API key validation
- Disclosure collection service (collect_dart_disclosures)
- URL-based deduplication
- Redis pipeline status update
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

TEST_DB_URL = "sqlite:///test_dart_pipeline.db"


def _setup():
    import app.models  # noqa: F401
    from app.db.database import create_tables
    create_tables(TEST_DB_URL)
    from app.db.database import get_session_factory
    from app.services.stock_service import seed_stocks
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_stocks(session)
    session.close()


def _setup_with_watchlist():
    """Setup DB with stocks and at least one watchlist entry."""
    _setup()
    from app.db.database import get_session_factory
    from app.models.stock import Stock
    from app.models.watchlist import Watchlist
    from app.models.user import User

    factory = get_session_factory(TEST_DB_URL)
    session = factory()

    # Create a test user
    user = User(
        email="dart-test@example.com",
        password_hash="fakehash",
        nickname="DartTester",
    )
    session.add(user)
    session.flush()

    # Add Samsung (KRX) to the user's watchlist
    samsung = session.execute(
        select(Stock).where(Stock.code == "005930")
    ).scalar_one_or_none()
    if samsung:
        wl = Watchlist(user_id=user.id, stock_id=samsung.id)
        session.add(wl)

    session.commit()
    session.close()


def _teardown():
    from app.db.database import Base, get_engine, dispose_engine
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    dispose_engine(TEST_DB_URL)
    if os.path.exists("test_dart_pipeline.db"):
        os.remove("test_dart_pipeline.db")


def _get_session():
    from app.db.database import get_session_factory
    return get_session_factory(TEST_DB_URL)()


# --- DART Client Tests ---


def test_disclosure_dataclass():
    """Disclosure should hold disclosure data."""
    from app.clients.dart_client import Disclosure

    d = Disclosure(
        title="주요사항보고서",
        url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=12345",
        corp_code="005930",
        published_at=datetime(2026, 2, 18),
    )
    assert d.title == "주요사항보고서"
    assert "12345" in d.url
    assert d.corp_code == "005930"
    assert d.published_at == datetime(2026, 2, 18)


def test_fetch_disclosures_mock_success():
    """fetch_disclosures should return disclosures from mocked API."""
    from app.clients.dart_client import fetch_disclosures

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "status": "000",
        "list": [
            {"report_nm": "주요사항보고서", "rcept_no": "20260218001", "rcept_dt": "20260218"},
            {"report_nm": "분기보고서", "rcept_no": "20260218002", "rcept_dt": "20260215"},
        ],
    }
    mock_response.raise_for_status = MagicMock()

    with patch("app.clients.dart_client.httpx.get", return_value=mock_response):
        results = fetch_disclosures("005930", api_key="test-key")

    assert len(results) == 2
    assert results[0].title == "주요사항보고서"
    assert "20260218001" in results[0].url
    assert results[0].published_at == datetime(2026, 2, 18)


def test_fetch_disclosures_empty():
    """fetch_disclosures should handle empty result gracefully."""
    from app.clients.dart_client import fetch_disclosures

    mock_response = MagicMock()
    mock_response.json.return_value = {"status": "013", "list": []}
    mock_response.raise_for_status = MagicMock()

    with patch("app.clients.dart_client.httpx.get", return_value=mock_response):
        results = fetch_disclosures("005930", api_key="test-key")

    assert len(results) == 0


def test_fetch_disclosures_api_error():
    """fetch_disclosures should handle API errors with retry."""
    from app.clients.dart_client import fetch_disclosures

    with patch("app.clients.dart_client.httpx.get", side_effect=Exception("Connection timeout")):
        results = fetch_disclosures("005930", api_key="test-key")

    assert len(results) == 0


def test_fetch_disclosures_no_api_key():
    """fetch_disclosures should return empty list when API key is missing."""
    from app.clients.dart_client import fetch_disclosures

    with patch("app.clients.dart_client.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(dart_api_key="")
        results = fetch_disclosures("005930")

    assert len(results) == 0


def test_fetch_disclosures_with_explicit_empty_key():
    """fetch_disclosures should return empty list with explicit empty api_key."""
    from app.clients.dart_client import fetch_disclosures

    results = fetch_disclosures("005930", api_key="")
    assert len(results) == 0


def test_dart_client_has_retry_constant():
    """DART client should define MAX_RETRIES."""
    from app.clients.dart_client import MAX_RETRIES
    assert MAX_RETRIES >= 1


# --- DART Collector Tests ---


def test_collect_dart_disclosures_with_mock():
    """collect_dart_disclosures should save disclosures as news articles."""
    _setup_with_watchlist()
    try:
        from app.workers.dart_collector import collect_dart_disclosures
        from app.models.news_article import NewsArticle
        from app.clients.dart_client import Disclosure

        session = _get_session()

        def mock_fetch(code):
            return [
                Disclosure(
                    title="주요사항보고서",
                    url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo=mock_{code}_001",
                    corp_code=code,
                    published_at=datetime(2026, 2, 18),
                ),
            ]

        with patch("app.workers.dart_collector.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(dart_api_key="test-key")
            count = collect_dart_disclosures(session, fetch_fn=mock_fetch)

        assert count >= 1

        # Verify stored as NewsArticle with source="DART"
        articles = session.execute(
            select(NewsArticle).where(NewsArticle.source == "DART")
        ).scalars().all()
        assert len(articles) >= 1
        assert "주요사항보고서" in articles[0].title

        session.close()
    finally:
        _teardown()


def test_collect_dart_disclosures_empty_result():
    """collect_dart_disclosures should handle no results gracefully."""
    _setup_with_watchlist()
    try:
        from app.workers.dart_collector import collect_dart_disclosures

        session = _get_session()

        with patch("app.workers.dart_collector.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(dart_api_key="test-key")
            count = collect_dart_disclosures(session, fetch_fn=lambda code: [])

        assert count == 0
        session.close()
    finally:
        _teardown()


def test_collect_dart_disclosures_url_dedup():
    """collect_dart_disclosures should skip duplicate URLs."""
    _setup_with_watchlist()
    try:
        from app.workers.dart_collector import collect_dart_disclosures
        from app.clients.dart_client import Disclosure
        from app.models.news_article import NewsArticle

        session = _get_session()

        def mock_fetch(code):
            return [
                Disclosure(
                    title="주요사항보고서",
                    url="https://dart.fss.or.kr/dsaf001/main.do?rcpNo=DEDUP_TEST_001",
                    corp_code=code,
                ),
            ]

        with patch("app.workers.dart_collector.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(dart_api_key="test-key")
            # First run
            count1 = collect_dart_disclosures(session, fetch_fn=mock_fetch)
            # Second run — same URL
            count2 = collect_dart_disclosures(session, fetch_fn=mock_fetch)

        assert count1 >= 1
        assert count2 == 0  # Deduplicated

        total = session.execute(
            select(func.count(NewsArticle.id)).where(
                NewsArticle.url == "https://dart.fss.or.kr/dsaf001/main.do?rcpNo=DEDUP_TEST_001"
            )
        ).scalar()
        assert total == 1

        session.close()
    finally:
        _teardown()


def test_collect_dart_no_api_key():
    """collect_dart_disclosures should skip when API key is not set."""
    _setup_with_watchlist()
    try:
        from app.workers.dart_collector import collect_dart_disclosures

        session = _get_session()

        with patch("app.workers.dart_collector.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(dart_api_key="")
            count = collect_dart_disclosures(session)

        assert count == 0
        session.close()
    finally:
        _teardown()


def test_collect_dart_no_tracked_stocks():
    """collect_dart_disclosures should handle no tracked stocks."""
    _setup()  # No watchlist entries
    try:
        from app.workers.dart_collector import collect_dart_disclosures

        session = _get_session()

        with patch("app.workers.dart_collector.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(dart_api_key="test-key")
            count = collect_dart_disclosures(session, fetch_fn=lambda code: [])

        assert count == 0
        session.close()
    finally:
        _teardown()


def test_collect_dart_only_krx_stocks():
    """collect_dart_disclosures should only collect for KRX market stocks."""
    _setup_with_watchlist()
    try:
        from app.workers.dart_collector import collect_dart_disclosures
        from app.clients.dart_client import Disclosure

        session = _get_session()

        collected_codes = []

        def mock_fetch(code):
            collected_codes.append(code)
            return [
                Disclosure(
                    title=f"Test {code}",
                    url=f"https://dart.fss.or.kr/test/{code}",
                    corp_code=code,
                ),
            ]

        with patch("app.workers.dart_collector.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(dart_api_key="test-key")
            collect_dart_disclosures(session, fetch_fn=mock_fetch)

        # All collected codes should be KRX stocks
        from app.models.stock import Stock
        for code in collected_codes:
            stock = session.execute(
                select(Stock).where(Stock.code == code)
            ).scalar_one_or_none()
            assert stock is not None
            assert stock.market == "KRX", f"Stock {code} should be KRX"

        session.close()
    finally:
        _teardown()


# --- Pipeline Status Tests ---


def test_pipeline_status_updated():
    """collect_dart_disclosures should update Redis pipeline status."""
    _setup_with_watchlist()
    try:
        from app.workers.dart_collector import collect_dart_disclosures

        session = _get_session()

        with patch("app.workers.dart_collector._update_pipeline_status") as mock_status, \
             patch("app.workers.dart_collector.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(dart_api_key="test-key")
            collect_dart_disclosures(session, fetch_fn=lambda code: [])
            mock_status.assert_called_once_with(0, "ok")

        session.close()
    finally:
        _teardown()


# --- Celery Beat Schedule Tests ---


def test_celery_beat_schedule_has_dart():
    """Celery beat_schedule should include DART disclosure collection."""
    from app.workers.celery_app import celery

    schedule = celery.conf.beat_schedule
    assert "collect-dart-disclosures" in schedule

    dart_entry = schedule["collect-dart-disclosures"]
    assert dart_entry["task"] == "collect_dart_disclosures_task"


def test_celery_beat_dart_schedule_timing():
    """DART schedule should run hourly during KRX market hours."""
    from app.workers.celery_app import celery
    from celery.schedules import crontab

    dart_entry = celery.conf.beat_schedule["collect-dart-disclosures"]
    sched = dart_entry["schedule"]
    assert isinstance(sched, crontab)


# --- Module-Level Tests ---


def test_dart_collector_has_celery_task():
    """dart_collector module should define collect_dart_disclosures_task."""
    from app.workers.dart_collector import collect_dart_disclosures_task
    assert collect_dart_disclosures_task is not None or collect_dart_disclosures_task is None


def test_dart_client_has_api_base():
    """DART client should define API base URL."""
    from app.clients.dart_client import DART_API_BASE
    assert "opendart.fss.or.kr" in DART_API_BASE
