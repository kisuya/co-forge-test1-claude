"""Tests for Alembic migration setup (fix-002).

Verifies that:
- Alembic directory structure exists
- env.py reads DATABASE_URL from environment
- Initial migration creates all tables
- Downgrade removes all tables
"""
from __future__ import annotations

import os
import sys

import pytest

# Ensure backend app is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

# Set JWT secret before any app imports
os.environ.setdefault(
    "JWT_SECRET_KEY",
    "test-secret-key-for-ohmystock-must-be-at-least-32-bytes-long",
)

BACKEND_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
ALEMBIC_DIR = os.path.join(BACKEND_DIR, "alembic")


def test_alembic_ini_exists():
    """alembic.ini should exist in backend/."""
    assert os.path.isfile(os.path.join(BACKEND_DIR, "alembic.ini"))


def test_alembic_directory_exists():
    """alembic/ directory should exist in backend/."""
    assert os.path.isdir(ALEMBIC_DIR)


def test_alembic_env_py_exists():
    """alembic/env.py should exist."""
    assert os.path.isfile(os.path.join(ALEMBIC_DIR, "env.py"))


def test_alembic_versions_directory_exists():
    """alembic/versions/ directory should exist."""
    assert os.path.isdir(os.path.join(ALEMBIC_DIR, "versions"))


def test_alembic_env_reads_database_url():
    """env.py should read DATABASE_URL from environment."""
    env_path = os.path.join(ALEMBIC_DIR, "env.py")
    content = open(env_path).read()
    assert "DATABASE_URL" in content
    assert "os.getenv" in content


def test_alembic_env_imports_base_metadata():
    """env.py should import Base metadata for autogenerate."""
    env_path = os.path.join(ALEMBIC_DIR, "env.py")
    content = open(env_path).read()
    assert "from app.db.database import Base" in content
    assert "target_metadata = Base.metadata" in content


def test_alembic_env_imports_models():
    """env.py should import models so Base.metadata is populated."""
    env_path = os.path.join(ALEMBIC_DIR, "env.py")
    content = open(env_path).read()
    assert "import app.models" in content


def test_initial_migration_exists():
    """At least one migration file should exist in versions/."""
    versions_dir = os.path.join(ALEMBIC_DIR, "versions")
    migration_files = [
        f for f in os.listdir(versions_dir)
        if f.endswith(".py") and not f.startswith("__")
    ]
    assert len(migration_files) >= 1, "Should have at least one migration file"


def test_initial_migration_has_all_tables():
    """Initial migration should create all model tables."""
    versions_dir = os.path.join(ALEMBIC_DIR, "versions")
    migration_files = [
        f for f in os.listdir(versions_dir)
        if f.endswith(".py") and not f.startswith("__")
    ]
    content = open(os.path.join(versions_dir, migration_files[0])).read()

    expected_tables = [
        "users",
        "stocks",
        "watchlists",
        "price_snapshots",
        "reports",
        "report_sources",
        "shared_reports",
        "discussions",
        "discussion_comments",
        "push_subscriptions",
        "market_briefings",
        "news_articles",
        "calendar_events",
    ]
    for table in expected_tables:
        assert f"'{table}'" in content, f"Migration should include {table} table"


def test_initial_migration_has_downgrade():
    """Initial migration should have a downgrade function."""
    versions_dir = os.path.join(ALEMBIC_DIR, "versions")
    migration_files = [
        f for f in os.listdir(versions_dir)
        if f.endswith(".py") and not f.startswith("__")
    ]
    content = open(os.path.join(versions_dir, migration_files[0])).read()
    assert "def downgrade()" in content


def test_alembic_upgrade_creates_tables():
    """alembic upgrade head should create all tables in an empty database."""
    from sqlalchemy import create_engine, inspect

    test_db_url = "sqlite:///test_alembic_upgrade.db"
    os.environ["DATABASE_URL"] = test_db_url

    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)

        command.upgrade(alembic_cfg, "head")

        engine = create_engine(test_db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        expected = [
            "users", "stocks", "watchlists", "price_snapshots",
            "reports", "report_sources", "shared_reports",
            "discussions", "discussion_comments",
            "push_subscriptions", "market_briefings",
            "news_articles", "calendar_events",
        ]
        for table in expected:
            assert table in tables, f"Table {table} should exist after upgrade"

        engine.dispose()
    finally:
        if os.path.exists("test_alembic_upgrade.db"):
            os.remove("test_alembic_upgrade.db")


def test_alembic_downgrade_removes_tables():
    """alembic downgrade -1 should remove tables."""
    from sqlalchemy import create_engine, inspect

    test_db_url = "sqlite:///test_alembic_downgrade.db"
    os.environ["DATABASE_URL"] = test_db_url

    try:
        from alembic.config import Config
        from alembic import command

        alembic_cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
        alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)

        # First upgrade
        command.upgrade(alembic_cfg, "head")

        # Then downgrade
        command.downgrade(alembic_cfg, "-1")

        engine = create_engine(test_db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()

        # Only alembic_version should remain (or nothing)
        user_tables = [t for t in tables if t != "alembic_version"]
        assert len(user_tables) == 0, f"All tables should be removed: {user_tables}"

        engine.dispose()
    finally:
        if os.path.exists("test_alembic_downgrade.db"):
            os.remove("test_alembic_downgrade.db")


def test_alembic_ini_no_hardcoded_url():
    """alembic.ini should not have a hardcoded database URL."""
    ini_path = os.path.join(BACKEND_DIR, "alembic.ini")
    content = open(ini_path).read()
    # Should not have a real database URL
    assert "driver://user:pass@localhost/dbname" not in content
