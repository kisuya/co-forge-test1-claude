"""Phase 4 integration tests for similar case scenario (case-004).

Verifies the similar case user journey:
  1. Report detail page → '과거 유사 사례' section displayed
  2. Case cards: date, change_pct, trend display
  3. Empty cases → appropriate message
  4. Mobile layout (grid-cols-1)
  5. Report generation includes similar_cases in analysis
  6. Phase 1-3 regression: all features still work
"""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.orm import Session

from app.clients.llm_client import AnalysisCause, AnalysisResult
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot, Report
from app.models.stock import Stock
from app.services.analysis_service import run_analysis
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_phase4_cases.db"

BASE_FE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def _get_test_db() -> Session:  # type: ignore[misc]
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        yield session  # type: ignore[misc]
    finally:
        session.close()


def _setup() -> None:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_stocks(session)
    seed_us_stocks(session)
    session.close()


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_phase4_cases.db"):
        os.remove("test_phase4_cases.db")


def _make_app():  # type: ignore[no-untyped-def]
    from app.api.auth import get_db as auth_get_db
    from app.api.deps import get_db as deps_get_db
    from app.main import create_app

    app = create_app()
    app.dependency_overrides[auth_get_db] = _get_test_db
    app.dependency_overrides[deps_get_db] = _get_test_db
    return app


async def _signup_login(c: AsyncClient) -> str:
    await c.post("/api/auth/signup", json={
        "email": "phase4@test.com", "password": "testpass123",
    })
    login = await c.post("/api/auth/login", json={
        "email": "phase4@test.com", "password": "testpass123",
    })
    return login.json()["access_token"]


def _mock_analyze(name: str, code: str, pct: float, sources: list) -> AnalysisResult:
    return AnalysisResult(
        summary=f"{name} 분석",
        causes=[AnalysisCause(reason="테스트", confidence="high", impact="상승")],
    )


# --- Scenario 1: Cases API returns empty for no-data report ---


@pytest.mark.asyncio
async def test_cases_api_empty_for_new_report() -> None:
    """GET /api/cases/{report_id} returns empty when no similar data."""
    _setup()
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        stock = session.query(Stock).filter(Stock.code == "005930").first()
        report = Report(
            stock_id=stock.id, trigger_price=Decimal("55000"),
            trigger_change_pct=5.0, status="completed",
        )
        session.add(report)
        session.commit()
        report_id = str(report.id)
        session.close()

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await c.get(f"/api/cases/{report_id}", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert data["cases"] == []
            assert "유사한" in data["message"]
    finally:
        _teardown()


# --- Scenario 2: Cases API returns data with trends ---


@pytest.mark.asyncio
async def test_cases_api_with_historical_data() -> None:
    """Cases API should return cases when historical data exists."""
    _setup()
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        stock = session.query(Stock).filter(Stock.code == "005930").first()
        snap = PriceSnapshot(
            stock_id=stock.id, price=Decimal("50000"),
            change_pct=5.0, volume=100000,
            captured_at=datetime.utcnow() - timedelta(days=60),
        )
        session.add(snap)

        report = Report(
            stock_id=stock.id, trigger_price=Decimal("55000"),
            trigger_change_pct=5.2, status="completed",
        )
        session.add(report)
        session.commit()
        report_id = str(report.id)
        session.close()

        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            token = await _signup_login(c)
            headers = {"Authorization": f"Bearer {token}"}

            resp = await c.get(f"/api/cases/{report_id}", headers=headers)
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["cases"]) >= 1
            case = data["cases"][0]
            assert "change_pct" in case
            assert "similarity_score" in case
            assert "trend_1w" in case
            assert "trend_1m" in case
    finally:
        _teardown()


# --- Scenario 3: Report generation includes similar_cases ---


def test_report_generation_includes_similar_cases() -> None:
    """run_analysis should add similar_cases to analysis JSONB."""
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        stock = Stock(code="005930", name="삼성전자", market="KRX")
        session.add(stock)
        session.flush()

        PriceSnapshot(
            stock_id=stock.id, price=Decimal("50000"),
            change_pct=5.0, volume=100000,
            captured_at=datetime.utcnow() - timedelta(days=60),
        )
        session.add(PriceSnapshot(
            stock_id=stock.id, price=Decimal("50000"),
            change_pct=5.0, volume=100000,
            captured_at=datetime.utcnow() - timedelta(days=60),
        ))

        report = Report(
            stock_id=stock.id, trigger_price=Decimal("55000"),
            trigger_change_pct=5.2, status="pending",
        )
        session.add(report)
        session.commit()

        run_analysis(session, report, analyze_fn=_mock_analyze)

        assert "similar_cases" in report.analysis
        assert isinstance(report.analysis["similar_cases"], list)
    finally:
        session.close()
        engine = get_engine(TEST_DB_URL)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        if os.path.exists("test_phase4_cases.db"):
            os.remove("test_phase4_cases.db")


# --- Scenario 4: Frontend structure checks ---


def test_similar_cases_component_exists():
    """SimilarCases component should exist."""
    path = os.path.join(BASE_FE, "components", "SimilarCases.tsx")
    assert os.path.isfile(path)


def test_similar_cases_in_report_view():
    """ReportView should include SimilarCases."""
    path = os.path.join(BASE_FE, "components", "ReportView.tsx")
    content = open(path).read()
    assert "SimilarCases" in content


def test_similar_cases_mobile_layout():
    """SimilarCases should use grid-cols-1 for mobile."""
    path = os.path.join(BASE_FE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "grid-cols-1" in content


def test_similar_cases_empty_state_messages():
    """Empty state should show both messages."""
    path = os.path.join(BASE_FE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "충분하지 않습니다" in content
    assert "자동으로 표시됩니다" in content


def test_similar_cases_toggle():
    """SimilarCases should be collapsible."""
    path = os.path.join(BASE_FE, "components", "SimilarCases.tsx")
    content = open(path).read()
    assert "similar-cases-toggle" in content
    assert "과거 유사 사례" in content


# --- Phase 1-3 regression ---


def test_regression_watchlist_manager():
    path = os.path.join(BASE_FE, "components", "WatchlistManager.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "StockSearch" in content


def test_regression_notification_panel():
    path = os.path.join(BASE_FE, "components", "NotificationPanel.tsx")
    assert os.path.isfile(path)
    content = open(path).read()
    assert "notification-bell" in content


def test_regression_market_tabs():
    path = os.path.join(BASE_FE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "market-tabs" in content
    assert "MARKET_TABS" in content


@pytest.mark.asyncio
async def test_regression_kr_search() -> None:
    """Korean stock search should still work."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={"q": "삼성"})
            assert resp.status_code == 200
            assert len(resp.json()) > 0
    finally:
        _teardown()


@pytest.mark.asyncio
async def test_regression_us_search() -> None:
    """US stock search should still work."""
    _setup()
    try:
        app = _make_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            resp = await c.get("/api/stocks/search", params={
                "q": "AAPL", "market": "us",
            })
            assert resp.status_code == 200
            assert len(resp.json()) >= 1
    finally:
        _teardown()
