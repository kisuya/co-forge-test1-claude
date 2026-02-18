"""Pipeline monitoring and status API (pipe-005)."""
from __future__ import annotations

import json
import logging
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

PIPELINE_COLLECTORS = [
    {"name": "krx_prices", "task": "collect_krx_prices_task", "description": "KRX stock price collection"},
    {"name": "us_prices", "task": "collect_us_prices_task", "description": "US stock price collection"},
    {"name": "dart_disclosures", "task": "collect_dart_disclosures_task", "description": "DART disclosure collection"},
    {"name": "stock_news", "task": "collect_stock_news_task", "description": "Stock news collection"},
]

CONSECUTIVE_FAILURE_THRESHOLD = 3


def _get_pipeline_status_from_redis(collector_name: str) -> dict[str, Any] | None:
    """Read pipeline status from Redis."""
    try:
        from app.core.cache import get_redis_client
        client = get_redis_client()
        if client is None:
            return None
        raw = client.get(f"pipeline:{collector_name}:last_run")
        if raw is None:
            return None
        return json.loads(raw)
    except Exception:
        logger.warning("Failed to read pipeline status for %s from Redis", collector_name)
        return None


def _get_failure_count(collector_name: str) -> int:
    """Read consecutive failure count from Redis."""
    try:
        from app.core.cache import get_redis_client
        client = get_redis_client()
        if client is None:
            return 0
        raw = client.get(f"pipeline:{collector_name}:failure_count")
        return int(raw) if raw else 0
    except Exception:
        return 0


def get_all_pipeline_statuses() -> list[dict[str, Any]]:
    """Get status for all registered pipeline collectors."""
    results = []
    for collector in PIPELINE_COLLECTORS:
        name = collector["name"]
        status_data = _get_pipeline_status_from_redis(name)
        failure_count = _get_failure_count(name)

        entry: dict[str, Any] = {
            "name": name,
            "description": collector["description"],
            "task": collector["task"],
            "last_run_at": None,
            "status": "unknown",
            "items_collected": 0,
            "consecutive_failures": failure_count,
        }

        if status_data:
            entry["last_run_at"] = status_data.get("last_run_at")
            entry["status"] = status_data.get("status", "unknown")
            entry["items_collected"] = status_data.get("items_collected", 0)

        # Log escalation for consecutive failures
        if failure_count >= CONSECUTIVE_FAILURE_THRESHOLD:
            logger.error(
                "Pipeline '%s' has %d consecutive failures — requires attention",
                name, failure_count,
            )

        results.append(entry)

    return results


@router.get("/pipeline-status")
async def pipeline_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """Get status of all data collection pipelines.

    Requires authentication. Returns each collector's last run time,
    success/failure status, and items collected.
    """
    collectors = get_all_pipeline_statuses()
    return {"collectors": collectors}
