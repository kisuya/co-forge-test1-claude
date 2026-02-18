from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.llm_client import MultiLayerAnalysisResult, analyze_stock_movement
from app.models.report import Report, ReportSource
from app.models.stock import Stock
from app.services.sector_service import get_sector_impact
from app.services.similar_case_service import get_cases_with_trends

US_MARKETS = ("NYSE", "NASDAQ")


def _is_us_stock(stock: Stock) -> bool:
    """Check if a stock is from a US market."""
    return stock.market in US_MARKETS


def _cause_to_dict(c) -> dict:
    """Convert a cause object to dict, including impact_level if present."""
    d = {
        "reason": c.reason,
        "confidence": c.confidence,
        "impact": c.impact,
    }
    if hasattr(c, "impact_level"):
        d["impact_level"] = c.impact_level
    return d


def run_analysis(
    db: Session,
    report: Report,
    analyze_fn: object | None = None,
) -> MultiLayerAnalysisResult:
    """Run LLM analysis on a report's collected sources.

    For US stocks, adds US market context (FOMC, CPI, pre/after market,
    exchange rate). Output is always in Korean.

    Args:
        db: Database session.
        report: Report with collected sources.
        analyze_fn: Optional override for LLM analysis (for testing).

    Returns:
        MultiLayerAnalysisResult with structured analysis.
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
        result: MultiLayerAnalysisResult = analyze_fn(
            stock.name, stock.code,
            report.trigger_change_pct, source_dicts,
        )
    else:
        result = analyze_stock_movement(
            stock.name, stock.code,
            report.trigger_change_pct, source_dicts,
        )

    has_no_sources = len(sources) == 0

    report.summary = result.summary

    # Build multi-layer analysis data
    analysis_data: dict = {
        "market": stock.market,
        # Backward-compatible flat causes list
        "causes": [_cause_to_dict(c) for c in result.causes],
    }

    # Add multi-layer structure if available
    if hasattr(result, "direct_causes"):
        analysis_data["direct_causes"] = [
            _cause_to_dict(c) for c in result.direct_causes
        ]
        analysis_data["indirect_causes"] = [
            _cause_to_dict(c) for c in result.indirect_causes
        ]
        analysis_data["macro_factors"] = [
            _cause_to_dict(c) for c in result.macro_factors
        ]

    # Add outlook if available
    if hasattr(result, "short_term_outlook") and result.short_term_outlook:
        o = result.short_term_outlook
        analysis_data["outlook"] = analysis_data.get("outlook", {})
        analysis_data["outlook"]["short_term"] = {
            "summary": o.summary,
            "sentiment": o.sentiment,
            "catalysts": o.catalysts,
        }
    if hasattr(result, "medium_term_outlook") and result.medium_term_outlook:
        o = result.medium_term_outlook
        analysis_data["outlook"] = analysis_data.get("outlook", {})
        analysis_data["outlook"]["medium_term"] = {
            "summary": o.summary,
            "sentiment": o.sentiment,
            "catalysts": o.catalysts,
        }

    # Add sector impact if available
    sector_impact = get_sector_impact(db, str(report.stock_id))
    if sector_impact:
        analysis_data["sector_impact"] = {
            "sector": sector_impact.sector,
            "related_stocks": [
                {
                    "name": rs.name,
                    "code": rs.code,
                    "change_pct": rs.change_pct,
                }
                for rs in sector_impact.related_stocks
            ],
            "correlation_note": sector_impact.correlation_note,
        }

    if has_no_sources:
        analysis_data["note"] = "관련 뉴스를 찾지 못했습니다"

    cases = get_cases_with_trends(
        db, str(report.stock_id), report.trigger_change_pct,
        exclude_date=report.created_at,
    )
    analysis_data["similar_cases"] = []
    for c in cases:
        case_data: dict = {
            "date": str(c.date),
            "change_pct": c.change_pct,
            "trend_1w": [{"day": t.day, "change_pct": t.change_pct} for t in c.trend_1w],
            "trend_1m": [{"day": t.day, "change_pct": t.change_pct} for t in c.trend_1m],
            "similarity_score": c.similarity_score,
        }
        if c.aftermath:
            case_data["aftermath"] = {
                "after_1w_pct": c.aftermath.after_1w_pct,
                "after_1m_pct": c.aftermath.after_1m_pct,
                "recovery_days": c.aftermath.recovery_days,
            }
        analysis_data["similar_cases"].append(case_data)

    report.analysis = analysis_data
    report.status = "completed"
    db.commit()

    return result
