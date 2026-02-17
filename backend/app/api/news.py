from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.news_article import NewsArticle
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist

router = APIRouter(prefix="/api/news", tags=["news"])


class NewsResponse(BaseModel):
    id: int
    stock_id: str | None = None
    stock_name: str | None = None
    title: str
    url: str
    source: str
    summary: str | None = None
    importance: str | None = None
    published_at: str | None = None


class NewsFeedResponse(BaseModel):
    items: list[NewsResponse]
    page: int
    per_page: int
    total: int
    has_more: bool
    message: str | None = None


@router.get("", response_model=NewsFeedResponse)
def list_news(
    stock_id: str | None = Query(None),
    importance: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """List news articles for the user's watchlist stocks."""
    # Validate importance if provided
    if importance is not None and importance not in ("high", "medium", "low"):
        from app.core.exceptions import raise_error
        raise_error(422, "importance must be 'high', 'medium', or 'low'")

    # Get user's watchlist stock IDs
    watchlist_stock_ids = list(
        db.execute(
            select(Watchlist.stock_id).where(Watchlist.user_id == user.id)
        ).scalars().all()
    )

    # Build query
    query = select(NewsArticle)

    if stock_id is not None:
        try:
            sid = uuid.UUID(stock_id)
        except (ValueError, AttributeError):
            from app.core.exceptions import raise_error
            raise_error(422, "Invalid stock_id format")
        # Filter to specific stock (must be in user's watchlist)
        if sid not in watchlist_stock_ids:
            return NewsFeedResponse(
                items=[],
                page=page,
                per_page=per_page,
                total=0,
                has_more=False,
                message="뉴스가 없습니다",
            )
        query = query.where(NewsArticle.stock_id == sid)
    else:
        if not watchlist_stock_ids:
            return NewsFeedResponse(
                items=[],
                page=page,
                per_page=per_page,
                total=0,
                has_more=False,
                message="뉴스가 없습니다",
            )
        query = query.where(NewsArticle.stock_id.in_(watchlist_stock_ids))

    if importance is not None:
        query = query.where(NewsArticle.importance == importance)

    # Count total
    from sqlalchemy import func
    count_query = select(func.count()).select_from(query.subquery())
    total = db.execute(count_query).scalar() or 0

    # Paginate
    offset = (page - 1) * per_page
    articles = list(
        db.execute(
            query.order_by(NewsArticle.published_at.desc().nullslast())
            .offset(offset)
            .limit(per_page)
        ).scalars().all()
    )

    # Build stock name map
    stock_ids_in_result = {a.stock_id for a in articles if a.stock_id}
    stock_map: dict[uuid.UUID, str] = {}
    if stock_ids_in_result:
        stocks = db.execute(
            select(Stock).where(Stock.id.in_(stock_ids_in_result))
        ).scalars().all()
        stock_map = {s.id: s.name for s in stocks}

    items = []
    for article in articles:
        items.append(NewsResponse(
            id=article.id,
            stock_id=str(article.stock_id) if article.stock_id else None,
            stock_name=stock_map.get(article.stock_id) if article.stock_id else None,
            title=article.title,
            url=article.url,
            source=article.source,
            summary=article.content_summary,
            importance=article.importance,
            published_at=str(article.published_at) if article.published_at else None,
        ))

    has_more = (offset + per_page) < total

    return NewsFeedResponse(
        items=items,
        page=page,
        per_page=per_page,
        total=total,
        has_more=has_more,
        message="뉴스가 없습니다" if not items else None,
    )
