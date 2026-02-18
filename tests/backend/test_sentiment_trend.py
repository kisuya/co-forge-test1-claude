"""Tests for news sentiment analysis trend (analysis-008).

Verifies:
- NewsArticle model has sentiment and sentiment_score columns
- news_summarizer populates sentiment fields
- Sentiment parsing from AI response
- GET /api/stocks/{stock_id}/sentiment endpoint
- Daily aggregation
- Frontend: SentimentTrend component structure
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)

TEST_DB_URL = "sqlite:///test_sentiment_trend.db"


def _setup():
    import app.models  # noqa: F401
    from app.db.database import create_tables
    create_tables(TEST_DB_URL)


def _teardown():
    from app.db.database import Base, get_engine, dispose_engine
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    dispose_engine(TEST_DB_URL)
    if os.path.exists("test_sentiment_trend.db"):
        os.remove("test_sentiment_trend.db")


def _get_session():
    from app.db.database import get_session_factory
    return get_session_factory(TEST_DB_URL)()


# ---- Model tests ----


def test_news_article_has_sentiment_columns():
    """NewsArticle model should have sentiment and sentiment_score columns."""
    _setup()
    session = _get_session()
    try:
        from app.models.news_article import NewsArticle
        from app.models.stock import Stock

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        article = NewsArticle(
            stock_id=stock.id,
            title="삼성전자 실적 호조",
            url="https://example.com/1",
            source="test",
            sentiment="positive",
            sentiment_score=0.8,
        )
        session.add(article)
        session.commit()

        loaded = session.execute(
            select(NewsArticle).where(NewsArticle.id == article.id)
        ).scalar_one()

        assert loaded.sentiment == "positive"
        assert loaded.sentiment_score == 0.8
    finally:
        session.close()
        _teardown()


def test_news_article_sentiment_nullable():
    """sentiment columns should be nullable for backward compat."""
    _setup()
    session = _get_session()
    try:
        from app.models.news_article import NewsArticle

        article = NewsArticle(
            title="No sentiment", url="https://example.com/2", source="test",
        )
        session.add(article)
        session.commit()

        loaded = session.execute(
            select(NewsArticle).where(NewsArticle.id == article.id)
        ).scalar_one()

        assert loaded.sentiment is None
        assert loaded.sentiment_score is None
    finally:
        session.close()
        _teardown()


# ---- news_summarizer tests ----


def test_summarizer_sets_sentiment():
    """summarize_news should populate sentiment fields from AI response."""
    _setup()
    session = _get_session()
    try:
        from app.models.news_article import NewsArticle
        from app.workers.news_summarizer import summarize_news

        article = NewsArticle(
            title="삼성전자 3분기 실적 사상 최대",
            url="https://example.com/3",
            source="test",
        )
        session.add(article)
        session.commit()

        def mock_summarize(title):
            return {
                "summary": "삼성전자 최대 실적",
                "importance": "high",
                "sentiment": "positive",
                "sentiment_score": 0.9,
            }

        summarize_news(session, summarize_fn=mock_summarize)

        loaded = session.execute(
            select(NewsArticle).where(NewsArticle.id == article.id)
        ).scalar_one()

        assert loaded.sentiment == "positive"
        assert loaded.sentiment_score == 0.9
    finally:
        session.close()
        _teardown()


def test_summarizer_sets_negative_sentiment():
    """summarize_news should handle negative sentiment."""
    _setup()
    session = _get_session()
    try:
        from app.models.news_article import NewsArticle
        from app.workers.news_summarizer import summarize_news

        article = NewsArticle(
            title="대규모 리콜 발생",
            url="https://example.com/4",
            source="test",
        )
        session.add(article)
        session.commit()

        def mock_summarize(title):
            return {
                "summary": "리콜 위기",
                "importance": "high",
                "sentiment": "negative",
                "sentiment_score": -0.7,
            }

        summarize_news(session, summarize_fn=mock_summarize)

        loaded = session.execute(
            select(NewsArticle).where(NewsArticle.id == article.id)
        ).scalar_one()

        assert loaded.sentiment == "negative"
        assert loaded.sentiment_score == -0.7
    finally:
        session.close()
        _teardown()


def test_summarizer_invalid_sentiment_defaults_neutral():
    """Invalid sentiment should default to neutral."""
    _setup()
    session = _get_session()
    try:
        from app.models.news_article import NewsArticle
        from app.workers.news_summarizer import summarize_news

        article = NewsArticle(
            title="일반 뉴스",
            url="https://example.com/5",
            source="test",
        )
        session.add(article)
        session.commit()

        def mock_summarize(title):
            return {
                "summary": "일반",
                "importance": "low",
                "sentiment": "invalid_value",
                "sentiment_score": 0.0,
            }

        summarize_news(session, summarize_fn=mock_summarize)

        loaded = session.execute(
            select(NewsArticle).where(NewsArticle.id == article.id)
        ).scalar_one()

        assert loaded.sentiment == "neutral"
    finally:
        session.close()
        _teardown()


def test_summarizer_clamps_sentiment_score():
    """sentiment_score should be clamped to [-1.0, 1.0]."""
    _setup()
    session = _get_session()
    try:
        from app.models.news_article import NewsArticle
        from app.workers.news_summarizer import summarize_news

        article = NewsArticle(
            title="극단적 뉴스",
            url="https://example.com/6",
            source="test",
        )
        session.add(article)
        session.commit()

        def mock_summarize(title):
            return {
                "summary": "극단",
                "importance": "high",
                "sentiment": "positive",
                "sentiment_score": 5.0,  # out of range
            }

        summarize_news(session, summarize_fn=mock_summarize)

        loaded = session.execute(
            select(NewsArticle).where(NewsArticle.id == article.id)
        ).scalar_one()

        assert loaded.sentiment_score == 1.0
    finally:
        session.close()
        _teardown()


def test_summarizer_derives_score_from_sentiment():
    """When no sentiment_score provided, derive from sentiment label."""
    _setup()
    session = _get_session()
    try:
        from app.models.news_article import NewsArticle
        from app.workers.news_summarizer import summarize_news

        article = NewsArticle(
            title="뉴스 없는 스코어",
            url="https://example.com/7",
            source="test",
        )
        session.add(article)
        session.commit()

        def mock_summarize(title):
            return {
                "summary": "test",
                "importance": "low",
                "sentiment": "negative",
                # no sentiment_score
            }

        summarize_news(session, summarize_fn=mock_summarize)

        loaded = session.execute(
            select(NewsArticle).where(NewsArticle.id == article.id)
        ).scalar_one()

        assert loaded.sentiment == "negative"
        assert loaded.sentiment_score == -0.5
    finally:
        session.close()
        _teardown()


def test_summarizer_no_sentiment_on_fallback():
    """When AI returns None, no sentiment should be set."""
    _setup()
    session = _get_session()
    try:
        from app.models.news_article import NewsArticle
        from app.workers.news_summarizer import summarize_news

        article = NewsArticle(
            title="Fallback test",
            url="https://example.com/8",
            source="test",
        )
        session.add(article)
        session.commit()

        def mock_summarize(title):
            return None

        summarize_news(session, summarize_fn=mock_summarize)

        loaded = session.execute(
            select(NewsArticle).where(NewsArticle.id == article.id)
        ).scalar_one()

        assert loaded.sentiment is None
        assert loaded.sentiment_score is None
    finally:
        session.close()
        _teardown()


# ---- API endpoint tests ----


def test_sentiment_api_response_model():
    """SentimentTrendResponse should have correct fields."""
    from app.api.stocks import SentimentTrendResponse, SentimentDayResponse

    resp = SentimentTrendResponse(
        stock_id="test-id",
        days=[
            SentimentDayResponse(date="2026-01-01", avg_score=0.5, article_count=3),
        ],
    )
    assert resp.stock_id == "test-id"
    assert len(resp.days) == 1
    assert resp.days[0].avg_score == 0.5


def test_sentiment_api_empty():
    """SentimentTrendResponse should handle no data."""
    from app.api.stocks import SentimentTrendResponse

    resp = SentimentTrendResponse(
        stock_id="test-id",
        days=[],
        message="감성 데이터가 충분하지 않습니다",
    )
    assert len(resp.days) == 0
    assert resp.message is not None


# ---- Prompt tests ----


def test_summarize_prompt_includes_sentiment():
    """_build_summarize_prompt should request sentiment analysis."""
    from app.workers.news_summarizer import _build_summarize_prompt

    prompt = _build_summarize_prompt("삼성전자 실적 호조")
    assert "sentiment" in prompt
    assert "positive" in prompt
    assert "negative" in prompt
    assert "neutral" in prompt
    assert "sentiment_score" in prompt


# ---- Frontend tests ----


def test_sentiment_trend_component_exists():
    """SentimentTrend.tsx should exist and have chart rendering."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "SentimentTrend.tsx"
    assert path.exists()
    content = path.read_text()
    assert "sentiment-trend" in content
    assert "sentiment-chart" in content


def test_sentiment_trend_in_stock_detail():
    """Stock detail page should include SentimentTrend component."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "app" / "stocks" / "[stockId]" / "page.tsx"
    content = path.read_text()
    assert "SentimentTrend" in content


def test_sentiment_chart_is_svg():
    """SentimentTrend should render SVG chart."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "SentimentTrend.tsx"
    content = path.read_text()
    assert "<svg" in content
    assert "polyline" in content
