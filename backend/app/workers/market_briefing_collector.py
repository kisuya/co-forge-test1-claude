"""Celery task for collecting market data for daily briefings."""
from __future__ import annotations

import logging
from datetime import date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.market_briefing import MarketBriefing
from app.models.report import PriceSnapshot
from app.models.stock import Stock

logger = logging.getLogger(__name__)

KST = ZoneInfo("Asia/Seoul")


def collect_market_data(
    db: Session,
    market: str = "KR",
    target_date: date | None = None,
    fetch_kr_fn: object | None = None,
    fetch_us_fn: object | None = None,
) -> MarketBriefing | None:
    """Collect market data and store as raw JSONB in MarketBriefing.

    Args:
        db: Database session.
        market: 'KR' or 'US'.
        target_date: Date for the briefing. Defaults to today (KST).
        fetch_kr_fn: Optional override for KR data fetching (for testing).
        fetch_us_fn: Optional override for US data fetching (for testing).

    Returns:
        The created or existing MarketBriefing, or None on error.
    """
    if target_date is None:
        target_date = datetime.now(KST).date()

    # Check if briefing already exists for this market+date
    existing = db.execute(
        select(MarketBriefing).where(
            MarketBriefing.market == market,
            MarketBriefing.date == target_date,
        )
    ).scalar_one_or_none()
    if existing is not None:
        logger.info("Briefing already exists for %s %s", market, target_date)
        return existing

    if market == "KR":
        raw_data = _collect_kr_data(db, target_date, fetch_fn=fetch_kr_fn)
    elif market == "US":
        raw_data = _collect_us_data(db, target_date, fetch_fn=fetch_us_fn)
    else:
        logger.error("Unknown market: %s", market)
        return None

    briefing = MarketBriefing(
        market=market,
        date=target_date,
        content=raw_data,
    )
    db.add(briefing)
    db.commit()
    db.refresh(briefing)

    logger.info("Created briefing for %s %s", market, target_date)
    return briefing


def _collect_kr_data(
    db: Session, target_date: date, fetch_fn: object | None = None
) -> dict:
    """Collect Korean market data from PriceSnapshot records."""
    if fetch_fn is not None:
        return fetch_fn(db, target_date)

    # Get KRX stocks with recent snapshots
    stocks = db.execute(
        select(Stock).where(Stock.market == "KRX")
    ).scalars().all()

    if not stocks:
        return {
            "market": "KR",
            "date": str(target_date),
            "total_stocks": 0,
            "top_movers": [],
            "market_stats": {"stocks_up": 0, "stocks_down": 0, "stocks_flat": 0},
        }

    stock_ids = [s.id for s in stocks]
    stock_map = {s.id: s for s in stocks}

    # Get latest price snapshots for each stock
    from sqlalchemy import desc
    snapshots = db.execute(
        select(PriceSnapshot)
        .where(PriceSnapshot.stock_id.in_(stock_ids))
        .order_by(PriceSnapshot.captured_at.desc())
    ).scalars().all()

    # Deduplicate: keep only latest per stock
    seen = set()
    latest_snapshots = []
    for snap in snapshots:
        if snap.stock_id not in seen:
            seen.add(snap.stock_id)
            latest_snapshots.append(snap)

    # Sort by absolute change_pct DESC to find top movers
    latest_snapshots.sort(key=lambda s: abs(s.change_pct), reverse=True)

    top_movers = []
    for snap in latest_snapshots[:10]:
        stock = stock_map.get(snap.stock_id)
        if stock:
            top_movers.append({
                "stock_name": stock.name,
                "stock_code": stock.code,
                "price": float(snap.price),
                "change_pct": snap.change_pct,
                "volume": snap.volume,
            })

    return {
        "market": "KR",
        "date": str(target_date),
        "total_stocks": len(stocks),
        "top_movers": top_movers,
        "market_stats": {
            "stocks_up": sum(1 for s in latest_snapshots if s.change_pct > 0),
            "stocks_down": sum(1 for s in latest_snapshots if s.change_pct < 0),
            "stocks_flat": sum(1 for s in latest_snapshots if s.change_pct == 0),
        },
    }


def _collect_us_data(
    db: Session, target_date: date, fetch_fn: object | None = None
) -> dict:
    """Collect US market data from PriceSnapshot records."""
    if fetch_fn is not None:
        return fetch_fn(db, target_date)

    stocks = db.execute(
        select(Stock).where(Stock.market.in_(("NYSE", "NASDAQ")))
    ).scalars().all()

    if not stocks:
        return {
            "market": "US",
            "date": str(target_date),
            "total_stocks": 0,
            "top_movers": [],
            "market_stats": {"stocks_up": 0, "stocks_down": 0, "stocks_flat": 0},
        }

    stock_ids = [s.id for s in stocks]
    stock_map = {s.id: s for s in stocks}

    from sqlalchemy import desc
    snapshots = db.execute(
        select(PriceSnapshot)
        .where(PriceSnapshot.stock_id.in_(stock_ids))
        .order_by(PriceSnapshot.captured_at.desc())
    ).scalars().all()

    seen = set()
    latest_snapshots = []
    for snap in snapshots:
        if snap.stock_id not in seen:
            seen.add(snap.stock_id)
            latest_snapshots.append(snap)

    latest_snapshots.sort(key=lambda s: abs(s.change_pct), reverse=True)

    top_movers = []
    for snap in latest_snapshots[:10]:
        stock = stock_map.get(snap.stock_id)
        if stock:
            top_movers.append({
                "stock_name": stock.name,
                "stock_code": stock.code,
                "market": stock.market,
                "price": float(snap.price),
                "change_pct": snap.change_pct,
                "volume": snap.volume,
            })

    return {
        "market": "US",
        "date": str(target_date),
        "total_stocks": len(stocks),
        "top_movers": top_movers,
        "market_stats": {
            "stocks_up": sum(1 for s in latest_snapshots if s.change_pct > 0),
            "stocks_down": sum(1 for s in latest_snapshots if s.change_pct < 0),
            "stocks_flat": sum(1 for s in latest_snapshots if s.change_pct == 0),
        },
    }


# Celery task — guarded behind try/except for environments without celery
try:
    from app.workers.celery_app import celery
    from app.config import get_settings
    from app.db.database import get_session_factory

    @celery.task(name="collect_market_data_task", bind=True, max_retries=0)
    def collect_market_data_task(self: object, market: str = "KR") -> dict:
        """Celery periodic task: collect market data for daily briefing.

        KR: runs after KRX close (~15:30 KST).
        US: runs after US close (~06:00 KST next day).
        """
        settings = get_settings()
        factory = get_session_factory(settings.database_url)
        session = factory()
        try:
            briefing = collect_market_data(session, market=market)
            if briefing is None:
                return {"status": "error", "market": market}
            return {
                "status": "ok",
                "market": market,
                "date": str(briefing.date),
                "briefing_id": briefing.id,
            }
        finally:
            session.close()

except ImportError:
    collect_market_data_task = None  # type: ignore[assignment]
