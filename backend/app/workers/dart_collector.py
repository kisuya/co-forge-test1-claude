"""Service and Celery task for DART disclosure collection."""
from __future__ import annotations

import json
import logging

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.clients.dart_client import Disclosure, fetch_disclosures
from app.config import get_settings
from app.models.news_article import NewsArticle
from app.models.stock import Stock
from app.models.watchlist import Watchlist

logger = logging.getLogger(__name__)

DART_SOURCE = "DART"
PIPELINE_CACHE_KEY = "pipeline:dart_collector:last_run"
PIPELINE_CACHE_TTL = 7200  # 2 hours


def _get_tracked_krx_stocks(db: Session) -> list[Stock]:
    """Return KRX stocks tracked by at least 1 user."""
    subq = (
        select(Watchlist.stock_id)
        .group_by(Watchlist.stock_id)
        .having(func.count(Watchlist.user_id) >= 1)
        .subquery()
    )
    return list(
        db.execute(
            select(Stock).where(
                Stock.id.in_(select(subq.c.stock_id)),
                Stock.market == "KRX",
            )
        ).scalars().all()
    )


def _update_pipeline_status(count: int, status: str) -> None:
    """Update Redis pipeline status after collection run."""
    try:
        from app.core.cache import get_redis_client
        client = get_redis_client()
        if client is not None:
            from datetime import datetime, timezone
            client.setex(
                PIPELINE_CACHE_KEY,
                PIPELINE_CACHE_TTL,
                json.dumps({
                    "status": status,
                    "items_collected": count,
                    "last_run_at": datetime.now(timezone.utc).isoformat(),
                }, default=str),
            )
    except Exception:
        logger.warning("Failed to update DART pipeline status in Redis")


def collect_dart_disclosures(
    db: Session,
    fetch_fn: object | None = None,
) -> int:
    """Collect DART disclosures for all tracked KRX stocks.

    Stores disclosures as NewsArticle entries with source="DART".
    Uses URL-based deduplication to prevent duplicates.

    Args:
        db: Database session.
        fetch_fn: Optional override for disclosure fetching (for testing).

    Returns:
        Number of new disclosures saved.
    """
    settings = get_settings()
    if not settings.dart_api_key and fetch_fn is None:
        logger.warning("DART_API_KEY not set, skipping disclosure collection")
        return 0

    tracked_stocks = _get_tracked_krx_stocks(db)
    if not tracked_stocks:
        logger.info("No tracked KRX stocks, skipping DART collection")
        return 0

    count = 0
    for stock in tracked_stocks:
        if fetch_fn is not None:
            disclosures: list[Disclosure] = fetch_fn(stock.code)
        else:
            disclosures = fetch_disclosures(stock.code)

        for d in disclosures:
            if not d.url:
                continue

            # URL-based deduplication
            existing = db.execute(
                select(NewsArticle).where(NewsArticle.url == d.url)
            ).scalar_one_or_none()
            if existing is not None:
                continue

            article = NewsArticle(
                stock_id=stock.id,
                title=d.title[:500],
                url=d.url[:2000],
                source=DART_SOURCE,
                published_at=d.published_at,
            )
            db.add(article)
            count += 1

    if count > 0:
        db.commit()

    logger.info("Collected %d new DART disclosures", count)
    _update_pipeline_status(count, "ok")
    return count


# Celery task — guarded behind try/except for environments without celery
try:
    from app.workers.celery_app import celery
    from app.db.database import get_session_factory

    @celery.task(name="collect_dart_disclosures_task", bind=True, max_retries=0)
    def collect_dart_disclosures_task(self: object) -> dict[str, object]:
        """Celery periodic task: collect DART disclosures during KRX market hours."""
        settings = get_settings()
        if not settings.dart_api_key:
            logger.info("DART_API_KEY not set, skipping disclosure collection task")
            return {"status": "skipped", "reason": "no_api_key"}

        factory = get_session_factory(settings.database_url)
        session = factory()
        try:
            count = collect_dart_disclosures(session)
            logger.info("Collected %d DART disclosures via Celery", count)
            return {"status": "ok", "count": count}
        except Exception as e:
            logger.error("DART disclosure collection task failed: %s", str(e))
            _update_pipeline_status(0, "error")
            return {"status": "error", "error": str(e)}
        finally:
            session.close()

except ImportError:
    collect_dart_disclosures_task = None  # type: ignore[assignment]
