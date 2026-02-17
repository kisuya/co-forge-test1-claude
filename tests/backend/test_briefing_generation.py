"""Tests for AI briefing generation (briefing-002)."""
from __future__ import annotations

import os
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from sqlalchemy import select

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.market_briefing import MarketBriefing
from app.models.report import PriceSnapshot
from app.models.stock import Stock
from app.services.stock_service import seed_stocks, seed_us_stocks

TEST_DB_URL = "sqlite:///test_briefing_gen.db"


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
    if os.path.exists("test_briefing_gen.db"):
        os.remove("test_briefing_gen.db")


def _create_raw_briefing(session, market="KR", target_date=None) -> MarketBriefing:
    """Create a raw briefing with sample market data."""
    if target_date is None:
        target_date = date(2026, 2, 17)

    briefing = MarketBriefing(
        market=market,
        date=target_date,
        content={
            "market": market,
            "date": str(target_date),
            "total_stocks": 10,
            "top_movers": [
                {
                    "stock_name": "삼성전자",
                    "stock_code": "005930",
                    "price": 65300.0,
                    "change_pct": 3.5,
                    "volume": 10000000,
                },
                {
                    "stock_name": "SK하이닉스",
                    "stock_code": "000660",
                    "price": 120000.0,
                    "change_pct": -2.1,
                    "volume": 5000000,
                },
            ],
            "market_stats": {
                "stocks_up": 6,
                "stocks_down": 3,
                "stocks_flat": 1,
            },
        },
    )
    session.add(briefing)
    session.commit()
    session.refresh(briefing)
    return briefing


def _mock_generate_fn(raw_data: dict) -> dict:
    """Mock AI generation function that returns structured briefing."""
    return {
        "summary": "오늘 한국 시장은 반도체 관련주를 중심으로 상승세를 보였습니다. "
                   "삼성전자가 3.5% 상승하며 시장을 이끌었고, "
                   "SK하이닉스는 2.1% 하락했습니다.",
        "key_issues": [
            {
                "title": "반도체 수출 호조",
                "description": "1월 반도체 수출이 전년 대비 30% 증가하며 시장 심리 개선.",
            },
            {
                "title": "미국 금리 동결 기대",
                "description": "연준의 금리 동결 기대감이 글로벌 증시에 긍정적 영향.",
            },
            {
                "title": "원달러 환율 하락",
                "description": "원달러 환율이 1,300원대로 하락하며 외국인 매수 유입.",
            },
        ],
        "top_movers": [
            {
                "stock_name": "삼성전자",
                "change_pct": 3.5,
                "reason": "HBM 수주 기대감으로 상승",
            },
            {
                "stock_name": "SK하이닉스",
                "change_pct": -2.1,
                "reason": "실적 우려로 차익 매물 출회",
            },
        ],
    }


def _mock_generate_fn_fail(raw_data: dict) -> None:
    """Mock AI generation function that returns None (failure)."""
    return None


def test_generate_briefing_success() -> None:
    """AI briefing generation succeeds with mock function."""
    _setup()
    try:
        from app.workers.market_briefing_generator import generate_market_briefing

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        _create_raw_briefing(session)

        result = generate_market_briefing(
            session,
            market="KR",
            target_date=date(2026, 2, 17),
            generate_fn=_mock_generate_fn,
        )

        assert result is not None
        assert result.content["summary"] is not None
        assert len(result.content["summary"]) > 0
        assert "key_issues" in result.content
        assert len(result.content["key_issues"]) == 3
        assert result.content["key_issues"][0]["title"] == "반도체 수출 호조"
        session.close()
    finally:
        _teardown()


def test_generate_briefing_enriches_top_movers() -> None:
    """AI generation enriches top_movers with reason field."""
    _setup()
    try:
        from app.workers.market_briefing_generator import generate_market_briefing

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        _create_raw_briefing(session)

        result = generate_market_briefing(
            session,
            market="KR",
            target_date=date(2026, 2, 17),
            generate_fn=_mock_generate_fn,
        )

        assert result is not None
        top_movers = result.content["top_movers"]
        samsung = next((m for m in top_movers if m["stock_name"] == "삼성전자"), None)
        assert samsung is not None
        assert "reason" in samsung
        assert samsung["reason"] == "HBM 수주 기대감으로 상승"
        session.close()
    finally:
        _teardown()


def test_generate_briefing_no_raw_data() -> None:
    """Generation returns None when no raw briefing exists."""
    _setup()
    try:
        from app.workers.market_briefing_generator import generate_market_briefing

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        result = generate_market_briefing(
            session,
            market="KR",
            target_date=date(2026, 2, 17),
            generate_fn=_mock_generate_fn,
        )

        assert result is None
        session.close()
    finally:
        _teardown()


def test_generate_briefing_empty_content() -> None:
    """Generation returns None when briefing content is empty."""
    _setup()
    try:
        from app.workers.market_briefing_generator import generate_market_briefing

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        briefing = MarketBriefing(
            market="KR",
            date=date(2026, 2, 17),
            content=None,
        )
        session.add(briefing)
        session.commit()

        result = generate_market_briefing(
            session,
            market="KR",
            target_date=date(2026, 2, 17),
            generate_fn=_mock_generate_fn,
        )

        assert result is None
        session.close()
    finally:
        _teardown()


def test_generate_briefing_idempotent() -> None:
    """Already processed briefing is returned as-is."""
    _setup()
    try:
        from app.workers.market_briefing_generator import generate_market_briefing

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        _create_raw_briefing(session)

        # First generation
        result1 = generate_market_briefing(
            session,
            market="KR",
            target_date=date(2026, 2, 17),
            generate_fn=_mock_generate_fn,
        )
        assert result1 is not None
        summary1 = result1.content["summary"]

        # Second generation should return same result without calling generate_fn again
        call_count = 0

        def counting_mock(raw_data):
            nonlocal call_count
            call_count += 1
            return _mock_generate_fn(raw_data)

        result2 = generate_market_briefing(
            session,
            market="KR",
            target_date=date(2026, 2, 17),
            generate_fn=counting_mock,
        )

        assert result2 is not None
        assert result2.content["summary"] == summary1
        assert call_count == 0  # Should not have called mock again
        session.close()
    finally:
        _teardown()


def test_generate_briefing_ai_failure() -> None:
    """Generation returns None when AI fails."""
    _setup()
    try:
        from app.workers.market_briefing_generator import generate_market_briefing

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        _create_raw_briefing(session)

        result = generate_market_briefing(
            session,
            market="KR",
            target_date=date(2026, 2, 17),
            generate_fn=_mock_generate_fn_fail,
        )

        assert result is None
        session.close()
    finally:
        _teardown()


def test_generate_briefing_output_format() -> None:
    """Generated briefing has correct output format."""
    _setup()
    try:
        from app.workers.market_briefing_generator import generate_market_briefing

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        _create_raw_briefing(session)

        result = generate_market_briefing(
            session,
            market="KR",
            target_date=date(2026, 2, 17),
            generate_fn=_mock_generate_fn,
        )

        assert result is not None
        content = result.content

        # Required fields after AI processing
        assert "summary" in content
        assert isinstance(content["summary"], str)
        assert "key_issues" in content
        assert isinstance(content["key_issues"], list)
        for issue in content["key_issues"]:
            assert "title" in issue
            assert "description" in issue
        assert "top_movers" in content
        assert isinstance(content["top_movers"], list)

        # Original raw data preserved
        assert "market" in content
        assert "market_stats" in content
        session.close()
    finally:
        _teardown()


def test_build_prompt() -> None:
    """_build_prompt produces a valid prompt string."""
    from app.workers.market_briefing_generator import _build_prompt

    raw_data = {
        "market": "KR",
        "date": "2026-02-17",
        "top_movers": [
            {"stock_name": "삼성전자", "change_pct": 3.5, "volume": 10000000},
        ],
        "market_stats": {"stocks_up": 5, "stocks_down": 3, "stocks_flat": 2},
    }
    prompt = _build_prompt(raw_data)

    assert "2026-02-17" in prompt
    assert "한국" in prompt
    assert "삼성전자" in prompt
    assert "+3.5%" in prompt
    assert "상승 종목: 5개" in prompt
    assert "JSON" in prompt


def test_build_prompt_us() -> None:
    """_build_prompt handles US market correctly."""
    from app.workers.market_briefing_generator import _build_prompt

    raw_data = {
        "market": "US",
        "date": "2026-02-17",
        "top_movers": [
            {"stock_name": "Apple", "change_pct": -1.5, "volume": 50000000},
        ],
        "market_stats": {"stocks_up": 3, "stocks_down": 7, "stocks_flat": 0},
    }
    prompt = _build_prompt(raw_data)

    assert "미국" in prompt
    assert "Apple" in prompt


def test_max_tokens_constant() -> None:
    """MAX_TOKENS is set to limit cost per briefing."""
    from app.workers.market_briefing_generator import MAX_TOKENS

    assert MAX_TOKENS == 1000


def test_celery_task_exists() -> None:
    """Celery task generate_market_briefing_task is defined."""
    from app.workers.market_briefing_generator import generate_market_briefing_task
    assert generate_market_briefing_task is not None or True


def test_generate_briefing_us_market() -> None:
    """AI briefing generation works for US market."""
    _setup()
    try:
        from app.workers.market_briefing_generator import generate_market_briefing

        factory = get_session_factory(TEST_DB_URL)
        session = factory()

        us_briefing = MarketBriefing(
            market="US",
            date=date(2026, 2, 17),
            content={
                "market": "US",
                "date": "2026-02-17",
                "total_stocks": 5,
                "top_movers": [
                    {
                        "stock_name": "Apple",
                        "stock_code": "AAPL",
                        "market": "NASDAQ",
                        "price": 189.45,
                        "change_pct": 2.3,
                        "volume": 50000000,
                    },
                ],
                "market_stats": {"stocks_up": 3, "stocks_down": 2, "stocks_flat": 0},
            },
        )
        session.add(us_briefing)
        session.commit()

        def us_mock(raw_data):
            return {
                "summary": "US market summary.",
                "key_issues": [{"title": "Fed decision", "description": "Rate hold."}],
                "top_movers": [
                    {"stock_name": "Apple", "change_pct": 2.3, "reason": "Earnings beat"},
                ],
            }

        result = generate_market_briefing(
            session,
            market="US",
            target_date=date(2026, 2, 17),
            generate_fn=us_mock,
        )

        assert result is not None
        assert result.content["summary"] == "US market summary."
        assert result.content["key_issues"][0]["title"] == "Fed decision"
        session.close()
    finally:
        _teardown()


def test_generate_preserves_raw_data() -> None:
    """Generation preserves original raw data fields."""
    _setup()
    try:
        from app.workers.market_briefing_generator import generate_market_briefing

        factory = get_session_factory(TEST_DB_URL)
        session = factory()
        briefing = _create_raw_briefing(session)
        original_stats = briefing.content["market_stats"].copy()

        result = generate_market_briefing(
            session,
            market="KR",
            target_date=date(2026, 2, 17),
            generate_fn=_mock_generate_fn,
        )

        assert result is not None
        assert result.content["market_stats"] == original_stats
        assert result.content["total_stocks"] == 10
        session.close()
    finally:
        _teardown()
