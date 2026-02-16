"""Celery task for sending push notifications on price spikes."""
from __future__ import annotations

import logging

from app.db.database import get_session_factory
from app.config import get_settings
from app.services.push_service import send_spike_notifications
from app.workers.celery_app import celery

logger = logging.getLogger(__name__)


@celery.task(name="send_spike_push", bind=True, max_retries=0)
def send_spike_push(self: object, stock_id: str, change_pct: float) -> dict[str, int]:
    """Celery task: send push notifications for a stock price spike.

    Args:
        stock_id: UUID of the stock that spiked.
        change_pct: The percentage change that triggered the alert.

    Returns:
        Dict with success/failed/expired counts.
    """
    settings = get_settings()
    factory = get_session_factory(settings.database_url)
    session = factory()
    try:
        result = send_spike_notifications(session, stock_id, change_pct)
        return {
            "success": result.success,
            "failed": result.failed,
            "expired": result.expired,
        }
    finally:
        session.close()
