from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.llm_client import AnalysisResult
from app.models.report import Report
from app.services.analysis_service import run_analysis
from app.services.price_detection import detect_price_spikes
from app.workers.news_collector import collect_news_for_report


def generate_reports(
    db: Session,
    disclosure_fn: object | None = None,
    news_fn: object | None = None,
    analyze_fn: object | None = None,
) -> list[Report]:
    """Full pipeline: detect spikes -> collect news -> analyze -> complete.

    Returns list of completed reports.
    """
    # Step 1: Detect price spikes (creates pending reports)
    new_reports = detect_price_spikes(db)

    # Step 2 & 3: For each pending report, collect news and analyze
    pending = db.execute(
        select(Report).where(Report.status == "pending")
    ).scalars().all()

    completed: list[Report] = []
    for report in pending:
        try:
            report.status = "generating"
            db.commit()

            # Step 2: Collect news and disclosures
            collect_news_for_report(
                db, report,
                disclosure_fn=disclosure_fn,
                news_fn=news_fn,
            )

            # Step 3: Run LLM analysis
            run_analysis(db, report, analyze_fn=analyze_fn)

            report.completed_at = datetime.now(timezone.utc)
            db.commit()
            completed.append(report)

        except Exception:
            report.status = "failed"
            db.commit()

    return completed
