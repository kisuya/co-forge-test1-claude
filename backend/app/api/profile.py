from __future__ import annotations

import re
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.auth import hash_password, verify_password
from app.api.deps import get_current_user, get_db
from app.core.exceptions import raise_error
from app.core.sanitize import strip_html_tags
from app.models.report import Report
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist

router = APIRouter(prefix="/api/profile", tags=["profile"])

NICKNAME_PATTERN = re.compile(r"^[가-힣a-zA-Z0-9_]{2,20}$")


class StatsResponse(BaseModel):
    watchlist_count: int = 0
    report_count: int = 0
    discussion_count: int = 0


class ProfileResponse(BaseModel):
    email: str
    nickname: str | None = None
    display_name: str
    created_at: str
    stats: StatsResponse | None = None


class ProfileUpdateRequest(BaseModel):
    nickname: str | None = Field(None, max_length=20)


PASSWORD_PATTERN = re.compile(r"^(?=.*[a-zA-Z])(?=.*\d).{8,}$")


class PasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=100)
    new_password: str = Field(min_length=1, max_length=100)


def _get_display_name(user: User) -> str:
    """Return nickname if set, otherwise email prefix."""
    if user.nickname:
        return user.nickname
    return user.email.split("@")[0]


def _get_stats(user: User, db: Session) -> StatsResponse:
    """Compute user activity stats."""
    # Watchlist count
    watchlist_count = db.execute(
        select(func.count(Watchlist.id)).where(Watchlist.user_id == user.id)
    ).scalar_one()

    # Report count: completed reports for user's watchlist stocks
    stock_ids_subq = (
        select(Watchlist.stock_id).where(Watchlist.user_id == user.id).subquery()
    )
    report_count = db.execute(
        select(func.count(Report.id)).where(
            Report.stock_id.in_(select(stock_ids_subq)),
            Report.status == "completed",
        )
    ).scalar_one()

    # Discussion count: graceful if table doesn't exist
    discussion_count = 0
    try:
        from sqlalchemy import text
        row = db.execute(
            text("SELECT COUNT(*) FROM discussions WHERE user_id = :uid"),
            {"uid": str(user.id)},
        ).scalar_one()
        discussion_count = row
    except Exception:
        discussion_count = 0

    return StatsResponse(
        watchlist_count=watchlist_count,
        report_count=report_count,
        discussion_count=discussion_count,
    )


@router.get("", response_model=ProfileResponse)
def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get current user profile with activity stats."""
    stats = _get_stats(user, db)
    return ProfileResponse(
        email=user.email,
        nickname=user.nickname,
        display_name=_get_display_name(user),
        created_at=str(user.created_at),
        stats=stats,
    )


@router.put("", response_model=ProfileResponse)
def update_profile(
    body: ProfileUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update user profile (nickname)."""
    nickname = body.nickname

    # Allow null/empty to reset nickname
    if nickname is not None and nickname.strip() == "":
        nickname = None

    if nickname is not None:
        nickname = strip_html_tags(nickname)
        if not NICKNAME_PATTERN.match(nickname):
            raise_error(422, "닉네임은 2~20자, 한글/영문/숫자/밑줄만 가능합니다")

        # Check duplicate
        existing = db.execute(
            select(User).where(User.nickname == nickname, User.id != user.id)
        ).scalar_one_or_none()
        if existing is not None:
            raise_error(409, "이미 사용 중인 닉네임입니다")

    user.nickname = nickname
    db.commit()
    db.refresh(user)

    return ProfileResponse(
        email=user.email,
        nickname=user.nickname,
        display_name=_get_display_name(user),
        created_at=str(user.created_at),
    )


@router.put("/password")
def change_password(
    body: PasswordChangeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Change user password."""
    if not verify_password(body.current_password, user.password_hash):
        raise_error(400, "현재 비밀번호가 올바르지 않습니다")

    if not PASSWORD_PATTERN.match(body.new_password):
        raise_error(422, "비밀번호는 8자 이상, 영문과 숫자를 포함해야 합니다")

    user.password_hash = hash_password(body.new_password)
    db.commit()

    return {"message": "비밀번호가 변경되었습니다"}


@router.get("/reports")
def get_profile_reports(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get user's watchlist stock reports (paginated)."""
    stock_ids_subq = (
        select(Watchlist.stock_id).where(Watchlist.user_id == user.id).subquery()
    )

    base_query = select(Report).join(
        Stock, Report.stock_id == Stock.id
    ).where(
        Report.stock_id.in_(select(stock_ids_subq)),
        Report.status == "completed",
    )

    total = db.execute(
        select(func.count()).select_from(base_query.subquery())
    ).scalar_one()

    rows = db.execute(
        base_query.order_by(Report.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    ).scalars().all()

    items = []
    for r in rows:
        stock = db.execute(select(Stock).where(Stock.id == r.stock_id)).scalar_one_or_none()
        items.append({
            "id": str(r.id),
            "stock_id": str(r.stock_id),
            "stock_name": stock.name if stock else "Unknown",
            "change_pct": r.trigger_change_pct if r.trigger_change_pct else 0.0,
            "created_at": str(r.created_at) if r.created_at else "",
        })

    return {
        "items": items,
        "page": page,
        "per_page": per_page,
        "total": total,
        "has_more": page * per_page < total,
    }


@router.get("/discussions")
def get_profile_discussions(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Get user's discussions (paginated)."""
    try:
        from app.models.discussion import Discussion

        base_query = select(Discussion).where(Discussion.user_id == user.id)

        total = db.execute(
            select(func.count()).select_from(base_query.subquery())
        ).scalar_one()

        rows = db.execute(
            base_query.order_by(Discussion.created_at.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
        ).scalars().all()

        items = []
        for d in rows:
            stock = db.execute(select(Stock).where(Stock.id == d.stock_id)).scalar_one_or_none()
            items.append({
                "id": str(d.id),
                "stock_id": str(d.stock_id),
                "stock_name": stock.name if stock else "Unknown",
                "content": d.content[:200] if d.content else "",
                "created_at": str(d.created_at) if d.created_at else "",
            })

        return {
            "items": items,
            "page": page,
            "per_page": per_page,
            "total": total,
            "has_more": page * per_page < total,
        }
    except Exception:
        return {
            "items": [],
            "page": page,
            "per_page": per_page,
            "total": 0,
            "has_more": False,
        }
