from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.cache import get_redis_client
from app.core.exceptions import raise_error
from app.models.report import PriceSnapshot
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

MAX_WATCHLIST_SIZE = 50

MARKET_CURRENCY = {
    "KRX": "KRW",
    "NYSE": "USD",
    "NASDAQ": "USD",
}

PRICE_CACHE_TTL = 300  # 5 minutes


class WatchlistAddRequest(BaseModel):
    stock_id: str


class WatchlistUpdateRequest(BaseModel):
    threshold: float = Field(ge=1.0, le=10.0)


class WatchlistItemResponse(BaseModel):
    id: str
    stock_id: str
    stock_code: str
    stock_name: str
    stock_market: str
    threshold: float
    latest_price: float | None = None
    price_change: float | None = None
    price_change_pct: float | None = None
    price_currency: str | None = None
    price_updated_at: str | None = None
    is_price_available: bool = False
    price_freshness: str = "unavailable"
    tracking_count: int = 0


def _compute_freshness(captured_at: datetime) -> str:
    """Compute price freshness based on age of snapshot."""
    now = datetime.now(timezone.utc)
    if captured_at.tzinfo is None:
        captured_at = captured_at.replace(tzinfo=timezone.utc)
    age = now - captured_at
    if age <= timedelta(minutes=30):
        return "live"
    if age <= timedelta(hours=6):
        return "delayed"
    return "stale"


def _serialize_snapshot(snapshot: PriceSnapshot) -> dict[str, Any]:
    """Serialize a PriceSnapshot to a dict for caching."""
    captured = snapshot.captured_at
    if isinstance(captured, datetime):
        captured_str = captured.isoformat()
    else:
        captured_str = str(captured)
    return {
        "stock_id": str(snapshot.stock_id),
        "price": str(snapshot.price),
        "change_pct": snapshot.change_pct,
        "volume": snapshot.volume,
        "captured_at": captured_str,
    }


def _get_cached_price(stock_id: uuid.UUID) -> dict[str, Any] | None:
    """Try to get a cached price from Redis."""
    client = get_redis_client()
    if client is None:
        return None
    try:
        cached = client.get(f"price:{stock_id}")
        if cached is not None:
            return json.loads(cached)
    except Exception:
        pass
    return None


def _set_cached_price(stock_id: uuid.UUID, data: dict[str, Any]) -> None:
    """Store price data in Redis cache."""
    client = get_redis_client()
    if client is None:
        return
    try:
        client.setex(f"price:{stock_id}", PRICE_CACHE_TTL, json.dumps(data))
    except Exception:
        pass


def _get_latest_prices(db: Session, stock_ids: list[uuid.UUID]) -> dict[uuid.UUID, PriceSnapshot]:
    """Get the latest PriceSnapshot for each stock_id, using Redis cache when available."""
    if not stock_ids:
        return {}

    result: dict[uuid.UUID, PriceSnapshot] = {}
    missing_ids: list[uuid.UUID] = []

    # Check Redis cache first
    for sid in stock_ids:
        cached = _get_cached_price(sid)
        if cached is not None:
            # Reconstruct a lightweight PriceSnapshot-like object
            snap = PriceSnapshot(
                stock_id=uuid.UUID(cached["stock_id"]),
                price=cached["price"],
                change_pct=cached["change_pct"],
                volume=cached.get("volume", 0),
            )
            snap.captured_at = datetime.fromisoformat(cached["captured_at"])
            result[sid] = snap
        else:
            missing_ids.append(sid)

    if not missing_ids:
        return result

    # Fetch missing from DB
    latest_subq = (
        select(
            PriceSnapshot.stock_id,
            func.max(PriceSnapshot.captured_at).label("max_captured"),
        )
        .where(PriceSnapshot.stock_id.in_(missing_ids))
        .group_by(PriceSnapshot.stock_id)
        .subquery()
    )

    stmt = (
        select(PriceSnapshot)
        .join(
            latest_subq,
            (PriceSnapshot.stock_id == latest_subq.c.stock_id)
            & (PriceSnapshot.captured_at == latest_subq.c.max_captured),
        )
    )
    snapshots = db.execute(stmt).scalars().all()
    for s in snapshots:
        result[s.stock_id] = s
        _set_cached_price(s.stock_id, _serialize_snapshot(s))

    return result


def _get_tracking_counts(db: Session, stock_ids: list[uuid.UUID]) -> dict[uuid.UUID, int]:
    """Get the number of distinct users tracking each stock."""
    if not stock_ids:
        return {}
    stmt = (
        select(
            Watchlist.stock_id,
            func.count(func.distinct(Watchlist.user_id)).label("cnt"),
        )
        .where(Watchlist.stock_id.in_(stock_ids))
        .group_by(Watchlist.stock_id)
    )
    rows = db.execute(stmt).all()
    return {row[0]: row[1] for row in rows}


def _build_item_response(
    item: Watchlist, stock: Stock, snapshot: PriceSnapshot | None,
    tracking_count: int = 0,
) -> WatchlistItemResponse:
    """Build a WatchlistItemResponse with optional price data."""
    price_data: dict[str, Any] = {}
    if snapshot is not None:
        price_val = float(snapshot.price)
        change_pct = snapshot.change_pct
        # Derive absolute change from price and change_pct
        if change_pct != 0:
            prev_price = price_val / (1 + change_pct / 100)
            price_change = price_val - prev_price
        else:
            price_change = 0.0

        updated_at = snapshot.captured_at
        if isinstance(updated_at, datetime):
            updated_at_str = updated_at.isoformat()
        else:
            updated_at_str = str(updated_at)

        freshness = _compute_freshness(snapshot.captured_at)

        price_data = {
            "latest_price": price_val,
            "price_change": round(price_change, 2),
            "price_change_pct": change_pct,
            "price_currency": MARKET_CURRENCY.get(stock.market, "KRW"),
            "price_updated_at": updated_at_str,
            "is_price_available": True,
            "price_freshness": freshness,
        }

    return WatchlistItemResponse(
        id=str(item.id),
        stock_id=str(item.stock_id),
        stock_code=stock.code,
        stock_name=stock.name,
        stock_market=stock.market,
        threshold=item.threshold,
        tracking_count=tracking_count,
        **price_data,
    )


@router.get("", response_model=list[WatchlistItemResponse])
def get_watchlist(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get all stocks in the user's watchlist."""
    items = db.execute(
        select(Watchlist).where(Watchlist.user_id == user.id)
    ).scalars().all()

    # Batch load stocks
    stock_ids = [item.stock_id for item in items]
    stocks_map: dict[uuid.UUID, Stock] = {}
    if stock_ids:
        stocks = db.execute(
            select(Stock).where(Stock.id.in_(stock_ids))
        ).scalars().all()
        stocks_map = {s.id: s for s in stocks}

    # Batch load latest prices and tracking counts
    prices_map = _get_latest_prices(db, stock_ids)
    tracking_map = _get_tracking_counts(db, stock_ids)

    result = []
    for item in items:
        stock = stocks_map[item.stock_id]
        snapshot = prices_map.get(item.stock_id)
        count = tracking_map.get(item.stock_id, 0)
        result.append(_build_item_response(item, stock, snapshot, count))
    return result


@router.post("", status_code=status.HTTP_201_CREATED, response_model=WatchlistItemResponse)
def add_to_watchlist(
    body: WatchlistAddRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Add a stock to the user's watchlist."""
    stock_uuid = uuid.UUID(body.stock_id)

    stock = db.execute(
        select(Stock).where(Stock.id == stock_uuid)
    ).scalar_one_or_none()
    if stock is None:
        raise_error(404, "Stock not found")

    existing = db.execute(
        select(Watchlist).where(
            Watchlist.user_id == user.id,
            Watchlist.stock_id == stock_uuid,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise_error(409, "Stock already in watchlist")

    count = db.execute(
        select(Watchlist).where(Watchlist.user_id == user.id)
    ).scalars().all()
    if len(count) >= MAX_WATCHLIST_SIZE:
        raise_error(400, "Watchlist limit reached (50)")

    item = Watchlist(user_id=user.id, stock_id=stock_uuid)
    db.add(item)
    db.commit()
    db.refresh(item)

    prices_map = _get_latest_prices(db, [stock_uuid])
    snapshot = prices_map.get(stock_uuid)
    tracking_map = _get_tracking_counts(db, [stock_uuid])
    count = tracking_map.get(stock_uuid, 0)
    return _build_item_response(item, stock, snapshot, count)


@router.delete("/{item_id}")
def remove_from_watchlist(
    item_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Remove a stock from the user's watchlist."""
    item = db.execute(
        select(Watchlist).where(
            Watchlist.id == uuid.UUID(item_id),
            Watchlist.user_id == user.id,
        )
    ).scalar_one_or_none()

    if item is None:
        raise_error(404, "Watchlist item not found")

    db.delete(item)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.patch("/{item_id}", response_model=WatchlistItemResponse)
def update_threshold(
    item_id: str,
    body: WatchlistUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update the threshold for a watchlist item."""
    item = db.execute(
        select(Watchlist).where(
            Watchlist.id == uuid.UUID(item_id),
            Watchlist.user_id == user.id,
        )
    ).scalar_one_or_none()

    if item is None:
        raise_error(404, "Watchlist item not found")

    item.threshold = body.threshold
    db.commit()
    db.refresh(item)

    stock = db.execute(
        select(Stock).where(Stock.id == item.stock_id)
    ).scalar_one()

    prices_map = _get_latest_prices(db, [item.stock_id])
    snapshot = prices_map.get(item.stock_id)
    tracking_map = _get_tracking_counts(db, [item.stock_id])
    count = tracking_map.get(item.stock_id, 0)
    return _build_item_response(item, stock, snapshot, count)
