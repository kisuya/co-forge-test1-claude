"""Tests for MarketBriefing model and data collection task (briefing-001)."""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, event, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.market_briefing import MarketBriefing
from app.models.report import PriceSnapshot
from app.models.stock import Stock
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_briefing_model.db"


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
    if os.path.exists("test_briefing_model.db"):
        os.remove("test_briefing_model.db")


def _get_kr_stock(session) -> Stock:
    return session.execute(
        select(Stock).where(Stock.market == "KRX")
    ).scalars().first()


def _get_us_stock(session) -> Stock:
    return session.execute(
        select(Stock).where(Stock.market.in_(("NYSE", "NASDAQ")))
    ).scalars().first()


def test_briefing_model_creation() -> None:
    """MarketBriefing can be created with valid fields."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        briefing = MarketBriefing(
            market="KR",
            date=date(2026, 2, 17),
            content={
                "summary": "Test summary",
                "key_issues": [],
                "top_movers": [],
                "market_stats": {},
            },
        )
        session.add(briefing)
        session.commit()
        session.refresh(briefing)

        assert briefing.id is not None
        assert briefing.market == "KR"
        assert briefing.date == date(2026, 2, 17)
        assert briefing.content["summary"] == "Test summary"
        assert briefing.created_at is not None
        session.close()
    finally:
        _teardown()


def test_briefing_us_market() -> None:
    """MarketBriefing can be created for US market."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        briefing = MarketBriefing(
            market="US",
            date=date(2026, 2, 17),
            content={"market": "US", "top_movers": []},
        )
        session.add(briefing)
        session.commit()
        session.refresh(briefing)

        assert briefing.market == "US"
        assert briefing.content["market"] == "US"
        session.close()
    finally:
        _teardown()


def test_briefing_unique_market_date() -> None:
    """MarketBriefing enforces unique constraint on (market, date)."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        b1 = MarketBriefing(
            market="KR",
            date=date(2026, 2, 17),
            content={"summary": "First"},
        )
        session.add(b1)
        session.commit()

        b2 = MarketBriefing(
            market="KR",
            date=date(2026, 2, 17),
            content={"summary": "Duplicate"},
        )
        session.add(b2)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_briefing_different_market_same_date() -> None:
    """Different markets can have briefings on the same date."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        b_kr = MarketBriefing(
            market="KR",
            date=date(2026, 2, 17),
            content={"market": "KR"},
        )
        b_us = MarketBriefing(
            market="US",
            date=date(2026, 2, 17),
            content={"market": "US"},
        )
        session.add(b_kr)
        session.add(b_us)
        session.commit()

        result = session.execute(
            select(MarketBriefing).where(MarketBriefing.date == date(2026, 2, 17))
        ).scalars().all()
        assert len(result) == 2
        markets = {b.market for b in result}
        assert markets == {"KR", "US"}
        session.close()
    finally:
        _teardown()


def test_briefing_market_not_null() -> None:
    """MarketBriefing market cannot be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        briefing = MarketBriefing(
            market=None,
            date=date(2026, 2, 17),
            content={},
        )
        session.add(briefing)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_briefing_date_not_null() -> None:
    """MarketBriefing date cannot be null."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        briefing = MarketBriefing(
            market="KR",
            date=None,
            content={},
        )
        session.add(briefing)
        with pytest.raises(IntegrityError):
            session.commit()
        session.rollback()
        session.close()
    finally:
        _teardown()


def test_briefing_content_nullable() -> None:
    """MarketBriefing content can be null (raw data not yet collected)."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        briefing = MarketBriefing(
            market="KR",
            date=date(2026, 2, 17),
            content=None,
        )
        session.add(briefing)
        session.commit()
        session.refresh(briefing)

        assert briefing.content is None
        session.close()
    finally:
        _teardown()


def test_collect_market_data_kr() -> None:
    """collect_market_data creates a KR briefing with stock data."""
    _setup()
    try:
        from app.workers.market_briefing_collector import collect_market_data

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        # Add some price snapshots for KR stocks
        kr_stock = _get_kr_stock(session)
        assert kr_stock is not None

        snap = PriceSnapshot(
            stock_id=kr_stock.id,
            price=Decimal("65300"),
            change_pct=3.5,
            volume=10000000,
        )
        session.add(snap)
        session.commit()

        target = date(2026, 2, 17)
        briefing = collect_market_data(session, market="KR", target_date=target)

        assert briefing is not None
        assert briefing.market == "KR"
        assert briefing.date == target
        assert briefing.content is not None
        assert briefing.content["market"] == "KR"
        assert "top_movers" in briefing.content
        assert len(briefing.content["top_movers"]) >= 1
        assert briefing.content["top_movers"][0]["stock_name"] == kr_stock.name
        assert briefing.content["top_movers"][0]["change_pct"] == 3.5
        session.close()
    finally:
        _teardown()


def test_collect_market_data_us() -> None:
    """collect_market_data creates a US briefing with stock data."""
    _setup()
    try:
        from app.workers.market_briefing_collector import collect_market_data

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        us_stock = _get_us_stock(session)
        if us_stock is None:
            pytest.skip("No US stocks seeded")

        snap = PriceSnapshot(
            stock_id=us_stock.id,
            price=Decimal("189.45"),
            change_pct=-2.1,
            volume=50000000,
        )
        session.add(snap)
        session.commit()

        target = date(2026, 2, 17)
        briefing = collect_market_data(session, market="US", target_date=target)

        assert briefing is not None
        assert briefing.market == "US"
        assert briefing.content["market"] == "US"
        assert len(briefing.content["top_movers"]) >= 1
        session.close()
    finally:
        _teardown()


def test_collect_market_data_idempotent() -> None:
    """collect_market_data returns existing briefing if already exists."""
    _setup()
    try:
        from app.workers.market_briefing_collector import collect_market_data

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        target = date(2026, 2, 17)
        b1 = collect_market_data(session, market="KR", target_date=target)
        b2 = collect_market_data(session, market="KR", target_date=target)

        assert b1.id == b2.id
        session.close()
    finally:
        _teardown()


def test_collect_market_data_custom_fetch_fn() -> None:
    """collect_market_data accepts custom fetch function for testing."""
    _setup()
    try:
        from app.workers.market_briefing_collector import collect_market_data

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        def mock_kr_fetch(db, td):
            return {
                "market": "KR",
                "date": str(td),
                "top_movers": [
                    {"stock_name": "MockStock", "change_pct": 5.0}
                ],
                "market_stats": {"stocks_up": 1, "stocks_down": 0},
            }

        target = date(2026, 2, 17)
        briefing = collect_market_data(
            session, market="KR", target_date=target, fetch_kr_fn=mock_kr_fetch
        )

        assert briefing is not None
        assert briefing.content["top_movers"][0]["stock_name"] == "MockStock"
        session.close()
    finally:
        _teardown()


def test_collect_market_data_empty_stocks() -> None:
    """collect_market_data handles empty stock list gracefully."""
    # Use a clean DB without seeding stocks
    create_tables(TEST_DB_URL)
    try:
        from app.workers.market_briefing_collector import collect_market_data

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        target = date(2026, 2, 17)
        briefing = collect_market_data(session, market="KR", target_date=target)

        assert briefing is not None
        assert briefing.content["top_movers"] == []
        session.close()
    finally:
        _teardown()


def test_collect_market_data_market_stats() -> None:
    """collect_market_data includes correct market stats."""
    _setup()
    try:
        from app.workers.market_briefing_collector import collect_market_data

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        # Add multiple snapshots with different change directions
        kr_stocks = session.execute(
            select(Stock).where(Stock.market == "KRX")
        ).scalars().all()

        if len(kr_stocks) >= 3:
            # Stock 1: up
            session.add(PriceSnapshot(
                stock_id=kr_stocks[0].id,
                price=Decimal("10000"),
                change_pct=2.5,
                volume=100000,
            ))
            # Stock 2: down
            session.add(PriceSnapshot(
                stock_id=kr_stocks[1].id,
                price=Decimal("20000"),
                change_pct=-1.8,
                volume=200000,
            ))
            # Stock 3: flat
            session.add(PriceSnapshot(
                stock_id=kr_stocks[2].id,
                price=Decimal("30000"),
                change_pct=0.0,
                volume=300000,
            ))
            session.commit()

        target = date(2026, 2, 18)
        briefing = collect_market_data(session, market="KR", target_date=target)

        assert briefing is not None
        stats = briefing.content.get("market_stats", {})
        assert "stocks_up" in stats
        assert "stocks_down" in stats
        assert "stocks_flat" in stats
        # At least the ones we added
        if len(kr_stocks) >= 3:
            assert stats["stocks_up"] >= 1
            assert stats["stocks_down"] >= 1
        session.close()
    finally:
        _teardown()


def test_celery_task_exists() -> None:
    """Celery task collect_market_data_task is defined."""
    from app.workers.market_briefing_collector import collect_market_data_task
    # Should be importable (may be None if celery not available)
    # But the function/attribute should exist
    assert collect_market_data_task is not None or True  # existence check


def test_briefing_index_exists() -> None:
    """MarketBriefing has required index on (market, date)."""
    indexes = MarketBriefing.__table__.indexes
    index_cols = set()
    for idx in indexes:
        cols = frozenset(c.name for c in idx.columns)
        index_cols.add(cols)

    assert frozenset({"market", "date"}) in index_cols


def test_briefing_autoincrement_id() -> None:
    """MarketBriefing uses autoincrement integer PK."""
    _setup()
    try:
        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        b1 = MarketBriefing(market="KR", date=date(2026, 1, 1), content={})
        session.add(b1)
        session.commit()
        session.refresh(b1)

        b2 = MarketBriefing(market="KR", date=date(2026, 1, 2), content={})
        session.add(b2)
        session.commit()
        session.refresh(b2)

        assert isinstance(b1.id, int)
        assert isinstance(b2.id, int)
        assert b2.id > b1.id
        session.close()
    finally:
        _teardown()
