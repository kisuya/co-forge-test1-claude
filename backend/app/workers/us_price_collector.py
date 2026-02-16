"""Service and Celery task for US stock price collection."""
from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.us_client import USStockPrice, fetch_us_prices
from app.models.report import PriceSnapshot
from app.models.stock import Stock

logger = logging.getLogger(__name__)

ET = ZoneInfo("America/New_York")
US_MARKETS = ("NYSE", "NASDAQ")
MARKET_OPEN_HOUR = 9
MARKET_OPEN_MIN = 30
MARKET_CLOSE_HOUR = 16
MARKET_CLOSE_MIN = 0


def is_us_market_open() -> bool:
    """Check if US stock market is currently open (Mon-Fri, 09:30-16:00 ET)."""
    now = datetime.now(ET)
    if now.weekday() >= 5:
        return False
    open_time = now.replace(
        hour=MARKET_OPEN_HOUR, minute=MARKET_OPEN_MIN, second=0, microsecond=0,
    )
    close_time = now.replace(
        hour=MARKET_CLOSE_HOUR, minute=MARKET_CLOSE_MIN, second=0, microsecond=0,
    )
    return open_time <= now <= close_time


def collect_us_prices(db: Session, fetch_fn: object | None = None) -> int:
    """Collect current prices for all US stocks.

    Args:
        db: Database session.
        fetch_fn: Optional override for price fetching (for testing).

    Returns:
        Number of price snapshots saved.
    """
    stocks = db.execute(
        select(Stock).where(Stock.market.in_(US_MARKETS))
    ).scalars().all()

    if not stocks:
        return 0

    codes = [s.code for s in stocks]
    code_to_stock = {s.code: s for s in stocks}

    if fetch_fn is not None:
        prices: list[USStockPrice] = fetch_fn(codes)
    else:
        prices = fetch_us_prices(codes)

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
        count += 1

    db.commit()
    return count


# Celery task — guarded behind try/except for environments without celery
try:
    from app.workers.celery_app import celery
    from app.config import get_settings
    from app.db.database import get_session_factory

    @celery.task(name="collect_us_prices_task", bind=True, max_retries=0)
    def collect_us_prices_task(self: object) -> dict[str, object]:
        """Celery periodic task: collect US stock prices during market hours."""
        if not is_us_market_open():
            logger.info("US market is closed, skipping price collection")
            return {"status": "skipped", "reason": "market_closed"}

        settings = get_settings()
        factory = get_session_factory(settings.database_url)
        session = factory()
        try:
            count = collect_us_prices(session)
            logger.info("Collected %d US price snapshots", count)
            return {"status": "ok", "count": count}
        finally:
            session.close()

except ImportError:
    collect_us_prices_task = None  # type: ignore[assignment]
