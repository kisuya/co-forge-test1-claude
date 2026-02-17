from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import raise_error
from app.core.sanitize import strip_html_tags
from app.models.report import PriceSnapshot, Report
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.stock_service import search_stocks

MARKET_CURRENCY = {
    "KRX": "KRW",
    "NYSE": "USD",
    "NASDAQ": "USD",
}

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


class StockResponse(BaseModel):
    id: str
    code: str
    name: str
    market: str
    sector: str | None = None


class StockDetailResponse(BaseModel):
    id: str
    name: str
    code: str
    market: str
    latest_price: float | None = None
    price_change_pct: float | None = None
    price_currency: str | None = None
    price_freshness: str = "unavailable"
    tracking_count: int = 0
    tracking_since: str | None = None
    is_tracked_by_me: bool = False


class HistoryEventResponse(BaseModel):
    id: str
    date: str
    change_pct: float
    direction: str
    summary: str | None = None
    confidence: str | None = None
    report_id: str


class PaginationResponse(BaseModel):
    page: int
    per_page: int
    total: int
    has_more: bool


class StockHistoryResponse(BaseModel):
    stock_id: str
    stock_name: str
    stock_code: str
    market: str
    tracking_since: str | None = None
    events: list[HistoryEventResponse]
    pagination: PaginationResponse
    message: str | None = None


@router.get("/search", response_model=list[StockResponse])
def search(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    market: str = Query("kr", description="Market filter: kr, us, or all"),
    db: Session = Depends(get_db),
) -> Any:
    """Search stocks by name or code, filtered by market."""
    q = strip_html_tags(q)
    stocks = search_stocks(db, q, market=market)
    return [
        StockResponse(
            id=str(s.id), code=s.code, name=s.name,
            market=s.market, sector=s.sector,
        )
        for s in stocks
    ]


def _compute_freshness(captured_at) -> str:
    """Compute price freshness based on age of snapshot."""
    from datetime import timedelta
    now = datetime.now(timezone.utc)
    if hasattr(captured_at, 'tzinfo') and captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    age = now - captured_at
    if age <= timedelta(minutes=30):
        return "live"
    if age <= timedelta(hours=6):
        return "delayed"
    return "stale"


@router.get("/{stock_id}", response_model=StockDetailResponse)
def get_stock_detail(
    stock_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get stock detail info for stock detail page header."""
    try:
        stock_uuid = uuid.UUID(stock_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid stock ID format")

    stock = db.execute(
        select(Stock).where(Stock.id == stock_uuid)
    ).scalar_one_or_none()

    if stock is None:
        raise_error(404, "Stock not found")

    # Latest price
    latest_snapshot = db.execute(
        select(PriceSnapshot)
        .where(PriceSnapshot.stock_id == stock_uuid)
        .order_by(PriceSnapshot.captured_at.desc())
        .limit(1)
    ).scalar_one_or_none()

    latest_price = None
    price_change_pct = None
    price_currency = None
    price_freshness = "unavailable"
    if latest_snapshot is not None:
        latest_price = float(latest_snapshot.price)
        price_change_pct = latest_snapshot.change_pct
        price_currency = MARKET_CURRENCY.get(stock.market, "KRW")
        price_freshness = _compute_freshness(latest_snapshot.captured_at)

    # Tracking count
    tracking_count = db.execute(
        select(func.count(func.distinct(Watchlist.user_id)))
        .where(Watchlist.stock_id == stock_uuid)
    ).scalar_one()

    # Tracking since
    tracking_since_val = db.execute(
        select(func.min(Watchlist.created_at)).where(Watchlist.stock_id == stock_uuid)
    ).scalar_one_or_none()
    tracking_since = str(tracking_since_val) if tracking_since_val else None

    # Is tracked by current user
    is_tracked = db.execute(
        select(Watchlist.id).where(
            Watchlist.stock_id == stock_uuid,
            Watchlist.user_id == user.id,
        )
    ).scalar_one_or_none() is not None

    return StockDetailResponse(
        id=str(stock.id),
        name=stock.name,
        code=stock.code,
        market=stock.market,
        latest_price=latest_price,
        price_change_pct=price_change_pct,
        price_currency=price_currency,
        price_freshness=price_freshness,
        tracking_count=tracking_count,
        tracking_since=tracking_since,
        is_tracked_by_me=is_tracked,
    )


def _extract_summary(analysis: dict | None) -> str | None:
    """Extract a 1-line summary from Report.analysis JSONB."""
    if analysis is None:
        return None
    # Try common keys for summary
    for key in ("summary", "one_line_summary", "brief"):
        if key in analysis and isinstance(analysis[key], str):
            return analysis[key][:200]
    # Try causes list
    causes = analysis.get("causes")
    if isinstance(causes, list) and causes:
        first = causes[0]
        if isinstance(first, dict):
            return str(first.get("description", first.get("cause", "")))[:200]
        if isinstance(first, str):
            return first[:200]
    return None


def _extract_confidence(analysis: dict | None) -> str | None:
    """Extract confidence level from Report.analysis JSONB."""
    if analysis is None:
        return None
    conf = analysis.get("confidence")
    if conf in ("high", "medium", "low"):
        return conf
    return None


@router.get("/{stock_id}/history", response_model=StockHistoryResponse)
def get_stock_history(
    stock_id: str,
    page: int = Query(1, ge=1, le=1000),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get event history timeline for a stock."""
    try:
        stock_uuid = uuid.UUID(stock_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid stock ID format")

    stock = db.execute(
        select(Stock).where(Stock.id == stock_uuid)
    ).scalar_one_or_none()

    if stock is None:
        raise_error(404, "Stock not found")

    # Get tracking_since: earliest watchlist creation for this stock
    tracking_since_row = db.execute(
        select(func.min(Watchlist.created_at)).where(Watchlist.stock_id == stock_uuid)
    ).scalar_one_or_none()

    tracking_since = None
    if tracking_since_row is not None:
        tracking_since = str(tracking_since_row)

    # Count total completed reports for this stock
    total = db.execute(
        select(func.count(Report.id)).where(
            Report.stock_id == stock_uuid,
            Report.status == "completed",
        )
    ).scalar_one()

    # Fetch paginated reports
    offset = (page - 1) * per_page
    reports = db.execute(
        select(Report)
        .where(Report.stock_id == stock_uuid, Report.status == "completed")
        .order_by(Report.created_at.desc())
        .offset(offset)
        .limit(per_page)
    ).scalars().all()

    events = []
    for r in reports:
        change = r.trigger_change_pct
        direction = "up" if change > 0 else "down" if change < 0 else "up"
        summary_text = _extract_summary(r.analysis) or r.summary
        confidence = _extract_confidence(r.analysis)
        events.append(
            HistoryEventResponse(
                id=str(r.id),
                date=str(r.created_at.date()) if r.created_at else "",
                change_pct=change,
                direction=direction,
                summary=summary_text,
                confidence=confidence,
                report_id=str(r.id),
            )
        )

    has_more = (offset + per_page) < total
    message = None
    if not events and page == 1:
        message = "아직 추적 이벤트가 없습니다"

    return StockHistoryResponse(
        stock_id=str(stock.id),
        stock_name=stock.name,
        stock_code=stock.code,
        market=stock.market,
        tracking_since=tracking_since,
        events=events,
        pagination=PaginationResponse(
            page=page, per_page=per_page, total=total, has_more=has_more,
        ),
        message=message,
    )
