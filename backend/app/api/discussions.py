"""Discussion CRUD API (community-002) and Comment API (community-003)."""
from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import raise_error
from app.core.sanitize import strip_html_tags
from app.models.discussion import Discussion, DiscussionComment
from app.models.stock import Stock
from app.models.user import User

router = APIRouter(tags=["discussions"])

MAX_COMMENT_PER_DISCUSSION = 100


def _get_display_name(user: User) -> str:
    """Return nickname if set, otherwise email prefix."""
    if user.nickname:
        return user.nickname
    return user.email.split("@")[0]


# --------------- Pydantic schemas ---------------

class DiscussionCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class DiscussionUpdateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=2000)


class DiscussionResponse(BaseModel):
    id: str
    content: str
    author_name: str
    comment_count: int = 0
    created_at: str
    updated_at: str | None = None
    is_mine: bool = False


class DiscussionPaginationResponse(BaseModel):
    page: int
    per_page: int
    total: int
    has_more: bool


class DiscussionListResponse(BaseModel):
    discussions: list[DiscussionResponse]
    pagination: DiscussionPaginationResponse


class CommentCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class CommentResponse(BaseModel):
    id: str
    content: str
    author_name: str
    created_at: str
    is_mine: bool = False


# --------------- Discussion CRUD ---------------

@router.post(
    "/api/stocks/{stock_id}/discussions",
    response_model=DiscussionResponse,
    status_code=201,
)
def create_discussion(
    stock_id: str,
    body: DiscussionCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Create a discussion for a stock."""
    try:
        stock_uuid = uuid.UUID(stock_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid stock ID format")

    stock = db.execute(
        select(Stock).where(Stock.id == stock_uuid)
    ).scalar_one_or_none()
    if stock is None:
        raise_error(404, "Stock not found")

    content = strip_html_tags(body.content)
    if len(content) == 0:
        raise_error(422, "Content cannot be empty after sanitization")

    discussion = Discussion(
        stock_id=stock_uuid,
        user_id=user.id,
        content=content,
    )
    db.add(discussion)
    db.commit()
    db.refresh(discussion)

    return DiscussionResponse(
        id=str(discussion.id),
        content=discussion.content,
        author_name=_get_display_name(user),
        comment_count=0,
        created_at=str(discussion.created_at),
        updated_at=str(discussion.updated_at) if discussion.updated_at else None,
        is_mine=True,
    )


@router.get(
    "/api/stocks/{stock_id}/discussions",
    response_model=DiscussionListResponse,
)
def list_discussions(
    stock_id: str,
    page: int = Query(1, ge=1, le=1000),
    per_page: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """List discussions for a stock, newest first."""
    try:
        stock_uuid = uuid.UUID(stock_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid stock ID format")

    stock = db.execute(
        select(Stock).where(Stock.id == stock_uuid)
    ).scalar_one_or_none()
    if stock is None:
        raise_error(404, "Stock not found")

    total = db.execute(
        select(func.count(Discussion.id)).where(Discussion.stock_id == stock_uuid)
    ).scalar_one()

    offset = (page - 1) * per_page
    discussions = db.execute(
        select(Discussion)
        .where(Discussion.stock_id == stock_uuid)
        .order_by(Discussion.created_at.desc())
        .offset(offset)
        .limit(per_page)
    ).scalars().all()

    items = []
    for d in discussions:
        comment_count = db.execute(
            select(func.count(DiscussionComment.id))
            .where(DiscussionComment.discussion_id == d.id)
        ).scalar_one()

        # Load user for display name
        d_user = db.execute(
            select(User).where(User.id == d.user_id)
        ).scalar_one_or_none()

        author_name = _get_display_name(d_user) if d_user else "unknown"

        items.append(DiscussionResponse(
            id=str(d.id),
            content=d.content,
            author_name=author_name,
            comment_count=comment_count,
            created_at=str(d.created_at),
            updated_at=str(d.updated_at) if d.updated_at else None,
            is_mine=(d.user_id == user.id),
        ))

    has_more = (offset + per_page) < total
    return DiscussionListResponse(
        discussions=items,
        pagination=DiscussionPaginationResponse(
            page=page, per_page=per_page, total=total, has_more=has_more,
        ),
    )


@router.put(
    "/api/discussions/{discussion_id}",
    response_model=DiscussionResponse,
)
def update_discussion(
    discussion_id: str,
    body: DiscussionUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Update a discussion. Only the author can update."""
    try:
        disc_uuid = uuid.UUID(discussion_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid discussion ID format")

    discussion = db.execute(
        select(Discussion).where(Discussion.id == disc_uuid)
    ).scalar_one_or_none()
    if discussion is None:
        raise_error(404, "Discussion not found")

    if discussion.user_id != user.id:
        raise_error(403, "You can only edit your own discussions")

    content = strip_html_tags(body.content)
    if len(content) == 0:
        raise_error(422, "Content cannot be empty after sanitization")

    discussion.content = content
    db.commit()
    db.refresh(discussion)

    comment_count = db.execute(
        select(func.count(DiscussionComment.id))
        .where(DiscussionComment.discussion_id == discussion.id)
    ).scalar_one()

    return DiscussionResponse(
        id=str(discussion.id),
        content=discussion.content,
        author_name=_get_display_name(user),
        comment_count=comment_count,
        created_at=str(discussion.created_at),
        updated_at=str(discussion.updated_at) if discussion.updated_at else None,
        is_mine=True,
    )


@router.delete("/api/discussions/{discussion_id}", status_code=204, response_class=Response)
def delete_discussion(
    discussion_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a discussion. Only the author can delete. Cascades to comments."""
    try:
        disc_uuid = uuid.UUID(discussion_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid discussion ID format")

    discussion = db.execute(
        select(Discussion).where(Discussion.id == disc_uuid)
    ).scalar_one_or_none()
    if discussion is None:
        raise_error(404, "Discussion not found")

    if discussion.user_id != user.id:
        raise_error(403, "You can only delete your own discussions")

    db.delete(discussion)
    db.commit()
    return Response(status_code=204)


# --------------- Comment CRUD ---------------

@router.post(
    "/api/discussions/{discussion_id}/comments",
    response_model=CommentResponse,
    status_code=201,
)
def create_comment(
    discussion_id: str,
    body: CommentCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """Create a comment on a discussion."""
    try:
        disc_uuid = uuid.UUID(discussion_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid discussion ID format")

    discussion = db.execute(
        select(Discussion).where(Discussion.id == disc_uuid)
    ).scalar_one_or_none()
    if discussion is None:
        raise_error(404, "Discussion not found")

    # Check comment limit
    current_count = db.execute(
        select(func.count(DiscussionComment.id))
        .where(DiscussionComment.discussion_id == disc_uuid)
    ).scalar_one()
    if current_count >= MAX_COMMENT_PER_DISCUSSION:
        raise_error(400, "Maximum comment limit reached")

    content = strip_html_tags(body.content)
    if len(content) == 0:
        raise_error(422, "Content cannot be empty after sanitization")

    comment = DiscussionComment(
        discussion_id=disc_uuid,
        user_id=user.id,
        content=content,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return CommentResponse(
        id=str(comment.id),
        content=comment.content,
        author_name=_get_display_name(user),
        created_at=str(comment.created_at),
        is_mine=True,
    )


@router.get(
    "/api/discussions/{discussion_id}/comments",
    response_model=list[CommentResponse],
)
def list_comments(
    discussion_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Any:
    """List comments for a discussion, oldest first."""
    try:
        disc_uuid = uuid.UUID(discussion_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid discussion ID format")

    discussion = db.execute(
        select(Discussion).where(Discussion.id == disc_uuid)
    ).scalar_one_or_none()
    if discussion is None:
        raise_error(404, "Discussion not found")

    comments = db.execute(
        select(DiscussionComment)
        .where(DiscussionComment.discussion_id == disc_uuid)
        .order_by(DiscussionComment.created_at.asc())
    ).scalars().all()

    result = []
    for c in comments:
        c_user = db.execute(
            select(User).where(User.id == c.user_id)
        ).scalar_one_or_none()
        author_name = _get_display_name(c_user) if c_user else "unknown"
        result.append(CommentResponse(
            id=str(c.id),
            content=c.content,
            author_name=author_name,
            created_at=str(c.created_at),
            is_mine=(c.user_id == user.id),
        ))

    return result


@router.delete("/api/comments/{comment_id}", status_code=204, response_class=Response)
def delete_comment(
    comment_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Response:
    """Delete a comment. Only the author can delete."""
    try:
        comment_uuid = uuid.UUID(comment_id)
    except (ValueError, AttributeError):
        raise_error(422, "Invalid comment ID format")

    comment = db.execute(
        select(DiscussionComment).where(DiscussionComment.id == comment_uuid)
    ).scalar_one_or_none()
    if comment is None:
        raise_error(404, "Comment not found")

    if comment.user_id != user.id:
        raise_error(403, "You can only delete your own comments")

    db.delete(comment)
    db.commit()
    return Response(status_code=204)
