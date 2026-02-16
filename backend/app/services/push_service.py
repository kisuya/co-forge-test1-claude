"""Push notification service for spike alerts."""
from __future__ import annotations

import json
import logging
import time
import uuid as uuid_mod
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.push_subscription import PushSubscription
from app.models.stock import Stock
from app.models.watchlist import Watchlist

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
BACKOFF_BASE = 1  # seconds: 1, 2, 4


@dataclass
class PushResult:
    """Result of sending push notifications for a spike event."""

    success: int = 0
    failed: int = 0
    expired: int = 0


def _build_payload(stock_name: str, stock_code: str, change_pct: float, stock_id: str) -> str:
    """Build the push notification JSON payload."""
    sign = "+" if change_pct > 0 else ""
    icon = "\U0001F4C8" if change_pct > 0 else "\U0001F4C9"
    return json.dumps({
        "title": f"{icon} {stock_name} {sign}{change_pct:.1f}%",
        "body": "급변동이 감지되었습니다. 탭하여 리포트를 확인하세요",
        "url": f"/reports/stock/{stock_id}",
    })


def _send_single(sub: PushSubscription, payload: str, send_fn: object | None = None) -> str:
    """Send push to a single subscription. Returns 'ok', 'failed', or 'expired'."""
    for attempt in range(MAX_RETRIES):
        try:
            if send_fn is not None:
                send_fn(sub, payload)  # type: ignore[operator]
            else:
                from pywebpush import webpush, WebPushException
                from app.config import get_settings
                settings = get_settings()
                webpush(
                    subscription_info={
                        "endpoint": sub.endpoint,
                        "keys": {"p256dh": sub.p256dh, "auth": sub.auth},
                    },
                    data=payload,
                    vapid_private_key=settings.vapid_private_key,
                    vapid_claims={"sub": settings.vapid_contact},
                )
            return "ok"
        except Exception as exc:
            status_code = getattr(exc, "response", None)
            if hasattr(status_code, "status_code"):
                status_code = status_code.status_code
            elif hasattr(exc, "errno"):
                status_code = getattr(exc, "errno", None)
            else:
                status_code = None

            if status_code == 410:
                return "expired"

            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_BASE * (2 ** attempt))
            else:
                logger.warning("Push failed after %d retries: %s", MAX_RETRIES, exc)
                return "failed"
    return "failed"


def send_spike_notifications(
    db: Session,
    stock_id: str,
    change_pct: float,
    send_fn: object | None = None,
) -> PushResult:
    """Send push notifications for a spike event on a stock.

    Finds all users watching this stock who have active push subscriptions
    and sends notifications.
    """
    sid = uuid_mod.UUID(stock_id) if isinstance(stock_id, str) else stock_id

    stock = db.execute(
        select(Stock).where(Stock.id == sid)
    ).scalar_one_or_none()

    if stock is None:
        return PushResult()

    wl_user_ids = db.execute(
        select(Watchlist.user_id).where(Watchlist.stock_id == sid)
    ).scalars().all()

    if not wl_user_ids:
        return PushResult()

    subs = db.execute(
        select(PushSubscription).where(
            PushSubscription.user_id.in_(wl_user_ids),
            PushSubscription.is_active == True,  # noqa: E712
        )
    ).scalars().all()

    if not subs:
        return PushResult()

    payload = _build_payload(stock.name, stock.code, change_pct, str(stock.id))
    result = PushResult()

    for sub in subs:
        status = _send_single(sub, payload, send_fn)
        if status == "ok":
            result.success += 1
        elif status == "expired":
            result.expired += 1
            sub.is_active = False
        else:
            result.failed += 1

    db.commit()

    logger.info(
        "Push for %s: %d success, %d failed, %d expired",
        stock.code, result.success, result.failed, result.expired,
    )
    return result
