"""Tests for US stock seed data (stock-002)."""
from __future__ import annotations

import os

import pytest
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.stock import Stock
from app.services.stock_service import seed_stocks, seed_us_stocks, search_stocks

TEST_DB_URL = "sqlite:///test_us_stock_seed.db"


def _setup() -> Session:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    return factory()


def _teardown(session: Session | None = None) -> None:
    if session:
        session.close()
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_us_stock_seed.db"):
        os.remove("test_us_stock_seed.db")


# --- Seed data ---


def test_us_stock_data_has_100_plus_entries() -> None:
    """SAMPLE_US_STOCKS should have at least 100 entries."""
    from app.data.us_stocks import SAMPLE_US_STOCKS
    assert len(SAMPLE_US_STOCKS) >= 100


def test_us_stock_data_has_correct_fields() -> None:
    """Each US stock entry should have (code, name, name_kr, market, sector)."""
    from app.data.us_stocks import SAMPLE_US_STOCKS
    for entry in SAMPLE_US_STOCKS:
        assert len(entry) == 5
        code, name, name_kr, market, sector = entry
        assert isinstance(code, str) and len(code) > 0
        assert isinstance(name, str) and len(name) > 0
        assert isinstance(name_kr, str) and len(name_kr) > 0
        assert market in ("NYSE", "NASDAQ")
        assert isinstance(sector, str) and len(sector) > 0


def test_us_stock_data_has_key_stocks() -> None:
    """Seed data should include major US stocks."""
    from app.data.us_stocks import SAMPLE_US_STOCKS
    codes = {s[0] for s in SAMPLE_US_STOCKS}
    for code in ("AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"):
        assert code in codes


def test_us_stock_codes_unique() -> None:
    """All US stock codes should be unique."""
    from app.data.us_stocks import SAMPLE_US_STOCKS
    codes = [s[0] for s in SAMPLE_US_STOCKS]
    assert len(codes) == len(set(codes))


# --- seed_us_stocks function ---


def test_seed_us_stocks_creates_records() -> None:
    """seed_us_stocks should insert US stocks into the database."""
    session = _setup()
    try:
        count = seed_us_stocks(session)
        assert count >= 100
        us = session.query(Stock).filter(Stock.market.in_(["NYSE", "NASDAQ"])).count()
        assert us >= 100
    finally:
        _teardown(session)


def test_seed_us_stocks_idempotent() -> None:
    """Running seed_us_stocks twice should not create duplicates."""
    session = _setup()
    try:
        first = seed_us_stocks(session)
        second = seed_us_stocks(session)
        assert first >= 100
        assert second == 0
    finally:
        _teardown(session)


def test_seed_us_stocks_independent_from_krx() -> None:
    """seed_us_stocks and seed_stocks should be independent."""
    session = _setup()
    try:
        krx_count = seed_stocks(session)
        us_count = seed_us_stocks(session)
        assert krx_count > 0
        assert us_count > 0

        total = session.query(Stock).count()
        assert total == krx_count + us_count

        krx = session.query(Stock).filter(Stock.market == "KRX").count()
        us = session.query(Stock).filter(Stock.market.in_(["NYSE", "NASDAQ"])).count()
        assert krx == krx_count
        assert us == us_count
    finally:
        _teardown(session)


# --- name_kr field ---


def test_stock_model_has_name_kr() -> None:
    """Stock model should have name_kr column."""
    assert hasattr(Stock, "name_kr")


def test_us_stocks_have_name_kr() -> None:
    """Seeded US stocks should have name_kr set."""
    session = _setup()
    try:
        seed_us_stocks(session)
        apple = session.query(Stock).filter(Stock.code == "AAPL").first()
        assert apple is not None
        assert apple.name_kr == "애플"

        tesla = session.query(Stock).filter(Stock.code == "TSLA").first()
        assert tesla is not None
        assert tesla.name_kr == "테슬라"
    finally:
        _teardown(session)


def test_krx_stocks_name_kr_is_none() -> None:
    """KRX stocks should have name_kr as None (backward compat)."""
    session = _setup()
    try:
        seed_stocks(session)
        samsung = session.query(Stock).filter(Stock.code == "005930").first()
        assert samsung is not None
        assert samsung.name_kr is None
    finally:
        _teardown(session)


# --- Search with name_kr ---


def test_search_by_korean_name_returns_us_stock() -> None:
    """Searching '애플' with market=us should return AAPL."""
    session = _setup()
    try:
        seed_us_stocks(session)
        results = search_stocks(session, "애플", market="us")
        codes = [s.code for s in results]
        assert "AAPL" in codes
    finally:
        _teardown(session)


def test_search_by_english_name_returns_us_stock() -> None:
    """Searching 'Apple' with market=us should return AAPL."""
    session = _setup()
    try:
        seed_us_stocks(session)
        results = search_stocks(session, "Apple", market="us")
        codes = [s.code for s in results]
        assert "AAPL" in codes
    finally:
        _teardown(session)


def test_search_by_code_returns_us_stock() -> None:
    """Searching 'TSLA' with market=us should return Tesla."""
    session = _setup()
    try:
        seed_us_stocks(session)
        results = search_stocks(session, "TSLA", market="us")
        assert len(results) >= 1
        assert results[0].code == "TSLA"
    finally:
        _teardown(session)


def test_krx_search_unaffected() -> None:
    """Existing KRX search should still work after US seed."""
    session = _setup()
    try:
        seed_stocks(session)
        seed_us_stocks(session)
        results = search_stocks(session, "삼성")
        codes = [s.code for s in results]
        assert any(c.startswith("0") for c in codes)
    finally:
        _teardown(session)


# --- Market differentiation ---


def test_us_stocks_have_correct_market() -> None:
    """US stocks should have NYSE or NASDAQ market."""
    session = _setup()
    try:
        seed_us_stocks(session)
        us_stocks = session.query(Stock).filter(
            Stock.market.in_(["NYSE", "NASDAQ"])
        ).all()
        for s in us_stocks:
            assert s.market in ("NYSE", "NASDAQ")
    finally:
        _teardown(session)


# --- Startup integration ---


def test_main_imports_seed_us_stocks() -> None:
    """main.py should import and call seed_us_stocks."""
    import inspect
    from app import main as main_module
    src = inspect.getsource(main_module)
    assert "seed_us_stocks" in src
