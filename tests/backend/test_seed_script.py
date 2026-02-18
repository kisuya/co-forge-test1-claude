"""Tests for seed sample data script (fix-003).

Verifies:
- Seed script creates expected data counts
- Seed script is idempotent (2nd run doesn't error)
- All tables have expected row counts
"""
from __future__ import annotations

import os
import sys

import pytest
from sqlalchemy import func, select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)

TEST_DB_URL = "sqlite:///test_seed_data.db"


def _setup():
    from app.db.database import create_tables
    create_tables(TEST_DB_URL)


def _teardown():
    from app.db.database import Base, get_engine
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_seed_data.db"):
        os.remove("test_seed_data.db")


def _get_session():
    from app.db.database import get_session_factory
    return get_session_factory(TEST_DB_URL)()


def test_seed_script_exists():
    """Shell wrapper for seed script should exist."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", ".forge", "scripts", "seed_sample_data.sh"
    )
    assert os.path.isfile(path)


def test_seed_script_is_executable():
    """Shell wrapper should be executable."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", ".forge", "scripts", "seed_sample_data.sh"
    )
    assert os.access(path, os.X_OK)


def test_seed_python_module_exists():
    """Python seed module should exist."""
    path = os.path.join(
        os.path.dirname(__file__), "..", "..", "backend", "app", "scripts", "seed_sample_data.py"
    )
    assert os.path.isfile(path)


def test_seed_creates_users():
    """Seed should create 2 users."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed
        counts = run_seed(TEST_DB_URL)
        assert counts["users"] == 2

        from app.models.user import User
        db = _get_session()
        user_count = db.execute(select(func.count(User.id))).scalar()
        assert user_count == 2

        # Verify specific emails
        user1 = db.execute(select(User).where(User.email == "test@example.com")).scalar_one_or_none()
        assert user1 is not None
        user2 = db.execute(select(User).where(User.email == "investor@example.com")).scalar_one_or_none()
        assert user2 is not None
        db.close()
    finally:
        _teardown()


def test_seed_creates_watchlists():
    """Seed should create 8 watchlist entries."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed
        counts = run_seed(TEST_DB_URL)
        assert counts["watchlists"] == 8

        from app.models.watchlist import Watchlist
        db = _get_session()
        wl_count = db.execute(select(func.count(Watchlist.id))).scalar()
        assert wl_count == 8
        db.close()
    finally:
        _teardown()


def test_seed_creates_price_snapshots():
    """Seed should create 15 price snapshots."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed
        counts = run_seed(TEST_DB_URL)
        assert counts["price_snapshots"] == 15

        from app.models.report import PriceSnapshot
        db = _get_session()
        snap_count = db.execute(select(func.count(PriceSnapshot.id))).scalar()
        assert snap_count == 15
        db.close()
    finally:
        _teardown()


def test_seed_creates_reports():
    """Seed should create 7 reports with analysis JSON."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed
        counts = run_seed(TEST_DB_URL)
        assert counts["reports"] == 7

        from app.models.report import Report
        db = _get_session()
        report_count = db.execute(select(func.count(Report.id))).scalar()
        assert report_count == 7

        # Verify analysis JSON is populated
        report = db.execute(select(Report).where(Report.status == "completed")).scalars().first()
        assert report is not None
        assert report.analysis is not None
        assert "causes" in report.analysis
        db.close()
    finally:
        _teardown()


def test_seed_creates_news():
    """Seed should create 12 news articles."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed
        counts = run_seed(TEST_DB_URL)
        assert counts["news_articles"] == 12

        from app.models.news_article import NewsArticle
        db = _get_session()
        news_count = db.execute(select(func.count(NewsArticle.id))).scalar()
        assert news_count == 12
        db.close()
    finally:
        _teardown()


def test_seed_creates_briefings():
    """Seed should create 3 briefings."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed
        counts = run_seed(TEST_DB_URL)
        assert counts["market_briefings"] == 3

        from app.models.market_briefing import MarketBriefing
        db = _get_session()
        brief_count = db.execute(select(func.count(MarketBriefing.id))).scalar()
        assert brief_count == 3
        db.close()
    finally:
        _teardown()


def test_seed_creates_calendar_events():
    """Seed should create 9 calendar events."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed
        counts = run_seed(TEST_DB_URL)
        assert counts["calendar_events"] == 9

        from app.models.calendar_event import CalendarEvent
        db = _get_session()
        event_count = db.execute(select(func.count(CalendarEvent.id))).scalar()
        assert event_count == 9
        db.close()
    finally:
        _teardown()


def test_seed_creates_discussions():
    """Seed should create 6 discussions and 5 comments."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed
        counts = run_seed(TEST_DB_URL)
        assert counts["discussions"] == 6
        assert counts["discussion_comments"] == 5

        from app.models.discussion import Discussion, DiscussionComment
        db = _get_session()
        disc_count = db.execute(select(func.count(Discussion.id))).scalar()
        assert disc_count == 6
        comment_count = db.execute(select(func.count(DiscussionComment.id))).scalar()
        assert comment_count == 5
        db.close()
    finally:
        _teardown()


def test_seed_creates_shared_report():
    """Seed should create 1 shared report."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed
        counts = run_seed(TEST_DB_URL)
        assert counts["shared_reports"] == 1

        from app.models.shared_report import SharedReport
        db = _get_session()
        share_count = db.execute(select(func.count(SharedReport.id))).scalar()
        assert share_count == 1
        db.close()
    finally:
        _teardown()


def test_seed_is_idempotent():
    """Running seed twice should not produce errors or duplicates."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed

        # First run
        counts1 = run_seed(TEST_DB_URL)
        assert counts1["users"] == 2

        # Second run — should not raise and should have same counts
        counts2 = run_seed(TEST_DB_URL)
        assert counts2["users"] == 2

        from app.models.user import User
        db = _get_session()
        user_count = db.execute(select(func.count(User.id))).scalar()
        assert user_count == 2, f"Expected 2 users after 2nd run, got {user_count}"
        db.close()
    finally:
        _teardown()


def test_seed_returns_correct_total_counts():
    """Seed should return correct counts for all entities."""
    _setup()
    try:
        from app.scripts.seed_sample_data import run_seed
        counts = run_seed(TEST_DB_URL)

        expected = {
            "users": 2,
            "watchlists": 8,
            "price_snapshots": 15,
            "reports": 7,
            "news_articles": 12,
            "market_briefings": 3,
            "calendar_events": 9,
            "discussions": 6,
            "discussion_comments": 5,
            "shared_reports": 1,
        }
        for key, expected_count in expected.items():
            assert counts[key] == expected_count, f"{key}: expected {expected_count}, got {counts[key]}"
    finally:
        _teardown()
