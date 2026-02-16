"""Tests for database models and table creation."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models import (
    PriceSnapshot,
    Report,
    ReportSource,
    Stock,
    User,
    Watchlist,
)

TEST_DB_URL = "sqlite:///test_ohmystock.db"


def _setup_db() -> Session:
    """Create all tables and return a session."""
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    return factory()


def _teardown_db(session: Session) -> None:
    """Drop all tables and close session."""
    engine = get_engine(TEST_DB_URL)
    session.close()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os
    if os.path.exists("test_ohmystock.db"):
        os.remove("test_ohmystock.db")


def test_create_tables_creates_all_expected_tables() -> None:
    """All 6 tables should be created."""
    session = _setup_db()
    try:
        engine = get_engine(TEST_DB_URL)
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        expected = {"users", "stocks", "watchlists", "price_snapshots", "reports", "report_sources"}
        assert expected.issubset(tables), f"Missing tables: {expected - tables}"
    finally:
        _teardown_db(session)


def test_user_model_crud() -> None:
    """Should be able to create and query a User."""
    session = _setup_db()
    try:
        user = User(
            email="test@example.com",
            password_hash="hashed_pw",
            settings={"threshold": 3.0},
        )
        session.add(user)
        session.commit()

        result = session.execute(select(User).where(User.email == "test@example.com"))
        fetched = result.scalar_one()
        assert fetched.email == "test@example.com"
        assert fetched.password_hash == "hashed_pw"
        assert isinstance(fetched.id, uuid.UUID)
    finally:
        _teardown_db(session)


def test_stock_model_crud() -> None:
    """Should be able to create and query a Stock."""
    session = _setup_db()
    try:
        stock = Stock(code="005930", name="삼성전자", market="KRX", sector="전기전자")
        session.add(stock)
        session.commit()

        result = session.execute(select(Stock).where(Stock.code == "005930"))
        fetched = result.scalar_one()
        assert fetched.name == "삼성전자"
        assert fetched.market == "KRX"
    finally:
        _teardown_db(session)


def test_watchlist_links_user_and_stock() -> None:
    """Watchlist should link a user to a stock with a threshold."""
    session = _setup_db()
    try:
        user = User(email="wl@test.com", password_hash="pw")
        stock = Stock(code="000660", name="SK하이닉스", market="KRX")
        session.add_all([user, stock])
        session.flush()

        wl = Watchlist(user_id=user.id, stock_id=stock.id, threshold=5.0)
        session.add(wl)
        session.commit()

        result = session.execute(select(Watchlist).where(Watchlist.user_id == user.id))
        fetched = result.scalar_one()
        assert fetched.stock_id == stock.id
        assert fetched.threshold == 5.0
    finally:
        _teardown_db(session)


def test_price_snapshot_stores_decimal_price() -> None:
    """PriceSnapshot should store price as Decimal."""
    session = _setup_db()
    try:
        stock = Stock(code="035420", name="NAVER", market="KRX")
        session.add(stock)
        session.flush()

        snap = PriceSnapshot(
            stock_id=stock.id,
            price=Decimal("215000"),
            change_pct=-2.5,
            volume=1000000,
        )
        session.add(snap)
        session.commit()

        result = session.execute(
            select(PriceSnapshot).where(PriceSnapshot.stock_id == stock.id)
        )
        fetched = result.scalar_one()
        assert fetched.price == Decimal("215000")
        assert fetched.change_pct == -2.5
    finally:
        _teardown_db(session)


def test_report_with_sources() -> None:
    """Report should have associated ReportSource entries."""
    session = _setup_db()
    try:
        stock = Stock(code="035720", name="카카오", market="KRX")
        session.add(stock)
        session.flush()

        report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("52000"),
            trigger_change_pct=-5.3,
            status="completed",
            summary="카카오 급락 분석",
            analysis={"causes": [{"reason": "실적 부진", "confidence": "high"}]},
        )
        session.add(report)
        session.flush()

        source = ReportSource(
            report_id=report.id,
            source_type="news",
            title="카카오 실적 부진 뉴스",
            url="https://example.com/news/1",
        )
        session.add(source)
        session.commit()

        result = session.execute(select(Report).where(Report.stock_id == stock.id))
        fetched = result.scalar_one()
        assert fetched.summary == "카카오 급락 분석"
        assert fetched.analysis["causes"][0]["confidence"] == "high"
        assert len(fetched.sources) == 1
        assert fetched.sources[0].source_type == "news"
    finally:
        _teardown_db(session)
