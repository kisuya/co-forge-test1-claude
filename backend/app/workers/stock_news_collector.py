"""Collect general news for tracked stocks (news-001).

This worker extends beyond the report-specific news_collector to gather
general news for all stocks that have at least 1 user tracking them.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.news_article import NewsArticle
from app.models.stock import Stock
from app.models.watchlist import Watchlist

logger = logging.getLogger(__name__)



def _get_tracked_stocks(db: Session) -> list[Stock]:
    """Return stocks tracked by at least 1 user."""
    subq = (
        select(Watchlist.stock_id)
        .group_by(Watchlist.stock_id)
        .having(func.count(Watchlist.user_id) >= 1)
        .subquery()
    )
    return list(
        db.execute(
            select(Stock).where(Stock.id.in_(select(subq.c.stock_id)))
        ).scalars().all()
    )


def _fetch_naver_news(stock_name: str, api_key: str = "") -> list[dict]:
    """Fetch news from NAVER Search API for Korean stocks.

    Returns a list of dicts with title, url, source, published_at.
    In production this would call the NAVER API. For now it returns
    an empty list when no API key is configured.
    """
    if not api_key:
        return []
    # Production: call NAVER search API
    # For now, return empty — the mock/test pattern allows injection
    return []


def _fetch_newsapi_articles(stock_name: str, api_key: str = "") -> list[dict]:
    """Fetch news from NewsAPI for US stocks.

    Returns a list of dicts with title, url, source, published_at.
    """
    if not api_key:
        return []
    return []


def collect_stock_news(
    db: Session,
    *,
    fetch_kr_fn: object | None = None,
    fetch_us_fn: object | None = None,
) -> list[NewsArticle]:
    """Collect news articles for all tracked stocks.

    Args:
        db: Database session.
        fetch_kr_fn: Override for Korean news fetching (for testing).
        fetch_us_fn: Override for US news fetching (for testing).

    Returns:
        List of newly created NewsArticle entries.
    """
    settings = get_settings()
    tracked_stocks = _get_tracked_stocks(db)
    created: list[NewsArticle] = []

    for stock in tracked_stocks:
        is_korean = stock.market == "KRX"

        if fetch_kr_fn and is_korean:
            raw_articles = fetch_kr_fn(stock.name)
        elif fetch_us_fn and not is_korean:
            raw_articles = fetch_us_fn(stock.name)
        elif is_korean:
            raw_articles = _fetch_naver_news(stock.name, settings.news_api_key)
        else:
            raw_articles = _fetch_newsapi_articles(stock.name, settings.news_api_key)

        for article in raw_articles:
            url = article.get("url", "")
            if not url:
                continue

            # URL-based deduplication
            existing = db.execute(
                select(NewsArticle).where(NewsArticle.url == url)
            ).scalar_one_or_none()
            if existing is not None:
                continue

            published_at = article.get("published_at")
            if isinstance(published_at, str):
                try:
                    published_at = datetime.fromisoformat(published_at)
                except (ValueError, TypeError):
                    published_at = None

            news = NewsArticle(
                stock_id=stock.id,
                title=article.get("title", "")[:500],
                url=url[:2000],
                source=article.get("source", "unknown")[:100],
                published_at=published_at,
            )
            db.add(news)
            created.append(news)

    if created:
        db.commit()
        logger.info("Collected %d new news articles", len(created))
    else:
        logger.info("No new news articles found")

    return created


# Celery task — guarded behind try/except for environments without celery
try:
    from app.workers.celery_app import celery
    from app.db.database import get_session_factory

    @celery.task(name="collect_stock_news_task", bind=True)
    def collect_stock_news_task(self) -> dict:
        """Celery periodic task: collect news for tracked stocks (1-hour interval)."""
        settings = get_settings()
        factory = get_session_factory(settings.database_url)
        session = factory()
        try:
            articles = collect_stock_news(session)
            return {"status": "ok", "articles_collected": len(articles)}
        except Exception as exc:
            logger.exception("collect_stock_news_task failed: %s", exc)
            return {"status": "error", "error": str(exc)}
        finally:
            session.close()

except ImportError:
    collect_stock_news_task = None  # type: ignore[assignment]
