from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.llm_client import AnalysisResult, analyze_stock_movement
from app.models.report import Report, ReportSource
from app.models.stock import Stock


def run_analysis(
    db: Session,
    report: Report,
    analyze_fn: object | None = None,
) -> AnalysisResult:
    """Run LLM analysis on a report's collected sources.

    Args:
        db: Database session.
        report: Report with collected sources.
        analyze_fn: Optional override for LLM analysis (for testing).

    Returns:
        AnalysisResult with structured analysis.
    """
    stock = db.execute(
        select(Stock).where(Stock.id == report.stock_id)
    ).scalar_one()

    sources = db.execute(
        select(ReportSource).where(ReportSource.report_id == report.id)
    ).scalars().all()

    source_dicts = [
        {"type": s.source_type, "title": s.title, "url": s.url}
        for s in sources
    ]

    if analyze_fn is not None:
        result: AnalysisResult = analyze_fn(
            stock.name, stock.code,
            report.trigger_change_pct, source_dicts,
        )
    else:
        result = analyze_stock_movement(
            stock.name, stock.code,
            report.trigger_change_pct, source_dicts,
        )

    report.summary = result.summary
    report.analysis = {
        "causes": [
            {
                "reason": c.reason,
                "confidence": c.confidence,
                "impact": c.impact,
            }
            for c in result.causes
        ],
    }
    report.status = "completed"
    db.commit()

    return result
