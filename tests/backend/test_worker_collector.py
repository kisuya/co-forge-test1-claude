"""Tests for price collector worker."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.krx_client import StockPrice
from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot
from app.models.stock import Stock
from app.services.stock_service import seed_stocks
from app.workers.price_collector import collect_prices

TEST_DB_URL = "sqlite:///test_collector.db"


def _setup() -> Session:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    seed_stocks(session)
    return session


def _teardown(session: Session) -> None:
    session.close()
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    import os as _os
    if _os.path.exists("test_collector.db"):
        _os.remove("test_collector.db")


def _mock_fetch(codes: list[str]) -> list[StockPrice]:
    """Mock price fetcher returning fake data for all codes."""
    return [
        StockPrice(
            code=code,
            price=Decimal("50000"),
            change_pct=2.5,
            volume=1000000,
        )
        for code in codes
    ]


def test_collect_prices_stores_snapshots() -> None:
    """collect_prices should create PriceSnapshot for each stock."""
    session = _setup()
    try:
        count = collect_prices(session, fetch_fn=_mock_fetch)
        assert count > 0

        snapshots = session.execute(select(PriceSnapshot)).scalars().all()
        assert len(snapshots) == count
        assert all(s.price == Decimal("50000") for s in snapshots)
    finally:
        _teardown(session)


def test_collect_prices_with_empty_db() -> None:
    """collect_prices with no stocks should return 0."""
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    session = factory()
    try:
        # Delete all stocks first
        session.execute(select(Stock))
        count = collect_prices(session, fetch_fn=_mock_fetch)
        assert count == 0
    finally:
        _teardown(session)


def test_collect_prices_handles_partial_results() -> None:
    """collect_prices should handle when only some stocks return prices."""
    session = _setup()
    try:
        def partial_fetch(codes: list[str]) -> list[StockPrice]:
            return [
                StockPrice(
                    code=codes[0],
                    price=Decimal("75000"),
                    change_pct=-1.5,
                    volume=500000,
                )
            ]

        count = collect_prices(session, fetch_fn=partial_fetch)
        assert count == 1
    finally:
        _teardown(session)


def test_collect_prices_snapshot_fields() -> None:
    """PriceSnapshot should have correct fields after collection."""
    session = _setup()
    try:
        def single_fetch(codes: list[str]) -> list[StockPrice]:
            return [
                StockPrice(
                    code="005930",
                    price=Decimal("72000"),
                    change_pct=-3.2,
                    volume=2000000,
                )
            ]

        collect_prices(session, fetch_fn=single_fetch)

        samsung = session.execute(
            select(Stock).where(Stock.code == "005930")
        ).scalar_one()
        snapshot = session.execute(
            select(PriceSnapshot).where(PriceSnapshot.stock_id == samsung.id)
        ).scalar_one()

        assert snapshot.price == Decimal("72000")
        assert snapshot.change_pct == -3.2
        assert snapshot.volume == 2000000
    finally:
        _teardown(session)
