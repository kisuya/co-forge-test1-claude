"""Structure tests for calendar user stock highlight (calendar-005)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Tracked highlight in monthly view (already from calendar-003) ---

def test_calendar_yellow_dot():
    """Tracked events should have yellow dot."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "bg-yellow-400" in content
    assert "is_tracked" in content


def test_calendar_tracked_badge_in_detail():
    """Tracked events should show badge in detail panel."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "calendar-tracked-badge" in content
    assert "내 관심 종목" in content


def test_calendar_tracked_highlight_bg():
    """Tracked events should have yellow background in detail."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "bg-yellow-50" in content


# --- Tracked-only filter toggle ---

def test_calendar_tracked_filter_exists():
    """Should have tracked filter section."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-tracked-filter"' in content


def test_calendar_tracked_toggle():
    """Should have tracked-only toggle checkbox."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-tracked-toggle"' in content
    assert "trackedOnly" in content


def test_calendar_tracked_toggle_label():
    """Toggle should have '내 종목만' label."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "내 종목만" in content


def test_calendar_tracked_filter_logic():
    """Should filter events by is_tracked when toggle on."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "filteredEvents" in content
    assert "trackedOnly" in content


# --- Login check for filter ---

def test_calendar_login_check():
    """Should check login status for filter."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "isLoggedIn" in content
    assert "loggedIn" in content


def test_calendar_login_prompt():
    """Should show login prompt for unauthenticated users."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-login-prompt"' in content
    assert "로그인하면 관심 종목 일정을 확인할 수 있습니다" in content


# --- Tracked filter empty state ---

def test_calendar_tracked_empty():
    """Should show empty state when filter on but no tracked events."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-tracked-empty"' in content
    assert "관심 종목 관련 이벤트가 없습니다" in content


# --- D-3 alert in widget ---

def test_calendar_widget_d3_alerts():
    """Widget should show D-3 alerts for tracked earnings."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert 'data-testid="calendar-d3-alerts"' in content
    assert 'data-testid="calendar-d3-alert"' in content


def test_calendar_widget_d3_text():
    """D-3 alert should show stock name and '실적 발표 3일 전'."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "실적 발표 3일 전" in content


def test_calendar_widget_d3_logic():
    """D-3 should check earnings type and 3-day window."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "d3Alerts" in content
    assert "earnings" in content
    assert "is_tracked" in content


def test_calendar_widget_d3_styling():
    """D-3 alert should have warning styling."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "bg-yellow-50" in content
    assert "border-yellow-200" in content
