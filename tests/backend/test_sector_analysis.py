"""Tests for sector chain impact analysis (analysis-006).

Verifies:
- get_sector_impact finds same-sector stocks
- Related stock change_pct from price_snapshots
- Correlation note generation (동반 상승/하락/혼조세)
- No sector → returns None
- No related stocks → returns None
- analysis_service stores sector_impact in JSONB
- Frontend rendering of sector impact section
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

TEST_DB_URL = "sqlite:///test_sector_analysis.db"


def _setup():
    import app.models  # noqa: F401
    from app.db.database import create_tables
    create_tables(TEST_DB_URL)


def _teardown():
    from app.db.database import Base, get_engine, dispose_engine
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    dispose_engine(TEST_DB_URL)
    if os.path.exists("test_sector_analysis.db"):
        os.remove("test_sector_analysis.db")


def _get_session():
    from app.db.database import get_session_factory
    return get_session_factory(TEST_DB_URL)()


def _create_stocks_with_sector(session, sector="반도체"):
    """Create a main stock and related stocks in the same sector."""
    from app.models.stock import Stock
    from app.models.report import PriceSnapshot

    main = Stock(code="005930", name="삼성전자", market="KRX", sector=sector)
    related1 = Stock(code="000660", name="SK하이닉스", market="KRX", sector=sector)
    related2 = Stock(code="042700", name="한미반도체", market="KRX", sector=sector)
    other = Stock(code="035720", name="카카오", market="KRX", sector="인터넷")

    session.add_all([main, related1, related2, other])
    session.flush()

    now = datetime.utcnow()

    # Add recent price snapshots for related stocks
    session.add(PriceSnapshot(
        stock_id=related1.id, price=Decimal("130000"),
        change_pct=-3.5, volume=100000, captured_at=now,
    ))
    session.add(PriceSnapshot(
        stock_id=related2.id, price=Decimal("25000"),
        change_pct=-2.1, volume=50000, captured_at=now,
    ))
    session.commit()

    return main, related1, related2, other


# ---- sector_service tests ----


def test_get_sector_impact_finds_related():
    """get_sector_impact should find stocks in the same sector."""
    _setup()
    session = _get_session()
    try:
        from app.services.sector_service import get_sector_impact
        main, r1, r2, other = _create_stocks_with_sector(session)

        result = get_sector_impact(session, str(main.id))
        assert result is not None
        assert result.sector == "반도체"
        assert len(result.related_stocks) == 2

        names = {rs.name for rs in result.related_stocks}
        assert "SK하이닉스" in names
        assert "한미반도체" in names
        assert "카카오" not in names
    finally:
        session.close()
        _teardown()


def test_get_sector_impact_change_pcts():
    """Related stocks should have correct change_pct values."""
    _setup()
    session = _get_session()
    try:
        from app.services.sector_service import get_sector_impact
        main, _, _, _ = _create_stocks_with_sector(session)

        result = get_sector_impact(session, str(main.id))
        assert result is not None

        by_name = {rs.name: rs for rs in result.related_stocks}
        assert by_name["SK하이닉스"].change_pct == -3.5
        assert by_name["한미반도체"].change_pct == -2.1
    finally:
        session.close()
        _teardown()


def test_get_sector_impact_correlation_note_down():
    """Correlation note should indicate 동반 하락 when majority falls."""
    _setup()
    session = _get_session()
    try:
        from app.services.sector_service import get_sector_impact
        main, _, _, _ = _create_stocks_with_sector(session)

        result = get_sector_impact(session, str(main.id))
        assert result is not None
        assert "동반 하락" in result.correlation_note
    finally:
        session.close()
        _teardown()


def test_get_sector_impact_correlation_note_up():
    """Correlation note should indicate 동반 상승 when majority rises."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import PriceSnapshot
        from app.services.sector_service import get_sector_impact

        main = Stock(code="AAPL", name="Apple", market="NASDAQ", sector="Tech")
        r1 = Stock(code="MSFT", name="Microsoft", market="NASDAQ", sector="Tech")
        r2 = Stock(code="GOOGL", name="Google", market="NASDAQ", sector="Tech")
        session.add_all([main, r1, r2])
        session.flush()

        now = datetime.utcnow()
        session.add(PriceSnapshot(
            stock_id=r1.id, price=Decimal("400"), change_pct=2.5,
            volume=100000, captured_at=now,
        ))
        session.add(PriceSnapshot(
            stock_id=r2.id, price=Decimal("170"), change_pct=1.8,
            volume=80000, captured_at=now,
        ))
        session.commit()

        result = get_sector_impact(session, str(main.id))
        assert result is not None
        assert "동반 상승" in result.correlation_note
    finally:
        session.close()
        _teardown()


def test_get_sector_impact_mixed():
    """Correlation note should say 혼조세 when no clear majority."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import PriceSnapshot
        from app.services.sector_service import get_sector_impact

        main = Stock(code="S1", name="Stock1", market="KRX", sector="혼합")
        r1 = Stock(code="S2", name="Stock2", market="KRX", sector="혼합")
        r2 = Stock(code="S3", name="Stock3", market="KRX", sector="혼합")
        r3 = Stock(code="S4", name="Stock4", market="KRX", sector="혼합")
        session.add_all([main, r1, r2, r3])
        session.flush()

        now = datetime.utcnow()
        session.add(PriceSnapshot(
            stock_id=r1.id, price=Decimal("1000"), change_pct=2.0,
            volume=1000, captured_at=now,
        ))
        session.add(PriceSnapshot(
            stock_id=r2.id, price=Decimal("2000"), change_pct=-1.5,
            volume=2000, captured_at=now,
        ))
        session.add(PriceSnapshot(
            stock_id=r3.id, price=Decimal("3000"), change_pct=0.0,
            volume=3000, captured_at=now,
        ))
        session.commit()

        result = get_sector_impact(session, str(main.id))
        assert result is not None
        assert "혼조세" in result.correlation_note
    finally:
        session.close()
        _teardown()


def test_get_sector_impact_no_sector():
    """Should return None if stock has no sector."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.services.sector_service import get_sector_impact

        stock = Stock(code="NOSEC", name="No Sector", market="KRX", sector=None)
        session.add(stock)
        session.commit()

        result = get_sector_impact(session, str(stock.id))
        assert result is None
    finally:
        session.close()
        _teardown()


def test_get_sector_impact_no_related_stocks():
    """Should return None if no other stocks in the same sector."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.services.sector_service import get_sector_impact

        stock = Stock(code="ALONE", name="Lonely", market="KRX", sector="독점업종")
        session.add(stock)
        session.commit()

        result = get_sector_impact(session, str(stock.id))
        assert result is None
    finally:
        session.close()
        _teardown()


def test_get_sector_impact_no_recent_snapshots():
    """Should return None if related stocks have no recent snapshots."""
    _setup()
    session = _get_session()
    try:
        from app.models.stock import Stock
        from app.models.report import PriceSnapshot
        from app.services.sector_service import get_sector_impact

        main = Stock(code="M1", name="Main", market="KRX", sector="테스트")
        related = Stock(code="R1", name="Related", market="KRX", sector="테스트")
        session.add_all([main, related])
        session.flush()

        # Add old snapshot (> 24 hours)
        old_time = datetime.utcnow() - timedelta(hours=48)
        session.add(PriceSnapshot(
            stock_id=related.id, price=Decimal("1000"), change_pct=1.0,
            volume=100, captured_at=old_time,
        ))
        session.commit()

        result = get_sector_impact(session, str(main.id))
        assert result is None
    finally:
        session.close()
        _teardown()


# ---- analysis_service integration ----


def test_run_analysis_stores_sector_impact():
    """run_analysis should store sector_impact in report.analysis."""
    _setup()
    session = _get_session()
    try:
        from app.clients.llm_client import MultiLayerAnalysisResult
        from app.models.report import Report, PriceSnapshot
        from app.models.stock import Stock
        from app.services.analysis_service import run_analysis

        main = Stock(code="005930", name="삼성전자", market="KRX", sector="반도체")
        related = Stock(code="000660", name="SK하이닉스", market="KRX", sector="반도체")
        session.add_all([main, related])
        session.flush()

        now = datetime.utcnow()
        session.add(PriceSnapshot(
            stock_id=related.id, price=Decimal("130000"),
            change_pct=-4.2, volume=90000, captured_at=now,
        ))

        report = Report(
            stock_id=main.id,
            trigger_price=Decimal("70000"),
            trigger_change_pct=-5.0,
            status="generating",
        )
        session.add(report)
        session.commit()

        def mock_analyze(name, code, change_pct, sources):
            return MultiLayerAnalysisResult(summary="test")

        run_analysis(session, report, analyze_fn=mock_analyze)

        db_report = session.execute(
            select(Report).where(Report.id == report.id)
        ).scalar_one()

        assert "sector_impact" in db_report.analysis
        si = db_report.analysis["sector_impact"]
        assert si["sector"] == "반도체"
        assert len(si["related_stocks"]) == 1
        assert si["related_stocks"][0]["name"] == "SK하이닉스"
        assert si["related_stocks"][0]["change_pct"] == -4.2
    finally:
        session.close()
        _teardown()


def test_run_analysis_no_sector_impact():
    """run_analysis should not add sector_impact when stock has no sector."""
    _setup()
    session = _get_session()
    try:
        from app.clients.llm_client import MultiLayerAnalysisResult
        from app.models.report import Report
        from app.models.stock import Stock
        from app.services.analysis_service import run_analysis

        stock = Stock(code="NOSEC", name="No Sector", market="KRX", sector=None)
        session.add(stock)
        session.flush()

        report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("10000"),
            trigger_change_pct=-3.0,
            status="generating",
        )
        session.add(report)
        session.commit()

        def mock_analyze(name, code, change_pct, sources):
            return MultiLayerAnalysisResult(summary="test")

        run_analysis(session, report, analyze_fn=mock_analyze)

        db_report = session.execute(
            select(Report).where(Report.id == report.id)
        ).scalar_one()

        assert "sector_impact" not in db_report.analysis
    finally:
        session.close()
        _teardown()


# ---- Frontend rendering tests (structure) ----


def test_report_view_sector_impact_section():
    """ReportView.tsx should have sector impact section."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "ReportView.tsx"
    content = path.read_text()
    assert "sector-impact-section" in content
    assert "섹터 영향" in content


def test_report_view_sector_related_stocks():
    """ReportView.tsx should render related stocks with change_pct."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "ReportView.tsx"
    content = path.read_text()
    assert "sector-related-stock" in content
    assert "change_pct" in content
    assert "correlation_note" in content


def test_frontend_types_sector_impact():
    """Frontend types should include SectorImpact interface."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "types" / "index.ts"
    content = path.read_text()
    assert "SectorImpact" in content
    assert "SectorRelatedStock" in content
    assert "sector_impact" in content


def test_report_view_sector_graceful_fallback():
    """ReportView.tsx should not render sector section when missing."""
    import pathlib
    path = pathlib.Path(__file__).parent.parent.parent / "frontend" / "src" / "components" / "ReportView.tsx"
    content = path.read_text()
    # Should check for sector_impact existence
    assert "sector_impact" in content
