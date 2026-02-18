"""API endpoint for similar historical case data."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import raise_error
from app.models.report import Report
from app.models.user import User
from app.services.similar_case_service import get_cases_with_trends

router = APIRouter(prefix="/api/cases", tags=["cases"])


class TrendPointResponse(BaseModel):
    day: int
    change_pct: float


class AftermathResponse(BaseModel):
    after_1w_pct: float | None = None
    after_1m_pct: float | None = None
    recovery_days: int | None = None


class CaseResponse(BaseModel):
    date: str
    change_pct: float
    volume: int
    similarity_score: float
    trend_1w: list[TrendPointResponse]
    trend_1m: list[TrendPointResponse]
    data_insufficient: bool
    aftermath: AftermathResponse | None = None


class CasesResponse(BaseModel):
    cases: list[CaseResponse]
    message: str | None = None


@router.get("/{report_id}", response_model=CasesResponse)
def get_cases(
    report_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get similar historical cases for a report."""
    try:
        parsed_id = uuid.UUID(report_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid report ID format")

    report = db.execute(
        select(Report).where(Report.id == parsed_id)
    ).scalar_one_or_none()

    if report is None:
        raise_error(404, "Report not found")

    cases = get_cases_with_trends(
        db,
        str(report.stock_id),
        report.trigger_change_pct,
        exclude_date=report.created_at,
    )

    if not cases:
        return CasesResponse(
            cases=[],
            message="유사한 과거 사례를 찾지 못했습니다",
        )

    return CasesResponse(
        cases=[
            CaseResponse(
                date=str(c.date),
                change_pct=c.change_pct,
                volume=c.volume,
                similarity_score=c.similarity_score,
                trend_1w=[
                    TrendPointResponse(day=t.day, change_pct=t.change_pct)
                    for t in c.trend_1w
                ],
                trend_1m=[
                    TrendPointResponse(day=t.day, change_pct=t.change_pct)
                    for t in c.trend_1m
                ],
                data_insufficient=c.data_insufficient,
                aftermath=AftermathResponse(
                    after_1w_pct=c.aftermath.after_1w_pct,
                    after_1m_pct=c.aftermath.after_1m_pct,
                    recovery_days=c.aftermath.recovery_days,
                ) if c.aftermath else None,
            )
            for c in cases
        ],
    )
