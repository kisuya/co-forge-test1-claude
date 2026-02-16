"""Tests for similar case matching engine (case-001)."""
from __future__ import annotations

import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.report import PriceSnapshot
from app.models.stock import Stock
from app.services.similar_case_service import (
    CHANGE_RANGE,
    CHANGE_WEIGHT,
    DEDUP_DAYS,
    MAX_RESULTS,
    MIN_DAYS_AGO,
    VOLUME_WEIGHT,
    SimilarCase,
    _compute_similarity,
    _dedup_consecutive,
    find_similar_cases,
)

TEST_DB_URL = "sqlite:///test_case_matching.db"


def _setup() -> Session:
    create_tables(TEST_DB_URL)
    factory = get_session_factory(TEST_DB_URL)
    return factory()


def _teardown(session: Session) -> None:
    session.close()
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_case_matching.db"):
        os.remove("test_case_matching.db")


def _add_stock(session: Session, code: str = "005930") -> Stock:
    stock = Stock(code=code, name="Test", market="KRX")
    session.add(stock)
    session.flush()
    return stock


def _add_snapshot(
    session: Session,
    stock: Stock,
    change_pct: float,
    days_ago: int,
    volume: int = 100000,
) -> PriceSnapshot:
    snap = PriceSnapshot(
        stock_id=stock.id,
        price=Decimal("50000"),
        change_pct=change_pct,
        volume=volume,
        captured_at=datetime.utcnow() - timedelta(days=days_ago),
    )
    session.add(snap)
    session.flush()
    return snap


# --- Constants ---


def test_change_range_is_1_5():
    assert CHANGE_RANGE == 1.5


def test_min_days_ago_is_30():
    assert MIN_DAYS_AGO == 30


def test_max_results_is_3():
    assert MAX_RESULTS == 3


def test_dedup_days_is_2():
    assert DEDUP_DAYS == 2


def test_weight_sum_is_1():
    assert CHANGE_WEIGHT + VOLUME_WEIGHT == pytest.approx(1.0)


# --- SimilarCase dataclass ---


def test_similar_case_fields():
    sc = SimilarCase(
        date=datetime.utcnow(),
        change_pct=5.0,
        volume=100000,
        similarity_score=0.5,
    )
    assert sc.change_pct == 5.0
    assert sc.volume == 100000
    assert sc.similarity_score == 0.5


# --- _compute_similarity ---


def test_compute_similarity_identical():
    """Identical values should give 0 similarity score."""
    score = _compute_similarity(5.0, 100000, 5.0, 100000)
    assert score == pytest.approx(0.0)


def test_compute_similarity_change_only():
    """Only change_pct differs: score = diff * 0.6."""
    score = _compute_similarity(5.0, 100000, 6.0, 100000)
    expected = 1.0 * CHANGE_WEIGHT + 0.0 * VOLUME_WEIGHT
    assert score == pytest.approx(expected)


def test_compute_similarity_volume_only():
    """Only volume differs: score includes volume ratio diff."""
    score = _compute_similarity(5.0, 100000, 5.0, 50000)
    vol_diff = abs(1.0 - 50000 / 100000)
    expected = 0.0 * CHANGE_WEIGHT + vol_diff * VOLUME_WEIGHT
    assert score == pytest.approx(expected)


# --- find_similar_cases ---


def test_find_empty_db_returns_empty():
    """Empty DB should return empty list, not error."""
    session = _setup()
    try:
        stock = _add_stock(session)
        session.commit()
        result = find_similar_cases(session, str(stock.id), 5.0)
        assert result == []
    finally:
        _teardown(session)


def test_find_returns_matching_cases():
    """Should return cases within ±1.5%p range."""
    session = _setup()
    try:
        stock = _add_stock(session)
        _add_snapshot(session, stock, 5.5, days_ago=60)
        _add_snapshot(session, stock, 4.0, days_ago=90)
        session.commit()
        result = find_similar_cases(session, str(stock.id), 5.0)
        assert len(result) == 2
    finally:
        _teardown(session)


def test_find_excludes_recent_data():
    """Data from less than 30 days ago should be excluded."""
    session = _setup()
    try:
        stock = _add_stock(session)
        _add_snapshot(session, stock, 5.0, days_ago=10)  # too recent
        _add_snapshot(session, stock, 5.0, days_ago=60)  # old enough
        session.commit()
        result = find_similar_cases(session, str(stock.id), 5.0)
        assert len(result) == 1
    finally:
        _teardown(session)


def test_find_excludes_out_of_range():
    """Cases outside ±1.5%p should be excluded."""
    session = _setup()
    try:
        stock = _add_stock(session)
        _add_snapshot(session, stock, 10.0, days_ago=60)  # too far
        _add_snapshot(session, stock, 5.5, days_ago=60)  # in range
        session.commit()
        result = find_similar_cases(session, str(stock.id), 5.0)
        assert len(result) == 1
        assert result[0].change_pct == pytest.approx(5.5)
    finally:
        _teardown(session)


def test_find_max_3_results():
    """Should return at most 3 results."""
    session = _setup()
    try:
        stock = _add_stock(session)
        for i in range(10):
            _add_snapshot(session, stock, 5.0 + i * 0.1, days_ago=40 + i * 5)
        session.commit()
        result = find_similar_cases(session, str(stock.id), 5.0)
        assert len(result) <= MAX_RESULTS
    finally:
        _teardown(session)


def test_find_sorted_by_similarity():
    """Results should be sorted by similarity (most similar first)."""
    session = _setup()
    try:
        stock = _add_stock(session)
        _add_snapshot(session, stock, 6.0, days_ago=60, volume=100000)
        _add_snapshot(session, stock, 5.1, days_ago=90, volume=100000)
        session.commit()
        result = find_similar_cases(
            session, str(stock.id), 5.0, reference_volume=100000,
        )
        assert len(result) == 2
        assert result[0].similarity_score <= result[1].similarity_score
    finally:
        _teardown(session)


def test_find_dedup_consecutive_days():
    """Consecutive-day events (±2 days) should be deduped."""
    session = _setup()
    try:
        stock = _add_stock(session)
        _add_snapshot(session, stock, 5.0, days_ago=60)
        _add_snapshot(session, stock, 5.1, days_ago=61)  # within 2 days
        _add_snapshot(session, stock, 5.2, days_ago=100)  # separate event
        session.commit()
        result = find_similar_cases(session, str(stock.id), 5.0)
        assert len(result) == 2  # deduped: 60/61 → 1 + 100 → 1
    finally:
        _teardown(session)


def test_find_exclude_date():
    """Should exclude events near the exclude_date."""
    session = _setup()
    try:
        stock = _add_stock(session)
        snap = _add_snapshot(session, stock, 5.0, days_ago=60)
        _add_snapshot(session, stock, 5.0, days_ago=120)
        session.commit()
        exclude = snap.captured_at
        result = find_similar_cases(
            session, str(stock.id), 5.0, exclude_date=exclude,
        )
        assert len(result) == 1
    finally:
        _teardown(session)


def test_find_different_stock_ignored():
    """Cases from other stocks should not appear."""
    session = _setup()
    try:
        stock_a = _add_stock(session, code="005930")
        stock_b = _add_stock(session, code="000660")
        _add_snapshot(session, stock_a, 5.0, days_ago=60)
        _add_snapshot(session, stock_b, 5.0, days_ago=60)
        session.commit()
        result = find_similar_cases(session, str(stock_a.id), 5.0)
        assert len(result) == 1
    finally:
        _teardown(session)


def test_find_returns_similarity_score():
    """Each result should have a non-negative similarity_score."""
    session = _setup()
    try:
        stock = _add_stock(session)
        _add_snapshot(session, stock, 5.2, days_ago=60)
        session.commit()
        result = find_similar_cases(session, str(stock.id), 5.0)
        assert len(result) == 1
        assert result[0].similarity_score >= 0
    finally:
        _teardown(session)


# --- _dedup_consecutive ---


def test_dedup_empty_returns_empty():
    assert _dedup_consecutive([]) == []
