"""End-to-end pipeline: price collection → spike detection → news → analysis → notify.

Orchestrates the full pipeline as a Celery chain with error isolation.
Each step runs independently; a failure in one step does not block subsequent steps.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """Result of a full pipeline run."""
    prices_collected: int = 0
    spikes_detected: int = 0
    news_collected: int = 0
    reports_completed: int = 0
    notifications_sent: int = 0
    errors: list[str] = field(default_factory=list)
    duration_ms: int = 0


def run_pipeline(
    db: Session,
    *,
    collect_prices_fn: object | None = None,
    detect_spikes_fn: object | None = None,
    collect_news_fn: object | None = None,
    run_analysis_fn: object | None = None,
    send_notifications_fn: object | None = None,
) -> PipelineResult:
    """Run the full spike detection → report generation pipeline.

    Each stage is isolated: failures are caught and logged,
    and the pipeline continues to the next stage.

    Args:
        db: Database session.
        collect_prices_fn: Override for price collection step.
        detect_spikes_fn: Override for spike detection step.
        collect_news_fn: Override for news collection step.
        run_analysis_fn: Override for analysis step.
        send_notifications_fn: Override for notification step.

    Returns:
        PipelineResult with counts and error details.
    """
    result = PipelineResult()
    start = time.monotonic()

    # Step 1: Collect prices
    try:
        if collect_prices_fn is not None:
            result.prices_collected = collect_prices_fn(db)
        else:
            from app.workers.price_collector import collect_prices
            result.prices_collected = collect_prices(db)
        logger.info("Pipeline step 1/5: collected %d prices", result.prices_collected)
    except Exception as exc:
        msg = f"collect_prices failed: {exc}"
        logger.error("Pipeline step 1/5 error: %s", msg)
        result.errors.append(msg)

    # Step 2: Detect spikes
    pending_reports = []
    try:
        if detect_spikes_fn is not None:
            pending_reports = detect_spikes_fn(db)
        else:
            from app.services.price_detection import detect_price_spikes
            pending_reports = detect_price_spikes(db)
        result.spikes_detected = len(pending_reports)
        logger.info("Pipeline step 2/5: detected %d spikes", result.spikes_detected)
    except Exception as exc:
        msg = f"detect_spikes failed: {exc}"
        logger.error("Pipeline step 2/5 error: %s", msg)
        result.errors.append(msg)

    # Step 3: Collect news for stocks with spikes
    try:
        if collect_news_fn is not None:
            news = collect_news_fn(db)
        else:
            from app.workers.stock_news_collector import collect_stock_news
            news = collect_stock_news(db)
        result.news_collected = len(news) if news else 0
        logger.info("Pipeline step 3/5: collected %d news articles", result.news_collected)
    except Exception as exc:
        msg = f"collect_news failed: {exc}"
        logger.error("Pipeline step 3/5 error: %s", msg)
        result.errors.append(msg)

    # Step 4: Run analysis for each pending report
    for report in pending_reports:
        try:
            if run_analysis_fn is not None:
                run_analysis_fn(db, report)
            else:
                from app.services.analysis_service import run_analysis
                run_analysis(db, report)
            if report.status == "completed":
                result.reports_completed += 1
                logger.info(
                    "Pipeline step 4/5: completed report %s", report.id,
                )
            else:
                logger.warning(
                    "Pipeline step 4/5: report %s not completed (status=%s)",
                    report.id, report.status,
                )
        except Exception as exc:
            msg = f"analysis failed for report {report.id}: {exc}"
            logger.error("Pipeline step 4/5 error: %s", msg)
            result.errors.append(msg)

    # Step 5: Send push notifications for completed reports
    for report in pending_reports:
        if report.status != "completed":
            continue
        try:
            if send_notifications_fn is not None:
                push_result = send_notifications_fn(db, str(report.stock_id), report.trigger_change_pct)
            else:
                from app.services.push_service import send_spike_notifications
                push_result = send_spike_notifications(
                    db, str(report.stock_id), report.trigger_change_pct,
                )
            result.notifications_sent += getattr(push_result, "success", 0)
        except Exception as exc:
            msg = f"notifications failed for report {report.id}: {exc}"
            logger.error("Pipeline step 5/5 error: %s", msg)
            result.errors.append(msg)

    elapsed = time.monotonic() - start
    result.duration_ms = int(elapsed * 1000)
    logger.info(
        "Pipeline complete in %dms: %d prices, %d spikes, %d news, %d reports, %d notifs, %d errors",
        result.duration_ms,
        result.prices_collected,
        result.spikes_detected,
        result.news_collected,
        result.reports_completed,
        result.notifications_sent,
        len(result.errors),
    )
    return result


# Celery task — guarded behind try/except for environments without celery
try:
    from app.workers.celery_app import celery
    from app.config import get_settings
    from app.db.database import get_session_factory

    @celery.task(name="run_e2e_pipeline_task", bind=True, max_retries=0)
    def run_e2e_pipeline_task(self: object) -> dict:
        """Celery task: run the full e2e pipeline."""
        settings = get_settings()
        factory = get_session_factory(settings.database_url)
        session = factory()
        try:
            result = run_pipeline(session)
            return {
                "status": "ok" if not result.errors else "partial",
                "prices_collected": result.prices_collected,
                "spikes_detected": result.spikes_detected,
                "news_collected": result.news_collected,
                "reports_completed": result.reports_completed,
                "notifications_sent": result.notifications_sent,
                "errors": result.errors,
                "duration_ms": result.duration_ms,
            }
        except Exception as exc:
            logger.exception("e2e pipeline task failed: %s", exc)
            return {"status": "error", "error": str(exc)}
        finally:
            session.close()

except ImportError:
    run_e2e_pipeline_task = None  # type: ignore[assignment]
