from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import raise_error
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist

router = APIRouter(prefix="/api/watchlist", tags=["watchlist"])

MAX_WATCHLIST_SIZE = 50


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


@router.get("", response_model=list[WatchlistItemResponse])
def get_watchlist(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get all stocks in the user's watchlist."""
    items = db.execute(
        select(Watchlist).where(Watchlist.user_id == user.id)
    ).scalars().all()

    result = []
    for item in items:
        stock = db.execute(
            select(Stock).where(Stock.id == item.stock_id)
        ).scalar_one()
        result.append(
            WatchlistItemResponse(
                id=str(item.id),
                stock_id=str(item.stock_id),
                stock_code=stock.code,
                stock_name=stock.name,
                stock_market=stock.market,
                threshold=item.threshold,
            )
        )
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

    return WatchlistItemResponse(
        id=str(item.id),
        stock_id=str(item.stock_id),
        stock_code=stock.code,
        stock_name=stock.name,
        stock_market=stock.market,
        threshold=item.threshold,
    )


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

    return WatchlistItemResponse(
        id=str(item.id),
        stock_id=str(item.stock_id),
        stock_code=stock.code,
        stock_name=stock.name,
        stock_market=stock.market,
        threshold=item.threshold,
    )
