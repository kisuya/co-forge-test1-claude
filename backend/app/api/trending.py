from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.report import PriceSnapshot, Report
from app.models.stock import Stock
from app.models.watchlist import Watchlist

router = APIRouter(prefix="/api", tags=["trending"])

CACHE_TTL = 300  # 5 minutes

MARKET_FILTER_MAP = {
    "KR": ["KRX"],
    "US": ["NYSE", "NASDAQ"],
}


class TrendingStockResponse(BaseModel):
    stock_id: str
    stock_name: str
    stock_code: str
    market: str
    change_pct: float
    event_count: int
    latest_report_id: str | None = None
    mini_summary: str | None = None


class PopularStockResponse(BaseModel):
    stock_id: str
    stock_name: str
    stock_code: str
    market: str
    tracking_count: int
    latest_price: float | None = None
    price_change_pct: float | None = None
    latest_change_reason: str | None = None


@router.get("/trending", response_model=list[TrendingStockResponse])
def get_trending(
    db: Session = Depends(get_db),
    market: str = Query("ALL", pattern="^(KR|US|ALL)$"),
    period: str = Query("daily", pattern="^(daily|weekly)$"),
) -> Any:
    """Get trending stocks (recent events, sorted by abs change_pct DESC).

    No authentication required.
    """
    if period == "weekly":
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    else:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    # Build base query for completed reports
    query = (
        select(
            Report.stock_id,
            func.max(func.abs(Report.trigger_change_pct)).label("max_change"),
            func.count(Report.id).label("event_count"),
        )
        .where(
            Report.status == "completed",
            Report.created_at >= cutoff,
        )
    )

    # Apply market filter via join with Stock
    if market != "ALL":
        markets = MARKET_FILTER_MAP[market]
        query = query.join(Stock, Report.stock_id == Stock.id).where(
            Stock.market.in_(markets)
        )

    query = (
        query.group_by(Report.stock_id)
        .order_by(func.max(func.abs(Report.trigger_change_pct)).desc())
        .limit(10)
    )

    results = db.execute(query).all()

    if not results:
        return []

    stock_ids = [r.stock_id for r in results]
    stocks = {
        s.id: s
        for s in db.execute(
            select(Stock).where(Stock.id.in_(stock_ids))
        ).scalars().all()
    }

    # Get latest report per stock (for report_id and mini_summary)
    latest_reports: dict[uuid.UUID, tuple[uuid.UUID, str | None]] = {}
    for sid in stock_ids:
        row = db.execute(
            select(Report.id, Report.summary)
            .where(
                Report.stock_id == sid,
                Report.status == "completed",
                Report.created_at >= cutoff,
            )
            .order_by(Report.created_at.desc())
            .limit(1)
        ).first()
        if row:
            latest_reports[sid] = (row.id, row.summary)

    items = []
    for r in results:
        stock = stocks.get(r.stock_id)
        if not stock:
            continue
        report_data = latest_reports.get(r.stock_id)
        items.append({
            "stock_id": str(r.stock_id),
            "stock_name": stock.name,
            "stock_code": stock.code,
            "market": stock.market,
            "change_pct": float(r.max_change),
            "event_count": r.event_count,
            "latest_report_id": str(report_data[0]) if report_data else None,
            "mini_summary": report_data[1] if report_data else None,
        })
    return items


@router.get("/popular", response_model=list[PopularStockResponse])
def get_popular(
    db: Session = Depends(get_db),
    market: str = Query("ALL", pattern="^(KR|US|ALL)$"),
    min_count: int = Query(1, ge=1),
) -> Any:
    """Get popular stocks (most tracked by users).

    No authentication required.
    """
    # Count tracking per stock
    query = (
        select(
            Watchlist.stock_id,
            func.count(Watchlist.user_id).label("tracking_count"),
        )
        .group_by(Watchlist.stock_id)
        .having(func.count(Watchlist.user_id) >= min_count)
        .order_by(func.count(Watchlist.user_id).desc())
        .limit(10)
    )

    results = db.execute(query).all()

    if not results:
        return []

    stock_ids = [r.stock_id for r in results]
    stocks = {
        s.id: s
        for s in db.execute(
            select(Stock).where(Stock.id.in_(stock_ids))
        ).scalars().all()
    }

    # Apply market filter after fetching stock info
    if market != "ALL":
        markets = MARKET_FILTER_MAP[market]
        stock_ids = [sid for sid in stock_ids if stocks.get(sid) and stocks[sid].market in markets]

    # Get latest price per stock
    latest_prices: dict[uuid.UUID, tuple[float, float]] = {}
    for sid in stock_ids:
        snap = db.execute(
            select(PriceSnapshot.price, PriceSnapshot.change_pct)
            .where(PriceSnapshot.stock_id == sid)
            .order_by(PriceSnapshot.captured_at.desc())
            .limit(1)
        ).first()
        if snap:
            latest_prices[sid] = (float(snap.price), float(snap.change_pct))

    # Get latest report summary per stock
    latest_reasons: dict[uuid.UUID, str | None] = {}
    for sid in stock_ids:
        row = db.execute(
            select(Report.summary)
            .where(
                Report.stock_id == sid,
                Report.status == "completed",
            )
            .order_by(Report.created_at.desc())
            .limit(1)
        ).first()
        if row:
            latest_reasons[sid] = row.summary

    items = []
    for r in results:
        stock = stocks.get(r.stock_id)
        if not stock:
            continue
        # Apply market filter
        if market != "ALL":
            markets = MARKET_FILTER_MAP[market]
            if stock.market not in markets:
                continue
        price_data = latest_prices.get(r.stock_id)
        items.append({
            "stock_id": str(r.stock_id),
            "stock_name": stock.name,
            "stock_code": stock.code,
            "market": stock.market,
            "tracking_count": r.tracking_count,
            "latest_price": price_data[0] if price_data else None,
            "price_change_pct": price_data[1] if price_data else None,
            "latest_change_reason": latest_reasons.get(r.stock_id),
        })
    return items
