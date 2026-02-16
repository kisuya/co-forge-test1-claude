"""Tests for LLM analysis service."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.llm_client import AnalysisCause, AnalysisResult
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import Report, ReportSource
from app.models.stock import Stock
from app.services.analysis_service import run_analysis

TEST_DB_URL = "sqlite:///test_analysis.db"


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
    if _os.path.exists("test_analysis.db"):
        _os.remove("test_analysis.db")


def _create_report_with_sources(session: Session) -> Report:
    stock = Stock(code="005930", name="삼성전자", market="KRX")
    session.add(stock)
    session.flush()

    report = Report(
        stock_id=stock.id,
        trigger_price=Decimal("70000"),
        trigger_change_pct=-5.0,
        status="generating",
    )
    session.add(report)
    session.flush()

    sources = [
        ReportSource(
            report_id=report.id, source_type="news",
            title="삼성전자 실적 부진", url="https://news.example.com/1",
        ),
        ReportSource(
            report_id=report.id, source_type="disclosure",
            title="분기보고서", url="https://dart.fss.or.kr/1",
        ),
    ]
    for s in sources:
        session.add(s)
    session.commit()
    return report


def _mock_analyze(
    name: str, code: str, change_pct: float, sources: list[dict[str, str]]
) -> AnalysisResult:
    return AnalysisResult(
        summary=f"{name} {change_pct:+.1f}% 변동 분석",
        causes=[
            AnalysisCause(
                reason="실적 부진",
                confidence="high",
                impact="단기 하락 압력",
            ),
            AnalysisCause(
                reason="시장 전반 약세",
                confidence="medium",
                impact="중립적",
            ),
        ],
    )


def test_run_analysis_updates_report() -> None:
    """run_analysis should update report summary, analysis, and status."""
    session = _setup()
    try:
        report = _create_report_with_sources(session)
        result = run_analysis(session, report, analyze_fn=_mock_analyze)

        assert result.summary == "삼성전자 -5.0% 변동 분석"
        assert len(result.causes) == 2

        db_report = session.execute(
            select(Report).where(Report.id == report.id)
        ).scalar_one()
        assert db_report.status == "completed"
        assert db_report.summary == "삼성전자 -5.0% 변동 분석"
        assert len(db_report.analysis["causes"]) == 2
    finally:
        _teardown(session)


def test_run_analysis_passes_sources_to_llm() -> None:
    """run_analysis should pass report sources to the analyze function."""
    session = _setup()
    try:
        report = _create_report_with_sources(session)
        captured_sources: list[list[dict[str, str]]] = []

        def capture_analyze(
            name: str, code: str, change_pct: float,
            sources: list[dict[str, str]],
        ) -> AnalysisResult:
            captured_sources.append(sources)
            return AnalysisResult(summary="test", causes=[])

        run_analysis(session, report, analyze_fn=capture_analyze)

        assert len(captured_sources) == 1
        assert len(captured_sources[0]) == 2
        types = {s["type"] for s in captured_sources[0]}
        assert types == {"news", "disclosure"}
    finally:
        _teardown(session)


def test_run_analysis_stores_structured_causes() -> None:
    """Analysis causes should be stored as structured JSON."""
    session = _setup()
    try:
        report = _create_report_with_sources(session)
        run_analysis(session, report, analyze_fn=_mock_analyze)

        db_report = session.execute(
            select(Report).where(Report.id == report.id)
        ).scalar_one()

        causes = db_report.analysis["causes"]
        assert causes[0]["reason"] == "실적 부진"
        assert causes[0]["confidence"] == "high"
        assert causes[1]["reason"] == "시장 전반 약세"
        assert causes[1]["confidence"] == "medium"
    finally:
        _teardown(session)


def test_run_analysis_with_no_sources() -> None:
    """run_analysis should work even with no sources."""
    session = _setup()
    try:
        stock = Stock(code="000660", name="SK하이닉스", market="KRX")
        session.add(stock)
        session.flush()
        report = Report(
            stock_id=stock.id,
            trigger_price=Decimal("130000"),
            trigger_change_pct=4.0,
            status="generating",
        )
        session.add(report)
        session.commit()

        def no_source_analyze(
            name: str, code: str, change_pct: float,
            sources: list[dict[str, str]],
        ) -> AnalysisResult:
            assert len(sources) == 0
            return AnalysisResult(
                summary="변동 원인 불명",
                causes=[AnalysisCause(
                    reason="명확한 원인 없음", confidence="low", impact="불확실"
                )],
            )

        result = run_analysis(session, report, analyze_fn=no_source_analyze)
        assert result.summary == "변동 원인 불명"
    finally:
        _teardown(session)
