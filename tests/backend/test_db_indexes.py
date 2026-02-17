"""Tests for database indexing optimization (quality-004)."""
from __future__ import annotations

import os

from sqlalchemy import text

from app.db.database import Base, create_tables, get_engine

# Import models so Base.metadata knows about all tables
from app.models import PriceSnapshot, Report, Stock, User, Watchlist  # noqa: F401

TEST_DB_URL = "sqlite:///test_db_indexes.db"


def _setup() -> None:
    create_tables(TEST_DB_URL)


def _teardown() -> None:
    engine = get_engine(TEST_DB_URL)
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("test_db_indexes.db"):
        os.remove("test_db_indexes.db")


def _get_raw_indexes() -> list[tuple]:
    """Get all indexes from sqlite_master."""
    engine = get_engine(TEST_DB_URL)
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT name, sql FROM sqlite_master WHERE type='index'")
        )
        return list(result)


def _get_index_names() -> list[str]:
    return [row[0] for row in _get_raw_indexes()]


def test_watchlist_user_stock_unique_constraint() -> None:
    """watchlist should have UNIQUE constraint on (user_id, stock_id)."""
    _setup()
    try:
        # SQLite creates autoindex for unique constraints
        names = _get_index_names()
        has_unique = any("watchlist" in n and "autoindex" in n for n in names)
        assert has_unique, f"No unique autoindex found for watchlists. Indexes: {names}"
    finally:
        _teardown()


def test_watchlist_stock_id_index() -> None:
    """watchlist should have standalone index on stock_id for tracking count queries."""
    _setup()
    try:
        names = _get_index_names()
        assert "ix_watchlists_stock_id" in names, f"Missing ix_watchlists_stock_id. Indexes: {names}"
    finally:
        _teardown()


def test_price_snapshots_composite_index() -> None:
    """price_snapshots should have composite index on (stock_id, captured_at)."""
    _setup()
    try:
        indexes = _get_raw_indexes()
        found = False
        for name, sql in indexes:
            if name == "ix_price_snapshots_stock_captured":
                assert "stock_id" in sql
                assert "captured_at" in sql
                found = True
                break
        assert found, f"Index ix_price_snapshots_stock_captured not found. Indexes: {[r[0] for r in indexes]}"
    finally:
        _teardown()


def test_reports_composite_index() -> None:
    """reports should have composite index on (stock_id, status, created_at)."""
    _setup()
    try:
        indexes = _get_raw_indexes()
        found = False
        for name, sql in indexes:
            if name == "ix_reports_stock_status_created":
                assert "stock_id" in sql
                assert "status" in sql
                assert "created_at" in sql
                found = True
                break
        assert found, f"Index ix_reports_stock_status_created not found. Indexes: {[r[0] for r in indexes]}"
    finally:
        _teardown()


def test_create_tables_idempotent() -> None:
    """Running create_tables twice should not raise errors (duplicate index safety)."""
    _setup()
    try:
        # Second call should not fail
        create_tables(TEST_DB_URL)
    finally:
        _teardown()
