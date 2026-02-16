"""Tests for report generation pipeline."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.dart_client import Disclosure
from app.clients.llm_client import AnalysisCause, AnalysisResult
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot, Report, ReportSource
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.report_service import generate_reports
from app.workers.news_collector import NewsItem

TEST_DB_URL = "sqlite:///test_pipeline.db"


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
    if _os.path.exists("test_pipeline.db"):
        _os.remove("test_pipeline.db")


def _seed_spike_scenario(session: Session) -> None:
    """Create a scenario where a stock has a spike."""
    user = User(email="pipeline@test.com", password_hash="pw")
    stock = Stock(code="005930", name="삼성전자", market="KRX")
    session.add_all([user, stock])
    session.flush()

    wl = Watchlist(user_id=user.id, stock_id=stock.id, threshold=3.0)
    session.add(wl)

    snap = PriceSnapshot(
        stock_id=stock.id,
        price=Decimal("70000"),
        change_pct=-5.0,
        volume=2000000,
    )
    session.add(snap)
    session.commit()


def _mock_disclosures(code: str) -> list[Disclosure]:
    return [Disclosure(title="분기보고서", url="https://dart.fss.or.kr/1")]


def _mock_news(name: str) -> list[NewsItem]:
    return [NewsItem(title=f"{name} 관련 뉴스", url="https://news.example.com/1")]


def _mock_analyze(
    name: str, code: str, change_pct: float, sources: list[dict[str, str]]
) -> AnalysisResult:
    return AnalysisResult(
        summary=f"{name} 급락 분석",
        causes=[
            AnalysisCause(reason="실적 부진", confidence="high", impact="하락"),
        ],
    )


def test_pipeline_end_to_end() -> None:
    """Full pipeline: spike detection -> news -> analysis -> completed report."""
    session = _setup()
    try:
        _seed_spike_scenario(session)

        completed = generate_reports(
            session,
            disclosure_fn=_mock_disclosures,
            news_fn=_mock_news,
            analyze_fn=_mock_analyze,
        )

        assert len(completed) == 1
        report = completed[0]
        assert report.status == "completed"
        assert report.summary == "삼성전자 급락 분석"
        assert report.completed_at is not None
    finally:
        _teardown(session)


def test_pipeline_creates_report_sources() -> None:
    """Pipeline should create both disclosure and news sources."""
    session = _setup()
    try:
        _seed_spike_scenario(session)

        completed = generate_reports(
            session,
            disclosure_fn=_mock_disclosures,
            news_fn=_mock_news,
            analyze_fn=_mock_analyze,
        )

        sources = session.execute(
            select(ReportSource).where(ReportSource.report_id == completed[0].id)
        ).scalars().all()
        assert len(sources) == 2
        types = {s.source_type for s in sources}
        assert types == {"disclosure", "news"}
    finally:
        _teardown(session)


def test_pipeline_no_spike_no_report() -> None:
    """If no spike detected, no reports should be generated."""
    session = _setup()
    try:
        user = User(email="nospike@test.com", password_hash="pw")
        stock = Stock(code="000660", name="SK하이닉스", market="KRX")
        session.add_all([user, stock])
        session.flush()

        wl = Watchlist(user_id=user.id, stock_id=stock.id, threshold=3.0)
        snap = PriceSnapshot(
            stock_id=stock.id, price=Decimal("130000"),
            change_pct=1.0, volume=500000,
        )
        session.add_all([wl, snap])
        session.commit()

        completed = generate_reports(
            session,
            disclosure_fn=_mock_disclosures,
            news_fn=_mock_news,
            analyze_fn=_mock_analyze,
        )
        assert len(completed) == 0
    finally:
        _teardown(session)


def test_pipeline_handles_analysis_failure() -> None:
    """If analysis fails, report status should be 'failed'."""
    session = _setup()
    try:
        _seed_spike_scenario(session)

        def failing_analyze(*args, **kwargs) -> AnalysisResult:
            raise RuntimeError("LLM API error")

        completed = generate_reports(
            session,
            disclosure_fn=_mock_disclosures,
            news_fn=_mock_news,
            analyze_fn=failing_analyze,
        )
        assert len(completed) == 0

        reports = session.execute(select(Report)).scalars().all()
        assert len(reports) == 1
        assert reports[0].status == "failed"
    finally:
        _teardown(session)
