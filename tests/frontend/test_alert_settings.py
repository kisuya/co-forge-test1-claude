"""Structure tests for alert settings UI and service worker (alert-003)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
PUBLIC = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public")


# --- Service Worker ---


def test_service_worker_exists():
    """public/sw.js should exist."""
    path = os.path.join(PUBLIC, "sw.js")
    assert os.path.isfile(path)


def test_service_worker_has_push_listener():
    """sw.js should listen for push events."""
    path = os.path.join(PUBLIC, "sw.js")
    content = open(path).read()
    assert "push" in content
    assert "showNotification" in content


def test_service_worker_has_notification_click():
    """sw.js should handle notification click to navigate."""
    path = os.path.join(PUBLIC, "sw.js")
    content = open(path).read()
    assert "notificationclick" in content
    assert "navigate" in content or "openWindow" in content


def test_service_worker_parses_json_payload():
    """sw.js should parse push event data as JSON."""
    path = os.path.join(PUBLIC, "sw.js")
    content = open(path).read()
    assert "json()" in content or "data.json" in content


# --- NotificationPanel component ---


def test_notification_panel_exists():
    """NotificationPanel component should exist."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    assert os.path.isfile(path)


def test_notification_panel_has_bell_icon():
    """NotificationPanel should have a bell icon button."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "notification-bell" in content


def test_notification_panel_has_side_panel():
    """NotificationPanel should have a side panel with slide animation."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "notification-panel" in content
    assert "animate-slide-left" in content or "slide" in content


def test_notification_panel_has_global_toggle():
    """NotificationPanel should have a global ON/OFF toggle."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "global-toggle" in content


def test_notification_panel_requests_permission():
    """NotificationPanel should request Notification permission."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "requestPermission" in content
    assert "Notification" in content


def test_notification_panel_has_permission_denied_message():
    """NotificationPanel should show message when permission denied."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "브라우저 설정에서 알림을 허용해주세요" in content
    assert "perm-denied-msg" in content


def test_notification_panel_calls_subscribe_api():
    """NotificationPanel should call pushApi.subscribe."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "pushApi" in content
    assert "subscribe" in content


def test_notification_panel_calls_unsubscribe_api():
    """NotificationPanel should call pushApi.unsubscribe."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "unsubscribe" in content


def test_notification_panel_has_stock_toggles():
    """NotificationPanel should display per-stock toggles."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "stock-toggles" in content
    assert "stock-toggle-" in content


def test_notification_panel_has_offline_indicator():
    """NotificationPanel should show offline indicator."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "offline-indicator" in content
    assert "오프라인 상태입니다" in content


def test_notification_panel_has_close_button():
    """NotificationPanel should have a close button."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "notification-close" in content


def test_notification_panel_registers_service_worker():
    """NotificationPanel should register /sw.js."""
    path = os.path.join(BASE, "components", "NotificationPanel.tsx")
    content = open(path).read()
    assert "serviceWorker.register" in content
    assert "sw.js" in content


# --- Dashboard integration ---


def test_dashboard_includes_notification_panel():
    """Dashboard should import and render NotificationPanel."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "NotificationPanel" in content


def test_dashboard_has_bell_in_header():
    """Dashboard header nav should include NotificationPanel."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "NotificationPanel" in content
    assert "<nav" in content


# --- Push API queries ---


def test_queries_has_push_api():
    """queries.ts should export pushApi."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "pushApi" in content
    assert "subscribe" in content
    assert "unsubscribe" in content
    assert "status" in content


def test_queries_push_status_interface():
    """queries.ts should have PushStatus interface."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "PushStatus" in content
    assert "subscribed" in content
    assert "endpoint_count" in content


# --- CSS animation ---


def test_globals_css_has_slide_left_animation():
    """globals.css should define slide-left animation for notification panel."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "slide-left" in content
    assert "@keyframes" in content
