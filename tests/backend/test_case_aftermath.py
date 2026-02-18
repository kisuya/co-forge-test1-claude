"""Tests for case aftermath (analysis-007).

Verifies:
- _compute_aftermath correctly calculates after_1w_pct, after_1m_pct
- recovery_days calculation
- Data insufficient handling
- aftermath is attached to SimilarCaseWithTrend
- API includes aftermath in response
- Frontend renders aftermath data
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)

TEST_DB_URL = "sqlite:///test_case_aftermath.db"


def _setup():
    import app.models  # noqa: F401
    from app.db.database import create_tables
    create_tables(TEST_DB_URL)


def _teardown():
    from app.db.database import Base, get_engine, dispose_engine
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    dispose_engine(TEST_DB_URL)
    if os.path.exists("test_case_aftermath.db"):
        os.remove("test_case_aftermath.db")


def _get_session():
    from app.db.database import get_session_factory
    return get_session_factory(TEST_DB_URL)()


# ---- _compute_aftermath tests ----


def test_aftermath_1w_return():
    """aftermath should compute 1-week return from 5th trading day."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import PriceSnapshot
        from app.services.similar_case_service import _compute_aftermath

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        event_date = datetime.utcnow() - timedelta(days=60)
        event_price = 70000.0

        # Add 20 snapshots after event (prices increasing)
        for i in range(20):
            price = 70000 + (i + 1) * 500  # gradually rising
            session.add(PriceSnapshot(
                stock_id=stock.id,
                price=Decimal(str(price)),
                change_pct=0.7,
                volume=100000,
                captured_at=event_date + timedelta(days=i + 1),
            ))
        session.commit()

        result = _compute_aftermath(session, stock.id, event_date, event_price)
        assert result is not None
        # 5th day price = 70000 + 5*500 = 72500 → (72500-70000)/70000*100 = 3.57
        assert result.after_1w_pct is not None
        assert abs(result.after_1w_pct - 3.57) < 0.1
    finally:
        session.close()
        _teardown()


def test_aftermath_1m_return():
    """aftermath should compute 1-month return from 20th trading day."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import PriceSnapshot
        from app.services.similar_case_service import _compute_aftermath

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        event_date = datetime.utcnow() - timedelta(days=60)
        event_price = 70000.0

        for i in range(25):
            price = 70000 + (i + 1) * 500
            session.add(PriceSnapshot(
                stock_id=stock.id,
                price=Decimal(str(price)),
                change_pct=0.7,
                volume=100000,
                captured_at=event_date + timedelta(days=i + 1),
            ))
        session.commit()

        result = _compute_aftermath(session, stock.id, event_date, event_price)
        assert result is not None
        # 20th day price = 70000 + 20*500 = 80000 → (80000-70000)/70000*100 = 14.29
        assert result.after_1m_pct is not None
        assert abs(result.after_1m_pct - 14.29) < 0.1
    finally:
        session.close()
        _teardown()


def test_aftermath_recovery_days():
    """aftermath should compute recovery_days when price recovers."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import PriceSnapshot
        from app.services.similar_case_service import _compute_aftermath

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        event_date = datetime.utcnow() - timedelta(days=60)
        event_price = 70000.0

        # Prices: drop first, then recover
        prices = [68000, 66000, 65000, 67000, 69000, 70000, 71000]
        for i, price in enumerate(prices):
            session.add(PriceSnapshot(
                stock_id=stock.id,
                price=Decimal(str(price)),
                change_pct=-2.0 if i < 3 else 1.5,
                volume=100000,
                captured_at=event_date + timedelta(days=i + 1),
            ))
        session.commit()

        result = _compute_aftermath(session, stock.id, event_date, event_price)
        assert result is not None
        # Recovery at 70000 on day 6 (0-indexed 5)
        assert result.recovery_days == 6
    finally:
        session.close()
        _teardown()


def test_aftermath_no_recovery():
    """recovery_days should be None if price never recovers."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import PriceSnapshot
        from app.services.similar_case_service import _compute_aftermath

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        event_date = datetime.utcnow() - timedelta(days=60)
        event_price = 70000.0

        # Prices stay below event price
        for i in range(10):
            session.add(PriceSnapshot(
                stock_id=stock.id,
                price=Decimal(str(65000 + i * 200)),
                change_pct=-1.0,
                volume=100000,
                captured_at=event_date + timedelta(days=i + 1),
            ))
        session.commit()

        result = _compute_aftermath(session, stock.id, event_date, event_price)
        assert result is not None
        assert result.recovery_days is None
    finally:
        session.close()
        _teardown()


def test_aftermath_no_snapshots():
    """aftermath should be None if no snapshots after event."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.services.similar_case_service import _compute_aftermath

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.commit()

        event_date = datetime.utcnow() - timedelta(days=60)
        result = _compute_aftermath(session, stock.id, event_date, 70000.0)
        assert result is None
    finally:
        session.close()
        _teardown()


def test_aftermath_insufficient_data_for_1w():
    """after_1w_pct should be None if fewer than 5 snapshots."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import PriceSnapshot
        from app.services.similar_case_service import _compute_aftermath

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        event_date = datetime.utcnow() - timedelta(days=60)

        # Only 3 snapshots
        for i in range(3):
            session.add(PriceSnapshot(
                stock_id=stock.id,
                price=Decimal("71000"),
                change_pct=1.0,
                volume=100000,
                captured_at=event_date + timedelta(days=i + 1),
            ))
        session.commit()

        result = _compute_aftermath(session, stock.id, event_date, 70000.0)
        assert result is not None
        assert result.after_1w_pct is None
        assert result.after_1m_pct is None
    finally:
        session.close()
        _teardown()


def test_aftermath_zero_event_price():
    """aftermath should be None if event price is 0."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import PriceSnapshot
        from app.services.similar_case_service import _compute_aftermath

        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        event_date = datetime.utcnow() - timedelta(days=60)
        session.add(PriceSnapshot(
            stock_id=stock.id, price=Decimal("100"),
            change_pct=1.0, volume=100, captured_at=event_date + timedelta(days=1),
        ))
        session.commit()

        result = _compute_aftermath(session, stock.id, event_date, 0.0)
        assert result is None
    finally:
        session.close()
        _teardown()


# ---- CaseAftermath dataclass ----


def test_case_aftermath_dataclass():
    """CaseAftermath should store all fields."""
    from app.services.similar_case_service import CaseAftermath

    a = CaseAftermath(after_1w_pct=3.2, after_1m_pct=8.5, recovery_days=12)
    assert a.after_1w_pct == 3.2
    assert a.after_1m_pct == 8.5
    assert a.recovery_days == 12


def test_case_aftermath_null_fields():
    """CaseAftermath should allow None values."""
    from app.services.similar_case_service import CaseAftermath

    a = CaseAftermath(after_1w_pct=None, after_1m_pct=None, recovery_days=None)
    assert a.after_1w_pct is None
    assert a.after_1m_pct is None
    assert a.recovery_days is None


# ---- API response ----


def test_api_aftermath_response_model():
    """AftermathResponse should be importable and have correct fields."""
    from app.api.cases import AftermathResponse

    a = AftermathResponse(after_1w_pct=3.2, after_1m_pct=8.5, recovery_days=12)
    assert a.after_1w_pct == 3.2
    assert a.after_1m_pct == 8.5
    assert a.recovery_days == 12


def test_api_aftermath_response_optional():
    """AftermathResponse fields should default to None."""
    from app.api.cases import AftermathResponse

    a = AftermathResponse()
    assert a.after_1w_pct is None
    assert a.after_1m_pct is None
    assert a.recovery_days is None


def test_case_response_includes_aftermath():
    """CaseResponse should have optional aftermath field."""
    from app.api.cases import CaseResponse, AftermathResponse

    c = CaseResponse(
        date="2025-01-01",
        change_pct=-5.0,
        volume=100000,
        similarity_score=0.3,
        trend_1w=[],
        trend_1m=[],
        data_insufficient=False,
        aftermath=AftermathResponse(after_1w_pct=2.0),
    )
    assert c.aftermath is not None
    assert c.aftermath.after_1w_pct == 2.0


def test_case_response_no_aftermath():
    """CaseResponse should work without aftermath."""
    from app.api.cases import CaseResponse

    c = CaseResponse(
        date="2025-01-01",
        change_pct=-5.0,
        volume=100000,
        similarity_score=0.3,
        trend_1w=[],
        trend_1m=[],
        data_insufficient=False,
    )
    assert c.aftermath is None


# ---- Frontend rendering tests ----


def test_similar_cases_component_has_aftermath():
    """SimilarCases.tsx should render aftermath section."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "SimilarCases.tsx"
    content = path.read_text()
    assert "case-aftermath" in content
    assert "이후 추이" in content
    assert "recovery_days" in content
    assert "회복까지" in content


def test_frontend_types_case_aftermath():
    """Frontend types should include CaseAftermath interface."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "types" / "index.ts"
    content = path.read_text()
    assert "CaseAftermath" in content
    assert "after_1w_pct" in content
    assert "after_1m_pct" in content
    assert "recovery_days" in content


def test_similar_case_item_has_aftermath():
    """SimilarCaseItem type should have optional aftermath field."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "types" / "index.ts"
    content = path.read_text()
    assert "aftermath?: CaseAftermath" in content
