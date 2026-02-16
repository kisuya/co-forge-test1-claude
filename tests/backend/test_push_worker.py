"""Tests for push notification worker (alert-002)."""
from __future__ import annotations

import os
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.db.database import Base, create_tables, get_engine, get_session_factory
from app.models.push_subscription import PushSubscription
from app.models.stock import Stock
from app.models.user import User
from app.models.watchlist import Watchlist
from app.services.push_service import (
    MAX_RETRIES,
    PushResult,
    _build_payload,
    send_spike_notifications,
)

TEST_DB_URL = "sqlite:///test_push_worker.db"


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
    if os.path.exists("test_push_worker.db"):
        os.remove("test_push_worker.db")


def _create_user(session: Session, email: str = "push@test.com") -> User:
    import bcrypt
    user = User(
        email=email,
        password_hash=bcrypt.hashpw(b"pass123", bcrypt.gensalt()).decode(),
    )
    session.add(user)
    session.flush()
    return user


def _create_stock(session: Session, code: str = "005930", name: str = "삼성전자") -> Stock:
    stock = Stock(code=code, name=name, market="KRX")
    session.add(stock)
    session.flush()
    return stock


def _create_watchlist(session: Session, user: User, stock: Stock) -> Watchlist:
    wl = Watchlist(user_id=user.id, stock_id=stock.id, threshold=3.0)
    session.add(wl)
    session.flush()
    return wl


def _create_subscription(
    session: Session, user: User, endpoint: str = "https://push.example.com/sub1"
) -> PushSubscription:
    sub = PushSubscription(
        user_id=user.id,
        endpoint=endpoint,
        p256dh="key123",
        auth="auth123",
        is_active=True,
    )
    session.add(sub)
    session.flush()
    return sub


# --- Payload tests ---


def test_build_payload_positive_change() -> None:
    """Payload should include stock name, positive sign, and URL."""
    payload = _build_payload("삼성전자", "005930", 5.2, "abc-123")
    import json
    data = json.loads(payload)
    assert "삼성전자" in data["title"]
    assert "+5.2%" in data["title"]
    assert data["url"] == "/reports/stock/abc-123"
    assert "급변동" in data["body"]


def test_build_payload_negative_change() -> None:
    """Payload should handle negative changes."""
    payload = _build_payload("카카오", "035720", -4.5, "def-456")
    import json
    data = json.loads(payload)
    assert "카카오" in data["title"]
    assert "-4.5%" in data["title"]


# --- send_spike_notifications tests ---


def test_no_watchers_returns_empty() -> None:
    """No watchers for the stock should return empty result."""
    session = _setup()
    try:
        stock = _create_stock(session)
        session.commit()
        result = send_spike_notifications(session, str(stock.id), 5.0)
        assert result.success == 0
        assert result.failed == 0
        assert result.expired == 0
    finally:
        _teardown(session)


def test_no_active_subscriptions_returns_empty() -> None:
    """Watchers without active subscriptions should get no pushes."""
    session = _setup()
    try:
        user = _create_user(session)
        stock = _create_stock(session)
        _create_watchlist(session, user, stock)
        session.commit()
        result = send_spike_notifications(session, str(stock.id), 5.0)
        assert result.success == 0
    finally:
        _teardown(session)


def test_successful_push_notification() -> None:
    """Successful push should count as success."""
    session = _setup()
    try:
        user = _create_user(session)
        stock = _create_stock(session)
        _create_watchlist(session, user, stock)
        _create_subscription(session, user)
        session.commit()

        sent = []
        def mock_send(sub: PushSubscription, payload: str) -> None:
            sent.append(payload)

        result = send_spike_notifications(session, str(stock.id), 5.0, send_fn=mock_send)
        assert result.success == 1
        assert result.failed == 0
        assert len(sent) == 1
    finally:
        _teardown(session)


def test_multiple_users_get_notifications() -> None:
    """Multiple users watching same stock should all get pushes."""
    session = _setup()
    try:
        stock = _create_stock(session)
        user1 = _create_user(session, "user1@test.com")
        user2 = _create_user(session, "user2@test.com")
        _create_watchlist(session, user1, stock)
        _create_watchlist(session, user2, stock)
        _create_subscription(session, user1, "https://push.example.com/u1")
        _create_subscription(session, user2, "https://push.example.com/u2")
        session.commit()

        sent = []
        def mock_send(sub: PushSubscription, payload: str) -> None:
            sent.append(sub.endpoint)

        result = send_spike_notifications(session, str(stock.id), 5.0, send_fn=mock_send)
        assert result.success == 2
        assert len(sent) == 2
    finally:
        _teardown(session)


def test_expired_subscription_deactivated() -> None:
    """HTTP 410 response should deactivate the subscription."""
    session = _setup()
    try:
        user = _create_user(session)
        stock = _create_stock(session)
        _create_watchlist(session, user, stock)
        sub = _create_subscription(session, user)
        session.commit()
        sub_id = sub.id

        class GoneError(Exception):
            def __init__(self) -> None:
                self.response = type("R", (), {"status_code": 410})()

        def mock_send_gone(sub: PushSubscription, payload: str) -> None:
            raise GoneError()

        result = send_spike_notifications(session, str(stock.id), 5.0, send_fn=mock_send_gone)
        assert result.expired == 1
        assert result.success == 0

        refreshed = session.query(PushSubscription).filter_by(id=sub_id).first()
        assert refreshed is not None
        assert refreshed.is_active is False
    finally:
        _teardown(session)


def test_failed_push_retries() -> None:
    """Failed push should retry MAX_RETRIES times."""
    session = _setup()
    try:
        user = _create_user(session)
        stock = _create_stock(session)
        _create_watchlist(session, user, stock)
        _create_subscription(session, user)
        session.commit()

        attempts = []
        def mock_send_fail(sub: PushSubscription, payload: str) -> None:
            attempts.append(1)
            raise ConnectionError("Network error")

        with patch("app.services.push_service.time.sleep"):
            result = send_spike_notifications(session, str(stock.id), 5.0, send_fn=mock_send_fail)
        assert result.failed == 1
        assert len(attempts) == MAX_RETRIES
    finally:
        _teardown(session)


def test_inactive_subscriptions_skipped() -> None:
    """Inactive subscriptions should not receive pushes."""
    session = _setup()
    try:
        user = _create_user(session)
        stock = _create_stock(session)
        _create_watchlist(session, user, stock)
        sub = _create_subscription(session, user)
        sub.is_active = False
        session.commit()

        sent = []
        def mock_send(sub: PushSubscription, payload: str) -> None:
            sent.append(1)

        result = send_spike_notifications(session, str(stock.id), 5.0, send_fn=mock_send)
        assert result.success == 0
        assert len(sent) == 0
    finally:
        _teardown(session)


def test_nonexistent_stock_returns_empty() -> None:
    """Non-existent stock ID should return empty result."""
    session = _setup()
    try:
        result = send_spike_notifications(session, str(uuid.uuid4()), 5.0)
        assert result.success == 0
    finally:
        _teardown(session)


# --- Celery task existence ---


def test_celery_task_registered() -> None:
    """send_spike_push should be a registered Celery task."""
    celery = pytest.importorskip("celery")
    from app.workers.push_worker import send_spike_push
    assert hasattr(send_spike_push, "delay")
    assert send_spike_push.name == "send_spike_push"


# --- Constants ---


def test_max_retries_is_3() -> None:
    """MAX_RETRIES should be 3."""
    assert MAX_RETRIES == 3
