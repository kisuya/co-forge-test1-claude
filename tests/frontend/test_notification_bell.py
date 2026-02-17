"""Structure tests for header notification bell (ui-022)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Component exists ---


def test_notification_bell_component_exists():
    """NotificationBell component should exist."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    assert os.path.exists(path), "NotificationBell.tsx should exist"


def test_notification_bell_is_client_component():
    """NotificationBell should be a client component."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Bell icon ---


def test_has_bell_icon():
    """Should have bell icon button."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert 'data-testid="notification-bell"' in content
    assert "🔔" in content


def test_bell_icon_size():
    """Bell icon should be visible size."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert "w-8" in content
    assert "h-8" in content


# --- Unread dot ---


def test_has_unread_dot():
    """Should have unread notification dot."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert 'data-testid="notification-unread-dot"' in content
    assert "bg-red-500" in content
    assert "rounded-full" in content


def test_unread_dot_size():
    """Unread dot should be 8px (w-2 h-2)."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert "w-2" in content
    assert "h-2" in content


# --- Dropdown ---


def test_has_dropdown():
    """Should have notification dropdown."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert 'data-testid="notification-dropdown"' in content


def test_dropdown_width():
    """Dropdown should be 300px wide."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert "300px" in content


def test_has_notification_items():
    """Should have notification item links."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert 'data-testid="notification-item"' in content
    assert "/reports/" in content


def test_notification_shows_stock_name():
    """Notification item should show stock name."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert "stock_name" in content


def test_notification_shows_change_pct():
    """Notification item should show change percentage."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert "change_pct" in content


# --- Empty state ---


def test_has_empty_state():
    """Should show empty message when no notifications."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert 'data-testid="notification-empty"' in content
    assert "새로운 알림이 없습니다" in content


# --- View all link ---


def test_has_view_all_link():
    """Should have 'view all' link."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert 'data-testid="notification-view-all"' in content
    assert "모든 알림 보기" in content
    assert "/notifications" in content


# --- Outside click ---


def test_outside_click_closes():
    """Dropdown should close on outside click."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert "mousedown" in content
    assert "handleClickOutside" in content


# --- API call ---


def test_fetches_notifications_api():
    """Should fetch from /api/notifications."""
    path = os.path.join(BASE, "components", "NotificationBell.tsx")
    content = open(path).read()
    assert "/api/notifications" in content
    assert "limit=5" in content


# --- Header integration ---


def test_header_uses_notification_bell():
    """GlobalHeader should import and use NotificationBell."""
    path = os.path.join(BASE, "components", "GlobalHeader.tsx")
    content = open(path).read()
    assert "NotificationBell" in content
