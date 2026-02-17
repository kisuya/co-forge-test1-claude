"""Tests for Discussion and DiscussionComment models (community-001)."""
from __future__ import annotations

import uuid

import pytest
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.discussion import Discussion, DiscussionComment
from app.models.stock import Stock
from app.models.user import User
from app.api.auth import hash_password
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_discussion_model.db"


def _make_fk_engine():
    """Create engine with foreign key support for SQLite."""
    engine = create_engine("sqlite:///test_discussion_model.db")

    @event.listens_for(engine, "connect")
    def _set_fk(dbapi_conn, _rec):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


def _setup() -> None:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_stocks(session)
    session.close()


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os as _os
    if _os.path.exists("test_discussion_model.db"):
        _os.remove("test_discussion_model.db")


def _create_user(session, email="disc@example.com") -> User:
    user = User(email=email, password_hash=hash_password("pass1234"))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _get_stock(session) -> Stock:
    return session.execute(
        select(Stock).where(Stock.code == "005930")
    ).scalar_one()


def test_discussion_creation() -> None:
    """Discussion can be created with valid fields."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        user = _create_user(session)
        stock = _get_stock(session)

        discussion = Discussion(
            stock_id=stock.id,
            user_id=user.id,
            content="삼성전자 전망이 어떨까요?",
        )
        session.add(discussion)
        session.commit()
        session.refresh(discussion)

        assert discussion.id is not None
        assert discussion.stock_id == stock.id
        assert discussion.user_id == user.id
        assert discussion.content == "삼성전자 전망이 어떨까요?"
        assert discussion.created_at is not None
        session.close()
    finally:
        _teardown()


def test_discussion_comment_creation() -> None:
    """DiscussionComment can be created with valid fields."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        user = _create_user(session)
        stock = _get_stock(session)

        discussion = Discussion(
            stock_id=stock.id,
            user_id=user.id,
            content="토론 본문",
        )
        session.add(discussion)
        session.commit()

        comment = DiscussionComment(
            discussion_id=discussion.id,
            user_id=user.id,
            content="좋은 의견입니다!",
        )
        session.add(comment)
        session.commit()
        session.refresh(comment)

        assert comment.id is not None
        assert comment.discussion_id == discussion.id
        assert comment.content == "좋은 의견입니다!"
        assert comment.created_at is not None
        session.close()
    finally:
        _teardown()


def test_discussion_content_not_null() -> None:
    """Discussion content cannot be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        user = _create_user(session)
        stock = _get_stock(session)

        discussion = Discussion(
            stock_id=stock.id,
            user_id=user.id,
            content=None,
        )
        session.add(discussion)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_discussion_stock_fk() -> None:
    """Discussion requires valid stock_id FK."""
    _setup()
    try:
        engine = _make_fk_engine()
        Session = sessionmaker(bind=engine)
        session = Session()
        user = _create_user(session)

        discussion = Discussion(
            stock_id=uuid.uuid4(),  # nonexistent
            user_id=user.id,
            content="Invalid stock",
        )
        session.add(discussion)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
        engine.dispose()
    finally:
        _teardown()


def _setup_with_fk():
    """Create tables and return engine+session with FK support."""
    engine = _make_fk_engine()
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    seed_stocks(session)
    session.close()
    return engine


def test_discussion_cascade_delete_stock() -> None:
    """Deleting stock cascades to discussions."""
    engine = _setup_with_fk()
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        user = _create_user(session)
        stock = _get_stock(session)
        stock_id = stock.id

        discussion = Discussion(
            stock_id=stock_id,
            user_id=user.id,
            content="Will be deleted",
        )
        session.add(discussion)
        session.commit()
        disc_id = discussion.id
        session.close()

        # Use ORM table delete (raw SQL won't match UUID format in SQLite)
        session2 = Session()
        session2.execute(Stock.__table__.delete().where(Stock.id == stock_id))
        session2.commit()

        result = session2.execute(
            select(Discussion).where(Discussion.id == disc_id)
        ).scalar_one_or_none()
        assert result is None
        session2.close()
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        import os as _os
        if _os.path.exists("test_discussion_model.db"):
            _os.remove("test_discussion_model.db")


def test_comment_cascade_delete_discussion() -> None:
    """Deleting discussion cascades to comments."""
    engine = _setup_with_fk()
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        user = _create_user(session)
        stock = _get_stock(session)

        discussion = Discussion(
            stock_id=stock.id,
            user_id=user.id,
            content="Parent discussion",
        )
        session.add(discussion)
        session.commit()
        disc_id = discussion.id

        comment = DiscussionComment(
            discussion_id=disc_id,
            user_id=user.id,
            content="Child comment",
        )
        session.add(comment)
        session.commit()
        comment_id = comment.id
        session.close()

        session2 = Session()
        session2.execute(Discussion.__table__.delete().where(Discussion.id == disc_id))
        session2.commit()

        result = session2.execute(
            select(DiscussionComment).where(DiscussionComment.id == comment_id)
        ).scalar_one_or_none()
        assert result is None
        session2.close()
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        import os as _os
        if _os.path.exists("test_discussion_model.db"):
            _os.remove("test_discussion_model.db")


def test_discussion_user_cascade_delete() -> None:
    """Deleting user cascades to discussions."""
    engine = _setup_with_fk()
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        user = _create_user(session, email="cascade@example.com")
        user_id = user.id
        stock = _get_stock(session)

        discussion = Discussion(
            stock_id=stock.id,
            user_id=user_id,
            content="User cascade test",
        )
        session.add(discussion)
        session.commit()
        disc_id = discussion.id
        session.close()

        session2 = Session()
        session2.execute(User.__table__.delete().where(User.id == user_id))
        session2.commit()

        result = session2.execute(
            select(Discussion).where(Discussion.id == disc_id)
        ).scalar_one_or_none()
        assert result is None
        session2.close()
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        import os as _os
        if _os.path.exists("test_discussion_model.db"):
            _os.remove("test_discussion_model.db")
