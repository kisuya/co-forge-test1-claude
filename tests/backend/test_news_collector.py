"""Tests for news and disclosure collector."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.dart_client import Disclosure
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import Report, ReportSource
from app.models.stock import Stock
from app.workers.news_collector import NewsItem, collect_news_for_report

TEST_DB_URL = "sqlite:///test_news.db"


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
    if _os.path.exists("test_news.db"):
        _os.remove("test_news.db")


def _create_stock_and_report(session: Session) -> tuple[Stock, Report]:
    stock = Stock(code="005930", name="삼성전자", market="KRX")
    session.add(stock)
    session.flush()
    report = Report(
        stock_id=stock.id,
        trigger_price=Decimal("70000"),
        trigger_change_pct=-5.0,
        status="pending",
    )
    session.add(report)
    session.commit()
    return stock, report


def test_collect_disclosures_creates_report_sources() -> None:
    """Should create ReportSource entries from mock disclosures."""
    session = _setup()
    try:
        stock, report = _create_stock_and_report(session)

        def mock_disclosures(code: str) -> list[Disclosure]:
            return [
                Disclosure(title="분기보고서", url="https://dart.fss.or.kr/1"),
                Disclosure(title="주요사항보고서", url="https://dart.fss.or.kr/2"),
            ]

        sources = collect_news_for_report(
            session, report, disclosure_fn=mock_disclosures
        )
        assert len(sources) == 2
        assert all(s.source_type == "disclosure" for s in sources)
    finally:
        _teardown(session)


def test_collect_news_creates_report_sources() -> None:
    """Should create ReportSource entries from mock news."""
    session = _setup()
    try:
        stock, report = _create_stock_and_report(session)

        def mock_news(name: str) -> list[NewsItem]:
            return [
                NewsItem(
                    title="삼성전자 실적 발표",
                    url="https://news.example.com/1",
                    published_at=datetime.now(timezone.utc),
                ),
            ]

        sources = collect_news_for_report(
            session, report, disclosure_fn=lambda c: [], news_fn=mock_news
        )
        assert len(sources) == 1
        assert sources[0].source_type == "news"
    finally:
        _teardown(session)


def test_collect_both_disclosures_and_news() -> None:
    """Should collect both disclosures and news."""
    session = _setup()
    try:
        stock, report = _create_stock_and_report(session)

        def mock_disc(code: str) -> list[Disclosure]:
            return [Disclosure(title="공시1", url="https://dart.fss.or.kr/1")]

        def mock_news(name: str) -> list[NewsItem]:
            return [NewsItem(title="뉴스1", url="https://news.example.com/1")]

        sources = collect_news_for_report(
            session, report, disclosure_fn=mock_disc, news_fn=mock_news
        )
        assert len(sources) == 2
        types = {s.source_type for s in sources}
        assert types == {"disclosure", "news"}
    finally:
        _teardown(session)


def test_collect_empty_sources() -> None:
    """Should handle no disclosures or news gracefully."""
    session = _setup()
    try:
        stock, report = _create_stock_and_report(session)

        sources = collect_news_for_report(
            session, report, disclosure_fn=lambda c: [], news_fn=lambda n: []
        )
        assert len(sources) == 0
    finally:
        _teardown(session)


def test_sources_linked_to_report() -> None:
    """ReportSource entries should be linked to the correct report."""
    session = _setup()
    try:
        stock, report = _create_stock_and_report(session)

        def mock_disc(code: str) -> list[Disclosure]:
            return [Disclosure(title="공시", url="https://dart.fss.or.kr/x")]

        collect_news_for_report(session, report, disclosure_fn=mock_disc)

        db_sources = session.execute(
            select(ReportSource).where(ReportSource.report_id == report.id)
        ).scalars().all()
        assert len(db_sources) == 1
        assert db_sources[0].report_id == report.id
    finally:
        _teardown(session)
