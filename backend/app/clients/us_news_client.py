"""US news client using NewsAPI for English news collection."""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 3600  # 1 hour cache
NEWSAPI_BASE = "https://newsapi.org/v2/everything"

_cache: dict[str, tuple[float, list["USNewsItem"]]] = {}


@dataclass
class USNewsItem:
    """A single English news article about a US stock."""

    title: str
    url: str
    source: str
    published_at: datetime | None = None
    summary: str = ""


def _get_cache(stock_code: str) -> list[USNewsItem] | None:
    """Return cached results if still valid, else None."""
    entry = _cache.get(stock_code)
    if entry is None:
        return None
    ts, items = entry
    if time.time() - ts > CACHE_TTL_SECONDS:
        del _cache[stock_code]
        return None
    return items


def _set_cache(stock_code: str, items: list[USNewsItem]) -> None:
    """Store results in cache."""
    _cache[stock_code] = (time.time(), items)


def clear_cache() -> None:
    """Clear the entire news cache (for testing)."""
    _cache.clear()


def fetch_us_news(
    stock_code: str, stock_name: str, hours: int = 24,
) -> list[USNewsItem]:
    """Fetch recent English news for a US stock from NewsAPI.

    Returns cached results if queried within the last hour.
    Returns empty list on failure (does not raise).
    """
    cached = _get_cache(stock_code)
    if cached is not None:
        return cached

    settings = get_settings()
    api_key = getattr(settings, "news_api_key", "") or ""
    if not api_key:
        logger.warning("NEWS_API_KEY not set, skipping US news fetch")
        return []

    try:
        from_dt = (datetime.utcnow() - timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
        resp = httpx.get(
            NEWSAPI_BASE,
            params={
                "q": f"{stock_code} OR {stock_name}",
                "from": from_dt,
                "sortBy": "publishedAt",
                "language": "en",
                "pageSize": "10",
                "apiKey": api_key,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()

        items: list[USNewsItem] = []
        for article in data.get("articles", []):
            pub_at = None
            raw = article.get("publishedAt")
            if raw:
                try:
                    pub_at = datetime.fromisoformat(raw.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pass
            items.append(USNewsItem(
                title=article.get("title", ""),
                url=article.get("url", ""),
                source=article.get("source", {}).get("name", ""),
                published_at=pub_at,
                summary=article.get("description", "") or "",
            ))

        _set_cache(stock_code, items)
        return items
    except Exception:
        logger.warning("Failed to fetch US news for %s, returning empty", stock_code)
        return []
