"""Collect general news for tracked stocks (news-001 / pipe-004).

This worker collects news for all stocks that have at least 1 user tracking them.
Korean stocks: NAVER Search API.
US stocks: NewsAPI.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.news_article import NewsArticle
from app.models.stock import Stock
from app.models.watchlist import Watchlist

logger = logging.getLogger(__name__)

MAX_RETRIES = 1
NAVER_API_BASE = "https://openapi.naver.com/v1/search/news.json"
NEWSAPI_BASE = "https://newsapi.org/v2/everything"


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


def _fetch_naver_news(
    stock_name: str,
    client_id: str = "",
    client_secret: str = "",
) -> list[dict]:
    """Fetch news from NAVER Search API for Korean stocks.

    Returns a list of dicts with title, url, source, published_at.
    """
    if not client_id or not client_secret:
        logger.warning("NAVER API credentials not set, skipping Korean news fetch")
        return []

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = httpx.get(
                NAVER_API_BASE,
                params={"query": stock_name, "display": 10, "sort": "date"},
                headers={
                    "X-Naver-Client-Id": client_id,
                    "X-Naver-Client-Secret": client_secret,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("items", []):
                pub_date = None
                date_str = item.get("pubDate", "")
                if date_str:
                    try:
                        pub_date = datetime.strptime(date_str, "%a, %d %b %Y %H:%M:%S %z")
                    except (ValueError, TypeError):
                        pass

                title = item.get("title", "")
                title = title.replace("<b>", "").replace("</b>", "")
                title = title.replace("&quot;", '"').replace("&amp;", "&")

                results.append({
                    "title": title,
                    "url": item.get("originallink", item.get("link", "")),
                    "source": "NAVER",
                    "published_at": pub_date,
                })

            logger.info(
                "NAVER news fetch for '%s': %d articles",
                stock_name, len(results),
            )
            return results
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(
                    "NAVER news retry for '%s' (attempt %d): %s",
                    stock_name, attempt + 1, str(e),
                )
            else:
                logger.error(
                    "NAVER news failed for '%s' after %d attempts: %s",
                    stock_name, MAX_RETRIES + 1, str(e),
                )

    return []


def _fetch_newsapi_articles(
    stock_name: str,
    api_key: str = "",
) -> list[dict]:
    """Fetch news from NewsAPI for US stocks.

    Returns a list of dicts with title, url, source, published_at.
    Free plan: 100 requests/day.
    """
    if not api_key:
        logger.warning("NEWS_API_KEY not set, skipping US news fetch")
        return []

    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = httpx.get(
                NEWSAPI_BASE,
                params={
                    "q": stock_name,
                    "sortBy": "publishedAt",
                    "pageSize": 10,
                    "apiKey": api_key,
                },
                timeout=10.0,
            )
            resp.raise_for_status()
            data = resp.json()

            results = []
            for article in data.get("articles", []):
                pub_date = None
                date_str = article.get("publishedAt", "")
                if date_str:
                    try:
                        pub_date = datetime.fromisoformat(
                            date_str.replace("Z", "+00:00")
                        )
                    except (ValueError, TypeError):
                        pass

                results.append({
                    "title": article.get("title", ""),
                    "url": article.get("url", ""),
                    "source": article.get("source", {}).get("name", "NewsAPI"),
                    "published_at": pub_date,
                })

            logger.info(
                "NewsAPI fetch for '%s': %d articles",
                stock_name, len(results),
            )
            return results
        except Exception as e:
            if attempt < MAX_RETRIES:
                logger.warning(
                    "NewsAPI retry for '%s' (attempt %d): %s",
                    stock_name, attempt + 1, str(e),
                )
            else:
                logger.error(
                    "NewsAPI failed for '%s' after %d attempts: %s",
                    stock_name, MAX_RETRIES + 1, str(e),
                )

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
            raw_articles = _fetch_naver_news(
                stock.name,
                settings.naver_client_id,
                settings.naver_client_secret,
            )
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

    @celery.task(name="collect_stock_news_task", bind=True, max_retries=0)
    def collect_stock_news_task(self) -> dict:
        """Celery periodic task: collect news for tracked stocks (1-hour interval)."""
        settings = get_settings()
        factory = get_session_factory(settings.database_url)
        session = factory()
        try:
            articles = collect_stock_news(session)
            logger.info("Collected %d news articles via Celery", len(articles))
            return {"status": "ok", "articles_collected": len(articles)}
        except Exception as exc:
            logger.error("collect_stock_news_task failed: %s", str(exc))
            return {"status": "error", "error": str(exc)}
        finally:
            session.close()

except ImportError:
    collect_stock_news_task = None  # type: ignore[assignment]
