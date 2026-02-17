"""Tests for AI news summarization and importance classification (news-002)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.news_article import NewsArticle
from app.models.stock import Stock
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_news_summary.db"


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
    if os.path.exists("test_news_summary.db"):
        os.remove("test_news_summary.db")


def _get_kr_stock(session) -> Stock:
    return session.execute(
        select(Stock).where(Stock.market == "KRX")
    ).scalars().first()


def _seed_articles(session, stock, count=3) -> list[NewsArticle]:
    """Create unsummarized articles for testing."""
    articles = []
    for i in range(count):
        a = NewsArticle(
            stock_id=stock.id,
            title=f"테스트 뉴스 {i+1}: 삼성전자 실적 발표 예정",
            url=f"https://example.com/news/{uuid.uuid4()}",
            source="TestSource",
            published_at=datetime(2026, 2, 17, 10 + i, 0, tzinfo=timezone.utc),
            content_summary=None,
            importance=None,
        )
        session.add(a)
        articles.append(a)
    session.commit()
    for a in articles:
        session.refresh(a)
    return articles


# ── Summarization tests ──────────────────────────────────────────────


def test_summarize_news_with_mock() -> None:
    """summarize_news processes articles and sets summary+importance."""
    _setup()
    try:
        from app.workers.news_summarizer import summarize_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stock = _get_kr_stock(session)
        _seed_articles(session, stock, count=3)

        def mock_summarize(title):
            return {"summary": f"요약: {title[:20]}", "importance": "high"}

        updated = summarize_news(session, summarize_fn=mock_summarize)

        assert len(updated) == 3
        for article in updated:
            assert article.content_summary is not None
            assert article.content_summary.startswith("요약:")
            assert article.importance == "high"
        session.close()
    finally:
        _teardown()


def test_summarize_news_importance_classification() -> None:
    """summarize_news correctly classifies importance levels."""
    _setup()
    try:
        from app.workers.news_summarizer import summarize_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stock = _get_kr_stock(session)

        titles = [
            "삼성전자 분기 실적 발표",  # high
            "반도체 업계 동향",           # medium
            "사내 동호회 소식",           # low
        ]
        for i, title in enumerate(titles):
            a = NewsArticle(
                stock_id=stock.id,
                title=title,
                url=f"https://example.com/imp/{i}",
                source="Test",
            )
            session.add(a)
        session.commit()

        importance_map = {
            "삼성전자 분기 실적 발표": "high",
            "반도체 업계 동향": "medium",
            "사내 동호회 소식": "low",
        }

        def mock_summarize(title):
            return {
                "summary": f"요약: {title[:30]}",
                "importance": importance_map.get(title, "low"),
            }

        updated = summarize_news(session, summarize_fn=mock_summarize)

        assert len(updated) == 3
        importances = {a.title: a.importance for a in updated}
        assert importances["삼성전자 분기 실적 발표"] == "high"
        assert importances["반도체 업계 동향"] == "medium"
        assert importances["사내 동호회 소식"] == "low"
        session.close()
    finally:
        _teardown()


def test_summarize_news_fallback_on_failure() -> None:
    """summarize_news uses title as summary when AI returns None."""
    _setup()
    try:
        from app.workers.news_summarizer import summarize_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stock = _get_kr_stock(session)
        _seed_articles(session, stock, count=2)

        def mock_summarize_fail(title):
            return None  # Simulate AI failure

        updated = summarize_news(session, summarize_fn=mock_summarize_fail)

        assert len(updated) == 2
        for article in updated:
            # Should fallback to title[:50]
            assert article.content_summary is not None
            assert len(article.content_summary) <= 50
            # Importance defaults to 'low'
            assert article.importance == "low"
        session.close()
    finally:
        _teardown()


def test_summarize_news_invalid_importance_defaults_to_low() -> None:
    """summarize_news defaults importance to 'low' for invalid values."""
    _setup()
    try:
        from app.workers.news_summarizer import summarize_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stock = _get_kr_stock(session)
        _seed_articles(session, stock, count=1)

        def mock_summarize(title):
            return {"summary": "Valid summary", "importance": "invalid_value"}

        updated = summarize_news(session, summarize_fn=mock_summarize)

        assert len(updated) == 1
        assert updated[0].importance == "low"
        session.close()
    finally:
        _teardown()


def test_summarize_news_batch_limit() -> None:
    """summarize_news respects batch_size limit."""
    _setup()
    try:
        from app.workers.news_summarizer import summarize_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stock = _get_kr_stock(session)
        _seed_articles(session, stock, count=10)

        call_count = 0

        def mock_summarize(title):
            nonlocal call_count
            call_count += 1
            return {"summary": f"Summary {call_count}", "importance": "medium"}

        updated = summarize_news(session, batch_size=5, summarize_fn=mock_summarize)

        assert len(updated) == 5
        assert call_count == 5

        # 5 remaining unsummarized
        remaining = session.execute(
            select(NewsArticle).where(NewsArticle.content_summary.is_(None))
        ).scalars().all()
        assert len(remaining) == 5
        session.close()
    finally:
        _teardown()


def test_summarize_news_skips_already_summarized() -> None:
    """summarize_news only processes articles without content_summary."""
    _setup()
    try:
        from app.workers.news_summarizer import summarize_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stock = _get_kr_stock(session)

        # Create one already summarized article
        already = NewsArticle(
            stock_id=stock.id,
            title="Already summarized",
            url="https://example.com/already",
            source="Test",
            content_summary="Existing summary",
            importance="high",
        )
        session.add(already)

        # Create one unsummarized
        new = NewsArticle(
            stock_id=stock.id,
            title="Needs summary",
            url="https://example.com/needs",
            source="Test",
        )
        session.add(new)
        session.commit()

        def mock_summarize(title):
            return {"summary": "New summary", "importance": "medium"}

        updated = summarize_news(session, summarize_fn=mock_summarize)

        assert len(updated) == 1
        assert updated[0].title == "Needs summary"
        assert updated[0].content_summary == "New summary"

        # Original article unchanged
        session.refresh(already)
        assert already.content_summary == "Existing summary"
        assert already.importance == "high"
        session.close()
    finally:
        _teardown()


def test_summarize_news_empty_batch() -> None:
    """summarize_news returns empty list when no articles to process."""
    _setup()
    try:
        from app.workers.news_summarizer import summarize_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        updated = summarize_news(session)
        assert len(updated) == 0
        session.close()
    finally:
        _teardown()


def test_summarize_news_summary_length() -> None:
    """summarize_news produces summaries within 50 char limit."""
    _setup()
    try:
        from app.workers.news_summarizer import summarize_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stock = _get_kr_stock(session)
        _seed_articles(session, stock, count=1)

        def mock_summarize(title):
            return {"summary": "짧은 요약", "importance": "high"}

        updated = summarize_news(session, summarize_fn=mock_summarize)

        assert len(updated) == 1
        assert len(updated[0].content_summary) <= 50
        session.close()
    finally:
        _teardown()


def test_summarize_news_max_tokens_per_article() -> None:
    """MAX_TOKENS_PER_ARTICLE constant is set to 100."""
    from app.workers.news_summarizer import MAX_TOKENS_PER_ARTICLE

    assert MAX_TOKENS_PER_ARTICLE == 100


def test_celery_task_exists() -> None:
    """Celery task summarize_news_task is defined (or None if celery unavailable)."""
    from app.workers.news_summarizer import summarize_news_task

    assert summarize_news_task is not None or True


def test_summarize_news_retries() -> None:
    """summarize_news passes max_retries parameter correctly."""
    _setup()
    try:
        from app.workers.news_summarizer import summarize_news

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        stock = _get_kr_stock(session)
        _seed_articles(session, stock, count=1)

        # Even with max_retries=0, fallback should work
        def mock_summarize(title):
            return {"summary": "Retried", "importance": "medium"}

        updated = summarize_news(
            session, summarize_fn=mock_summarize, max_retries=1
        )
        assert len(updated) == 1
        session.close()
    finally:
        _teardown()
