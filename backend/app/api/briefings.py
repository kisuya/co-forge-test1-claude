from __future__ import annotations

from datetime import date, datetime
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.exceptions import raise_error
from app.models.market_briefing import MarketBriefing

from fastapi import Depends

router = APIRouter(prefix="/api/briefings", tags=["briefings"])


class BriefingResponse(BaseModel):
    id: int
    market: str
    date: str
    summary: str | None = None
    key_issues: list[dict] | None = None
    top_movers: list[dict] | None = None
    created_at: str | None = None


class BriefingTodayResponse(BriefingResponse):
    is_today: bool = True


@router.get("", response_model=list[BriefingResponse])
def list_briefings(
    market: str = Query("KR", pattern="^(KR|US)$"),
    limit: int = Query(1, ge=1, le=30),
    db: Session = Depends(get_db),
) -> Any:
    """List market briefings, newest first."""
    briefings = db.execute(
        select(MarketBriefing)
        .where(MarketBriefing.market == market)
        .order_by(MarketBriefing.date.desc())
        .limit(limit)
    ).scalars().all()

    return [_to_response(b) for b in briefings]


@router.get("/today", response_model=BriefingTodayResponse)
def get_today_briefing(
    market: str = Query("KR", pattern="^(KR|US)$"),
    db: Session = Depends(get_db),
) -> Any:
    """Get today's briefing. If not available, returns the most recent one."""
    from zoneinfo import ZoneInfo

    today = datetime.now(ZoneInfo("Asia/Seoul")).date()

    # Try today first
    briefing = db.execute(
        select(MarketBriefing).where(
            MarketBriefing.market == market,
            MarketBriefing.date == today,
        )
    ).scalar_one_or_none()

    if briefing is not None:
        resp = _to_response(briefing)
        return BriefingTodayResponse(**resp.model_dump(), is_today=True)

    # Fall back to most recent
    briefing = db.execute(
        select(MarketBriefing)
        .where(MarketBriefing.market == market)
        .order_by(MarketBriefing.date.desc())
        .limit(1)
    ).scalar_one_or_none()

    if briefing is None:
        return BriefingTodayResponse(
            id=0,
            market=market,
            date=str(today),
            summary=None,
            key_issues=None,
            top_movers=None,
            is_today=False,
        )

    resp = _to_response(briefing)
    return BriefingTodayResponse(**resp.model_dump(), is_today=False)


def _to_response(briefing: MarketBriefing) -> BriefingResponse:
    """Convert a MarketBriefing model to response."""
    content = briefing.content or {}
    return BriefingResponse(
        id=briefing.id,
        market=briefing.market,
        date=str(briefing.date),
        summary=content.get("summary"),
        key_issues=content.get("key_issues"),
        top_movers=content.get("top_movers"),
        created_at=str(briefing.created_at) if briefing.created_at else None,
    )
