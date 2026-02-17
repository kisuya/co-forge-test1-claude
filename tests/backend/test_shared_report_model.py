"""Tests for SharedReport model (share-001)."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import Report
from app.models.shared_report import SharedReport
from app.models.stock import Stock
from app.models.user import User
from app.services.stock_service import seed_stocks

TEST_DB_URL = "sqlite:///test_shared_report_model.db"


def _make_fk_engine():
    """Create engine with foreign key support for SQLite."""
    engine = create_engine("sqlite:///test_shared_report_model.db")

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
    if _os.path.exists("test_shared_report_model.db"):
        _os.remove("test_shared_report_model.db")


def _create_user(session: Session, email: str = "share@example.com") -> uuid.UUID:
    import bcrypt
    user = User(
        email=email,
        password_hash=bcrypt.hashpw(b"pass1234", bcrypt.gensalt()).decode(),
    )
    session.add(user)
    session.commit()
    return user.id


def _create_report(session: Session, stock_id: uuid.UUID) -> uuid.UUID:
    report = Report(
        stock_id=stock_id,
        trigger_price=Decimal("50000"),
        trigger_change_pct=5.0,
        status="completed",
        summary="Test report",
    )
    session.add(report)
    session.commit()
    return report.id


def _get_stock_id(session: Session) -> uuid.UUID:
    stock = session.execute(
        select(Stock).where(Stock.code == "005930")
    ).scalar_one()
    return stock.id


def test_shared_report_creation() -> None:
    """SharedReport can be created with required fields."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        stock_id = _get_stock_id(session)
        user_id = _create_user(session)
        report_id = _create_report(session, stock_id)

        shared = SharedReport(
            report_id=report_id,
            created_by=user_id,
        )
        session.add(shared)
        session.commit()

        assert shared.id is not None
        assert shared.share_token is not None
        assert len(shared.share_token) == 36  # UUID format
        assert shared.expires_at is not None
        # Expires roughly 30 days from now (handle timezone-naive from SQLite)
        now = datetime.now(timezone.utc)
        expires = shared.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        diff = expires - now
        assert 29 <= diff.days <= 30

        session.close()
    finally:
        _teardown()


def test_shared_report_unique_token() -> None:
    """share_token must be unique."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        stock_id = _get_stock_id(session)
        user_id = _create_user(session)
        report_id = _create_report(session, stock_id)

        token = str(uuid.uuid4())
        s1 = SharedReport(
            report_id=report_id,
            created_by=user_id,
            share_token=token,
        )
        session.add(s1)
        session.commit()

        s2 = SharedReport(
            report_id=report_id,
            created_by=user_id,
            share_token=token,  # duplicate
        )
        session.add(s2)
        with pytest.raises(IntegrityError):
            session.commit()

        session.close()
    finally:
        _teardown()


def test_shared_report_not_null_report_id() -> None:
    """report_id is required (NOT NULL)."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        user_id = _create_user(session)

        shared = SharedReport(
            report_id=None,  # type: ignore[arg-type]
            created_by=user_id,
        )
        session.add(shared)
        with pytest.raises(IntegrityError):
            session.commit()

        session.close()
    finally:
        _teardown()


def test_shared_report_not_null_created_by() -> None:
    """created_by is required (NOT NULL)."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        stock_id = _get_stock_id(session)
        report_id = _create_report(session, stock_id)

        shared = SharedReport(
            report_id=report_id,
            created_by=None,  # type: ignore[arg-type]
        )
        session.add(shared)
        with pytest.raises(IntegrityError):
            session.commit()

        session.close()
    finally:
        _teardown()


def test_shared_report_cascade_on_report_delete() -> None:
    """Deleting a report cascades to delete shared reports (FK CASCADE)."""
    _setup()
    try:
        engine = _make_fk_engine()
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        stock_id = _get_stock_id(session)
        user_id = _create_user(session)
        report_id = _create_report(session, stock_id)

        shared = SharedReport(
            report_id=report_id,
            created_by=user_id,
        )
        session.add(shared)
        session.commit()
        shared_id = shared.id

        # Delete the report via raw SQL to trigger FK CASCADE
        session.execute(
            Report.__table__.delete().where(Report.id == report_id)
        )
        session.commit()

        # SharedReport should be gone (CASCADE)
        remaining = session.execute(
            select(SharedReport).where(SharedReport.id == shared_id)
        ).scalar_one_or_none()
        assert remaining is None

        session.close()
        engine.dispose()
    finally:
        _teardown()


def test_shared_report_cascade_on_user_delete() -> None:
    """Deleting a user cascades to delete shared reports (FK CASCADE)."""
    _setup()
    try:
        engine = _make_fk_engine()
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()

        stock_id = _get_stock_id(session)
        user_id = _create_user(session)
        report_id = _create_report(session, stock_id)

        shared = SharedReport(
            report_id=report_id,
            created_by=user_id,
        )
        session.add(shared)
        session.commit()
        shared_id = shared.id

        # Delete the user via raw SQL to trigger FK CASCADE
        session.execute(
            User.__table__.delete().where(User.id == user_id)
        )
        session.commit()

        remaining = session.execute(
            select(SharedReport).where(SharedReport.id == shared_id)
        ).scalar_one_or_none()
        assert remaining is None

        session.close()
        engine.dispose()
    finally:
        _teardown()


def test_shared_report_token_is_36_chars() -> None:
    """Auto-generated share_token is UUID v4 format (36 chars)."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        stock_id = _get_stock_id(session)
        user_id = _create_user(session)
        report_id = _create_report(session, stock_id)

        shared = SharedReport(
            report_id=report_id,
            created_by=user_id,
        )
        session.add(shared)
        session.commit()

        assert len(shared.share_token) <= 36
        # Validate it's a valid UUID
        uuid.UUID(shared.share_token)

        session.close()
    finally:
        _teardown()
