"""Service and Celery task for KRX stock price collection."""
from __future__ import annotations

import json
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.krx_client import StockPrice, fetch_current_prices, is_krx_market_open
from app.models.report import PriceSnapshot
from app.models.stock import Stock

logger = logging.getLogger(__name__)

KRX_MARKET = "KRX"
PRICE_CACHE_TTL = 300  # 5 minutes


def _refresh_price_cache(stock_id: str, price_data: dict) -> None:
    """Update Redis cache for a stock price after collection."""
    try:
        from app.core.cache import get_redis_client
        client = get_redis_client()
        if client is not None:
            client.setex(
                f"price:{stock_id}",
                PRICE_CACHE_TTL,
                json.dumps(price_data, default=str),
            )
    except Exception:
        logger.warning("Failed to refresh price cache for stock %s", stock_id)


def collect_prices(db: Session, fetch_fn: object | None = None) -> int:
    """Collect current prices for all KRX stocks in DB.

    Args:
        db: Database session.
        fetch_fn: Optional override for price fetching (for testing).

    Returns:
        Number of price snapshots saved.
    """
    stocks = db.execute(
        select(Stock).where(Stock.market == KRX_MARKET)
    ).scalars().all()
    if not stocks:
        return 0

    codes = [s.code for s in stocks]
    code_to_stock = {s.code: s for s in stocks}

    if fetch_fn is not None:
        prices: list[StockPrice] = fetch_fn(codes)
    else:
        prices = fetch_current_prices(codes)

    count = 0
    for p in prices:
        stock = code_to_stock.get(p.code)
        if stock is None:
            continue
        snapshot = PriceSnapshot(
            stock_id=stock.id,
            price=p.price,
            change_pct=p.change_pct,
            volume=p.volume,
        )
        db.add(snapshot)

        _refresh_price_cache(str(stock.id), {
            "stock_id": str(stock.id),
            "price": str(p.price),
            "change_pct": p.change_pct,
            "volume": p.volume,
        })
        count += 1

    db.commit()
    logger.info("Collected %d KRX price snapshots", count)
    return count


# Celery task — guarded behind try/except for environments without celery
try:
    from app.workers.celery_app import celery
    from app.config import get_settings
    from app.db.database import get_session_factory

    @celery.task(name="collect_krx_prices_task", bind=True, max_retries=0)
    def collect_krx_prices_task(self: object) -> dict[str, object]:
        """Celery periodic task: collect KRX stock prices during market hours."""
        if not is_krx_market_open():
            logger.info("KRX market is closed, skipping price collection")
            return {"status": "skipped", "reason": "market_closed"}

        settings = get_settings()
        factory = get_session_factory(settings.database_url)
        session = factory()
        try:
            count = collect_prices(session)
            logger.info("Collected %d KRX price snapshots via Celery", count)
            return {"status": "ok", "count": count}
        except Exception as e:
            logger.error("KRX price collection task failed: %s", str(e))
            return {"status": "error", "error": str(e)}
        finally:
            session.close()

except ImportError:
    collect_krx_prices_task = None  # type: ignore[assignment]
