"""Push subscription API endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import raise_error
from app.models.push_subscription import PushSubscription
from app.models.user import User

router = APIRouter(prefix="/api/push", tags=["push"])


class SubscribeRequest(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class SubscribeResponse(BaseModel):
    id: str
    endpoint: str
    is_active: bool


class StatusResponse(BaseModel):
    subscribed: bool
    endpoint_count: int


class UnsubscribeRequest(BaseModel):
    endpoint: str


@router.post("/subscribe", response_model=SubscribeResponse, status_code=status.HTTP_201_CREATED)
def subscribe(
    body: SubscribeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SubscribeResponse:
    """Register or update a push subscription (upsert by endpoint)."""
    existing = db.query(PushSubscription).filter(
        PushSubscription.endpoint == body.endpoint
    ).first()

    if existing:
        existing.p256dh = body.p256dh
        existing.auth = body.auth
        existing.user_id = user.id
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return SubscribeResponse(
            id=str(existing.id),
            endpoint=existing.endpoint,
            is_active=existing.is_active,
        )

    sub = PushSubscription(
        user_id=user.id,
        endpoint=body.endpoint,
        p256dh=body.p256dh,
        auth=body.auth,
        is_active=True,
    )
    db.add(sub)
    db.commit()
    db.refresh(sub)
    return SubscribeResponse(
        id=str(sub.id),
        endpoint=sub.endpoint,
        is_active=sub.is_active,
    )


@router.delete("/unsubscribe", status_code=status.HTTP_200_OK)
def unsubscribe(
    body: UnsubscribeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Deactivate a push subscription by endpoint."""
    sub = db.query(PushSubscription).filter(
        PushSubscription.endpoint == body.endpoint,
        PushSubscription.user_id == user.id,
    ).first()

    if not sub:
        raise_error(404, "Subscription not found")

    sub.is_active = False
    db.commit()
    return {"status": "unsubscribed"}


@router.get("/status", response_model=StatusResponse)
def push_status(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StatusResponse:
    """Return current user's push subscription status."""
    count = db.query(PushSubscription).filter(
        PushSubscription.user_id == user.id,
        PushSubscription.is_active == True,  # noqa: E712
    ).count()

    return StatusResponse(
        subscribed=count > 0,
        endpoint_count=count,
    )
