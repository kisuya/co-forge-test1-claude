from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import raise_error
from app.models.report import Report
from app.models.shared_report import SharedReport
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist

router = APIRouter(prefix="/api", tags=["share"])


class ShareResponse(BaseModel):
    share_token: str
    share_url: str
    expires_at: str


class SharedReportResponse(BaseModel):
    stock_name: str
    stock_code: str
    market: str
    report: dict
    shared_at: str
    expires_at: str


@router.post("/reports/{report_id}/share", response_model=ShareResponse)
def create_share(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Create a share link for a report."""
    try:
        report_uuid = uuid.UUID(report_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid report ID format")

    report = db.execute(
        select(Report).where(Report.id == report_uuid)
    ).scalar_one_or_none()

    if report is None:
        raise_error(404, "Report not found")

    # Check that the user tracks the stock
    tracked = db.execute(
        select(Watchlist.id).where(
            Watchlist.stock_id == report.stock_id,
            Watchlist.user_id == user.id,
        )
    ).scalar_one_or_none()

    if tracked is None:
        raise_error(403, "You can only share reports for your tracked stocks")

    # Check for existing valid token
    now = datetime.now(timezone.utc)
    existing = db.execute(
        select(SharedReport).where(
            SharedReport.report_id == report_uuid,
            SharedReport.created_by == user.id,
            SharedReport.expires_at > now,
        )
    ).scalar_one_or_none()

    if existing is not None:
        expires_str = str(existing.expires_at)
        return ShareResponse(
            share_token=existing.share_token,
            share_url=f"/shared/{existing.share_token}",
            expires_at=expires_str,
        )

    # Create new share
    shared = SharedReport(
        report_id=report_uuid,
        created_by=user.id,
    )
    db.add(shared)
    db.commit()
    db.refresh(shared)

    return ShareResponse(
        share_token=shared.share_token,
        share_url=f"/shared/{shared.share_token}",
        expires_at=str(shared.expires_at),
    )


@router.get("/shared/{share_token}", response_model=SharedReportResponse)
def get_shared_report(
    share_token: str,
    db: Session = Depends(get_db),
) -> Any:
    """Get a shared report by token (no auth required)."""
    shared = db.execute(
        select(SharedReport).where(SharedReport.share_token == share_token)
    ).scalar_one_or_none()

    if shared is None:
        raise_error(404, "Shared report not found")

    # Check expiration
    now = datetime.now(timezone.utc)
    expires = shared.expires_at
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    if expires <= now:
        raise_error(410, "이 공유 링크는 만료되었습니다")

    report = db.execute(
        select(Report).where(Report.id == shared.report_id)
    ).scalar_one_or_none()

    if report is None:
        raise_error(404, "Report not found")

    stock = db.execute(
        select(Stock).where(Stock.id == report.stock_id)
    ).scalar_one()

    report_data = {
        "summary": report.summary,
        "causes": report.analysis.get("causes", []) if report.analysis else [],
        "sources": [],
        "similar_cases": report.analysis.get("similar_cases", []) if report.analysis else [],
        "created_at": str(report.created_at) if report.created_at else None,
    }

    # Load sources
    from app.models.report import ReportSource
    sources = db.execute(
        select(ReportSource).where(ReportSource.report_id == report.id)
    ).scalars().all()
    report_data["sources"] = [
        {"source_type": s.source_type, "title": s.title, "url": s.url}
        for s in sources
    ]

    return SharedReportResponse(
        stock_name=stock.name,
        stock_code=stock.code,
        market=stock.market,
        report=report_data,
        shared_at=str(shared.created_at),
        expires_at=str(shared.expires_at),
    )
