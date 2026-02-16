"""Tests for price spike detection logic."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot, Report
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.price_detection import detect_price_spikes

TEST_DB_URL = "sqlite:///test_detection.db"


def _setup() -> Session:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    return factory()


def _teardown(session: Session) -> None:
    session.close()
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os as _os
    if _os.path.exists("test_detection.db"):
        _os.remove("test_detection.db")


def _seed_data(session: Session, change_pct: float, threshold: float = 3.0) -> None:
    """Create user, stock, watchlist, and snapshot with given change_pct."""
    user = User(email="detect@test.com", password_hash="pw")
    stock = Stock(code="005930", name="삼성전자", market="KRX")
    session.add_all([user, stock])
    session.flush()

    wl = Watchlist(user_id=user.id, stock_id=stock.id, threshold=threshold)
    session.add(wl)
    session.flush()

    snap = PriceSnapshot(
        stock_id=stock.id,
        price=Decimal("70000"),
        change_pct=change_pct,
        volume=1000000,
    )
    session.add(snap)
    session.commit()


def test_detect_spike_above_threshold_creates_report() -> None:
    """Change >= threshold should create a pending Report."""
    session = _setup()
    try:
        _seed_data(session, change_pct=5.0, threshold=3.0)
        reports = detect_price_spikes(session)
        assert len(reports) == 1
        assert reports[0].status == "pending"
        assert reports[0].trigger_change_pct == 5.0
    finally:
        _teardown(session)


def test_detect_no_spike_below_threshold() -> None:
    """Change < threshold should NOT create a Report."""
    session = _setup()
    try:
        _seed_data(session, change_pct=1.5, threshold=3.0)
        reports = detect_price_spikes(session)
        assert len(reports) == 0
    finally:
        _teardown(session)


def test_detect_negative_spike() -> None:
    """Negative change exceeding threshold should also trigger."""
    session = _setup()
    try:
        _seed_data(session, change_pct=-4.0, threshold=3.0)
        reports = detect_price_spikes(session)
        assert len(reports) == 1
        assert reports[0].trigger_change_pct == -4.0
    finally:
        _teardown(session)


def test_detect_respects_custom_threshold() -> None:
    """User custom threshold should be applied."""
    session = _setup()
    try:
        _seed_data(session, change_pct=4.0, threshold=5.0)
        reports = detect_price_spikes(session)
        assert len(reports) == 0
    finally:
        _teardown(session)


def test_detect_no_duplicate_reports() -> None:
    """Should not create duplicate pending reports for same stock/price."""
    session = _setup()
    try:
        _seed_data(session, change_pct=5.0, threshold=3.0)
        reports1 = detect_price_spikes(session)
        assert len(reports1) == 1

        reports2 = detect_price_spikes(session)
        assert len(reports2) == 0

        all_reports = session.execute(select(Report)).scalars().all()
        assert len(all_reports) == 1
    finally:
        _teardown(session)


def test_detect_no_snapshot_no_report() -> None:
    """If no snapshot exists, no report should be created."""
    session = _setup()
    try:
        user = User(email="nosnapshot@test.com", password_hash="pw")
        stock = Stock(code="999999", name="테스트", market="KRX")
        session.add_all([user, stock])
        session.flush()
        wl = Watchlist(user_id=user.id, stock_id=stock.id, threshold=3.0)
        session.add(wl)
        session.commit()

        reports = detect_price_spikes(session)
        no_snap_reports = [
            r for r in reports
            if r.stock_id == stock.id
        ]
        assert len(no_snap_reports) == 0
    finally:
        _teardown(session)
