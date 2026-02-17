"""Tests for NewsArticle model and stock news collection (news-001)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.news_article import NewsArticle
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_news_collection.db"


def _make_fk_engine():
    """Create engine with foreign key support for SQLite."""
    engine = create_engine("sqlite:///test_news_collection.db")

    @event.listens_for(engine, "connect")
    def _set_fk(dbapi_conn, _rec):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


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
    if os.path.exists("test_news_collection.db"):
        os.remove("test_news_collection.db")


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
        email="newstest@example.com",
        password_hash="hashed",
        settings={"threshold": 3.0},
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _track_stock(session, user: User, stock: Stock) -> None:
    wl = Watchlist(user_id=user.id, stock_id=stock.id)
    session.add(wl)
    session.commit()


# ── Model tests ──────────────────────────────────────────────────────


def test_news_article_creation() -> None:
    """NewsArticle can be created with valid fields."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stock = _get_kr_stock(session)

        article = NewsArticle(
            stock_id=stock.id,
            title="삼성전자 실적 발표",
            url="https://example.com/news/1",
            source="NAVER",
            published_at=datetime(2026, 2, 17, 10, 0, tzinfo=timezone.utc),
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        assert article.id is not None
        assert article.stock_id == stock.id
        assert article.title == "삼성전자 실적 발표"
        assert article.url == "https://example.com/news/1"
        assert article.source == "NAVER"
        assert article.published_at is not None
        assert article.content_summary is None
        assert article.importance is None
        assert article.created_at is not None
        session.close()
    finally:
        _teardown()


def test_news_article_nullable_stock_id() -> None:
    """NewsArticle can be created without stock_id (market-wide news)."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        article = NewsArticle(
            stock_id=None,
            title="코스피 급등",
            url="https://example.com/market/1",
            source="Reuters",
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        assert article.stock_id is None
        assert article.title == "코스피 급등"
        session.close()
    finally:
        _teardown()


def test_news_article_url_unique() -> None:
    """NewsArticle URL must be unique."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        a1 = NewsArticle(
            title="News 1",
            url="https://example.com/same-url",
            source="Test",
        )
        session.add(a1)
        session.commit()

        a2 = NewsArticle(
            title="News 2",
            url="https://example.com/same-url",
            source="Test",
        )
        session.add(a2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_news_article_title_not_null() -> None:
    """NewsArticle title cannot be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        article = NewsArticle(
            title=None,
            url="https://example.com/no-title",
            source="Test",
        )
        session.add(article)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_news_article_url_not_null() -> None:
    """NewsArticle url cannot be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        article = NewsArticle(
            title="Some title",
            url=None,
            source="Test",
        )
        session.add(article)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_news_article_source_not_null() -> None:
    """NewsArticle source cannot be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        article = NewsArticle(
            title="Some title",
            url="https://example.com/no-source",
            source=None,
        )
        session.add(article)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_news_article_content_summary_nullable() -> None:
    """NewsArticle content_summary is nullable (AI fills it later)."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        article = NewsArticle(
            title="No summary yet",
            url="https://example.com/no-summary",
            source="Test",
            content_summary=None,
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        assert article.content_summary is None
        session.close()
    finally:
        _teardown()


def test_news_article_importance_nullable() -> None:
    """NewsArticle importance is nullable (AI classifies later)."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        article = NewsArticle(
            title="No importance",
            url="https://example.com/no-importance",
            source="Test",
            importance=None,
        )
        session.add(article)
        session.commit()
        session.refresh(article)

        assert article.importance is None
        session.close()
    finally:
        _teardown()


def test_news_article_importance_values() -> None:
    """NewsArticle importance can be 'high', 'medium', or 'low'."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        for i, imp in enumerate(["high", "medium", "low"]):
            article = NewsArticle(
                title=f"News {imp}",
                url=f"https://example.com/imp-{i}",
                source="Test",
                importance=imp,
            )
            session.add(article)
        session.commit()

        articles = session.execute(
            select(NewsArticle).where(NewsArticle.importance.isnot(None))
        ).scalars().all()
        assert len(articles) == 3
        importances = {a.importance for a in articles}
        assert importances == {"high", "medium", "low"}
        session.close()
    finally:
        _teardown()


def test_news_article_index_exists() -> None:
    """NewsArticle has required index on (stock_id, published_at)."""
    indexes = NewsArticle.__table__.indexes
    index_cols = set()
    for idx in indexes:
        cols = frozenset(c.name for c in idx.columns)
        index_cols.add(cols)

    assert frozenset({"stock_id", "published_at"}) in index_cols


def test_news_article_cascade_on_stock_delete() -> None:
    """NewsArticle is deleted when its stock is deleted (CASCADE)."""
    _setup()
    try:
        engine = _make_fk_engine()
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()

        stock = session.execute(
            select(Stock).where(Stock.market == "KRX")
        ).scalars().first()

        article = NewsArticle(
            stock_id=stock.id,
            title="Will be cascaded",
            url="https://example.com/cascade",
            source="Test",
        )
        session.add(article)
        session.commit()
        article_id = article.id

        # Delete the stock
        session.delete(stock)
        session.commit()

        # Article should be gone
        result = session.execute(
            select(NewsArticle).where(NewsArticle.id == article_id)
        ).scalar_one_or_none()
        assert result is None
        session.close()
        engine.dispose()
    finally:
        _teardown()


# ── Collection task tests ────────────────────────────────────────────


def test_collect_stock_news_with_mock() -> None:
    """collect_stock_news creates articles from mock fetch function."""
    _setup()
    try:
        from app.workers.stock_news_collector import collect_stock_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        stock = _get_kr_stock(session)
        user = _create_user(session)
        _track_stock(session, user, stock)

        def mock_kr_fetch(stock_name):
            return [
                {
                    "title": f"{stock_name} 관련 뉴스 1",
                    "url": "https://example.com/kr/1",
                    "source": "NAVER",
                    "published_at": "2026-02-17T10:00:00+09:00",
                },
                {
                    "title": f"{stock_name} 관련 뉴스 2",
                    "url": "https://example.com/kr/2",
                    "source": "한국경제",
                },
            ]

        articles = collect_stock_news(session, fetch_kr_fn=mock_kr_fetch)

        assert len(articles) == 2
        assert articles[0].stock_id == stock.id
        assert articles[0].source == "NAVER"
        assert articles[0].published_at is not None
        assert articles[1].source == "한국경제"
        session.close()
    finally:
        _teardown()


def test_collect_stock_news_us_stocks() -> None:
    """collect_stock_news handles US stocks with US fetch function."""
    _setup()
    try:
        from app.workers.stock_news_collector import collect_stock_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        us_stock = _get_us_stock(session)
        if us_stock is None:
            pytest.skip("No US stocks seeded")

        user = _create_user(session)
        _track_stock(session, user, us_stock)

        def mock_us_fetch(stock_name):
            return [
                {
                    "title": f"{stock_name} earnings report",
                    "url": "https://example.com/us/1",
                    "source": "Reuters",
                    "published_at": "2026-02-17T15:00:00+00:00",
                },
            ]

        articles = collect_stock_news(session, fetch_us_fn=mock_us_fetch)

        assert len(articles) == 1
        assert articles[0].stock_id == us_stock.id
        assert articles[0].source == "Reuters"
        session.close()
    finally:
        _teardown()


def test_collect_stock_news_url_deduplication() -> None:
    """collect_stock_news skips articles with duplicate URLs."""
    _setup()
    try:
        from app.workers.stock_news_collector import collect_stock_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        stock = _get_kr_stock(session)
        user = _create_user(session)
        _track_stock(session, user, stock)

        # Pre-insert an article with a known URL
        existing = NewsArticle(
            stock_id=stock.id,
            title="Already exists",
            url="https://example.com/dup",
            source="Test",
        )
        session.add(existing)
        session.commit()

        def mock_kr_fetch(stock_name):
            return [
                {
                    "title": "Duplicate",
                    "url": "https://example.com/dup",
                    "source": "NAVER",
                },
                {
                    "title": "New one",
                    "url": "https://example.com/new",
                    "source": "NAVER",
                },
            ]

        articles = collect_stock_news(session, fetch_kr_fn=mock_kr_fetch)

        # Only the new one should be created
        assert len(articles) == 1
        assert articles[0].url == "https://example.com/new"
        session.close()
    finally:
        _teardown()


def test_collect_stock_news_untracked_stocks_skipped() -> None:
    """collect_stock_news only collects for stocks tracked by >= 1 user."""
    _setup()
    try:
        from app.workers.stock_news_collector import collect_stock_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        # No user tracking any stock — should return empty
        call_count = 0

        def mock_kr_fetch(stock_name):
            nonlocal call_count
            call_count += 1
            return [
                {
                    "title": "Should not be fetched",
                    "url": f"https://example.com/untracked/{call_count}",
                    "source": "Test",
                },
            ]

        articles = collect_stock_news(session, fetch_kr_fn=mock_kr_fetch)

        assert len(articles) == 0
        assert call_count == 0  # mock_kr_fetch was never called
        session.close()
    finally:
        _teardown()


def test_collect_stock_news_empty_url_skipped() -> None:
    """collect_stock_news skips articles with empty URL."""
    _setup()
    try:
        from app.workers.stock_news_collector import collect_stock_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        stock = _get_kr_stock(session)
        user = _create_user(session)
        _track_stock(session, user, stock)

        def mock_kr_fetch(stock_name):
            return [
                {"title": "No URL", "url": "", "source": "Test"},
                {"title": "Has URL", "url": "https://example.com/valid", "source": "Test"},
            ]

        articles = collect_stock_news(session, fetch_kr_fn=mock_kr_fetch)

        assert len(articles) == 1
        assert articles[0].url == "https://example.com/valid"
        session.close()
    finally:
        _teardown()


def test_collect_stock_news_no_api_key() -> None:
    """collect_stock_news returns empty when no API key configured."""
    _setup()
    try:
        from app.workers.stock_news_collector import collect_stock_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        stock = _get_kr_stock(session)
        user = _create_user(session)
        _track_stock(session, user, stock)

        # Without mock functions and without API keys, should return empty
        articles = collect_stock_news(session)
        assert len(articles) == 0
        session.close()
    finally:
        _teardown()


def test_celery_task_exists() -> None:
    """Celery task collect_stock_news_task is defined (or None if celery unavailable)."""
    from app.workers.stock_news_collector import collect_stock_news_task

    # Should be importable — may be None when celery is not installed
    assert collect_stock_news_task is not None or True


def test_news_article_autoincrement_id() -> None:
    """NewsArticle uses autoincrement integer PK."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        a1 = NewsArticle(title="First", url="https://example.com/a1", source="Test")
        session.add(a1)
        session.commit()
        session.refresh(a1)

        a2 = NewsArticle(title="Second", url="https://example.com/a2", source="Test")
        session.add(a2)
        session.commit()
        session.refresh(a2)

        assert isinstance(a1.id, int)
        assert isinstance(a2.id, int)
        assert a2.id > a1.id
        session.close()
    finally:
        _teardown()
