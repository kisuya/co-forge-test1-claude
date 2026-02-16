from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.llm_client import AnalysisResult, analyze_stock_movement
from app.models.report import Report, ReportSource
from app.models.stock import Stock
from app.services.similar_case_service import get_cases_with_trends

US_MARKETS = ("NYSE", "NASDAQ")


def _is_us_stock(stock: Stock) -> bool:
    """Check if a stock is from a US market."""
    return stock.market in US_MARKETS


def run_analysis(
    db: Session,
    report: Report,
    analyze_fn: object | None = None,
) -> AnalysisResult:
    """Run LLM analysis on a report's collected sources.

    For US stocks, adds US market context (FOMC, CPI, pre/after market,
    exchange rate). Output is always in Korean.

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

    is_us = _is_us_stock(stock)
    has_no_sources = len(sources) == 0

    report.summary = result.summary
    analysis_data: dict = {
        "market": stock.market,
        "causes": [
            {
                "reason": c.reason,
                "confidence": c.confidence,
                "impact": c.impact,
            }
            for c in result.causes
        ],
    }

    if has_no_sources:
        analysis_data["note"] = "관련 뉴스를 찾지 못했습니다"

    cases = get_cases_with_trends(
        db, str(report.stock_id), report.trigger_change_pct,
        exclude_date=report.created_at,
    )
    analysis_data["similar_cases"] = [
        {
            "date": str(c.date),
            "change_pct": c.change_pct,
            "trend_1w": [{"day": t.day, "change_pct": t.change_pct} for t in c.trend_1w],
            "trend_1m": [{"day": t.day, "change_pct": t.change_pct} for t in c.trend_1m],
            "similarity_score": c.similarity_score,
        }
        for c in cases
    ]

    report.analysis = analysis_data
    report.status = "completed"
    db.commit()

    return result
