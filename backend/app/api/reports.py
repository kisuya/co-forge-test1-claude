from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.report import Report, ReportSource
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist

router = APIRouter(prefix="/api/reports", tags=["reports"])


class ReportSourceResponse(BaseModel):
    id: str
    source_type: str
    title: str
    url: str


class ReportResponse(BaseModel):
    id: str
    stock_id: str
    stock_code: str
    stock_name: str
    trigger_change_pct: float
    summary: str | None = None
    analysis: dict | None = None
    status: str
    sources: list[ReportSourceResponse] = []
    created_at: str | None = None
    completed_at: str | None = None


def _to_response(report: Report, stock: Stock, sources: list[ReportSource]) -> ReportResponse:
    return ReportResponse(
        id=str(report.id),
        stock_id=str(report.stock_id),
        stock_code=stock.code,
        stock_name=stock.name,
        trigger_change_pct=report.trigger_change_pct,
        summary=report.summary,
        analysis=report.analysis,
        status=report.status,
        sources=[
            ReportSourceResponse(
                id=str(s.id), source_type=s.source_type,
                title=s.title, url=s.url,
            )
            for s in sources
        ],
        created_at=str(report.created_at) if report.created_at else None,
        completed_at=str(report.completed_at) if report.completed_at else None,
    )


@router.get("", response_model=list[ReportResponse])
def list_reports(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """List reports for user's watchlist stocks, newest first."""
    watchlist_items = db.execute(
        select(Watchlist).where(Watchlist.user_id == user.id)
    ).scalars().all()

    stock_ids = [w.stock_id for w in watchlist_items]
    if not stock_ids:
        return []

    reports = db.execute(
        select(Report)
        .where(Report.stock_id.in_(stock_ids))
        .order_by(Report.created_at.desc())
    ).scalars().all()

    result = []
    for r in reports:
        stock = db.execute(select(Stock).where(Stock.id == r.stock_id)).scalar_one()
        sources = db.execute(
            select(ReportSource).where(ReportSource.report_id == r.id)
        ).scalars().all()
        result.append(_to_response(r, stock, sources))
    return result


@router.get("/{report_id}", response_model=ReportResponse)
def get_report(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get a single report by ID."""
    report = db.execute(
        select(Report).where(Report.id == uuid.UUID(report_id))
    ).scalar_one_or_none()

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")

    stock = db.execute(select(Stock).where(Stock.id == report.stock_id)).scalar_one()
    sources = db.execute(
        select(ReportSource).where(ReportSource.report_id == report.id)
    ).scalars().all()

    return _to_response(report, stock, sources)


@router.get("/stock/{stock_id}", response_model=list[ReportResponse])
def get_reports_by_stock(
    stock_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get all reports for a specific stock."""
    reports = db.execute(
        select(Report)
        .where(Report.stock_id == uuid.UUID(stock_id))
        .order_by(Report.created_at.desc())
    ).scalars().all()

    result = []
    for r in reports:
        stock = db.execute(select(Stock).where(Stock.id == r.stock_id)).scalar_one()
        sources = db.execute(
            select(ReportSource).where(ReportSource.report_id == r.id)
        ).scalars().all()
        result.append(_to_response(r, stock, sources))
    return result
