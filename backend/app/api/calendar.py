from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta
from typing import Any

from fastapi import APIRouter, Depends, Header, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.config import get_settings
from app.core.exceptions import raise_error
from app.models.calendar_event import CalendarEvent
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist

router = APIRouter(prefix="/api/calendar", tags=["calendar"])


class CalendarEventResponse(BaseModel):
    id: int
    event_type: str
    title: str
    description: str | None = None
    event_date: str
    market: str
    stock_name: str | None = None
    is_tracked: bool = False


def _get_optional_user(
    authorization: str | None = Header(None),
    db: Session = Depends(get_db),
) -> User | None:
    """Try to decode JWT, return None if not authenticated."""
    if not authorization:
        return None
    import jwt as pyjwt

    token = authorization.replace("Bearer ", "")
    try:
        settings = get_settings()
        payload = pyjwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    except Exception:
        return None
    if payload.get("type") != "access":
        return None
    user_id = payload.get("sub")
    if user_id is None:
        return None
    return db.execute(
        select(User).where(User.id == uuid.UUID(user_id))
    ).scalar_one_or_none()


@router.get("", response_model=list[CalendarEventResponse])
def list_calendar_events(
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    market: str = Query("ALL", pattern="^(KR|US|ALL)$"),
    event_type: str | None = Query(None),
    user: User | None = Depends(_get_optional_user),
    db: Session = Depends(get_db),
) -> Any:
    """List calendar events in a date range (max 90 days).

    No authentication required. Authenticated users get is_tracked flag.
    """
    try:
        start = date.fromisoformat(start_date)
        end = date.fromisoformat(end_date)
    except ValueError:
        raise_error(422, "날짜 형식이 올바르지 않습니다")

    if start > end:
        raise_error(422, "시작일이 종료일보다 클 수 없습니다")

    delta = (end - start).days
    if delta > 90:
        raise_error(422, "최대 90일 범위만 조회 가능합니다")

    # Build query
    query = (
        select(CalendarEvent)
        .where(
            CalendarEvent.event_date >= start,
            CalendarEvent.event_date <= end,
        )
        .order_by(CalendarEvent.event_date.asc())
    )

    if market != "ALL":
        query = query.where(CalendarEvent.market == market)

    if event_type:
        query = query.where(CalendarEvent.event_type == event_type)

    events = db.execute(query).scalars().all()

    # Get tracked stock IDs for the user
    tracked_stock_ids: set[uuid.UUID] = set()
    if user is not None:
        rows = db.execute(
            select(Watchlist.stock_id).where(Watchlist.user_id == user.id)
        ).all()
        tracked_stock_ids = {r[0] for r in rows}

    # Get stock names for events with stock_id
    stock_ids = {e.stock_id for e in events if e.stock_id is not None}
    stock_map: dict[uuid.UUID, str] = {}
    if stock_ids:
        stocks = db.execute(
            select(Stock).where(Stock.id.in_(stock_ids))
        ).scalars().all()
        stock_map = {s.id: s.name for s in stocks}

    return [
        CalendarEventResponse(
            id=e.id,
            event_type=e.event_type,
            title=e.title,
            description=e.description,
            event_date=str(e.event_date),
            market=e.market,
            stock_name=stock_map.get(e.stock_id) if e.stock_id else None,
            is_tracked=e.stock_id in tracked_stock_ids if e.stock_id else False,
        )
        for e in events
    ]


@router.get("/week", response_model=list[CalendarEventResponse])
def get_week_events(
    user: User | None = Depends(_get_optional_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get this week's events (Monday to Friday).

    No authentication required. Authenticated users get is_tracked flag.
    """
    today = date.today()
    # Monday of current week
    monday = today - timedelta(days=today.weekday())
    friday = monday + timedelta(days=4)

    events = db.execute(
        select(CalendarEvent)
        .where(
            CalendarEvent.event_date >= monday,
            CalendarEvent.event_date <= friday,
        )
        .order_by(CalendarEvent.event_date.asc())
    ).scalars().all()

    # Get tracked stock IDs for the user
    tracked_stock_ids: set[uuid.UUID] = set()
    if user is not None:
        rows = db.execute(
            select(Watchlist.stock_id).where(Watchlist.user_id == user.id)
        ).all()
        tracked_stock_ids = {r[0] for r in rows}

    # Get stock names
    stock_ids = {e.stock_id for e in events if e.stock_id is not None}
    stock_map: dict[uuid.UUID, str] = {}
    if stock_ids:
        stocks = db.execute(
            select(Stock).where(Stock.id.in_(stock_ids))
        ).scalars().all()
        stock_map = {s.id: s.name for s in stocks}

    return [
        CalendarEventResponse(
            id=e.id,
            event_type=e.event_type,
            title=e.title,
            description=e.description,
            event_date=str(e.event_date),
            market=e.market,
            stock_name=stock_map.get(e.stock_id) if e.stock_id else None,
            is_tracked=e.stock_id in tracked_stock_ids if e.stock_id else False,
        )
        for e in events
    ]
