"""Structure tests for dashboard week events widget (calendar-004)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Component existence ---

def test_calendar_widget_exists():
    """CalendarWidget component should exist."""
    path = os.path.join(BASE, "components", "CalendarWidget.tsx")
    assert os.path.isfile(path)


def test_calendar_widget_is_client_component():
    """CalendarWidget must be a client component."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert '"use client"' in content


# --- Dashboard integration ---

def test_dashboard_imports_calendar_widget():
    """Dashboard page should import CalendarWidget."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    assert "CalendarWidget" in content


def test_dashboard_renders_calendar_widget():
    """Dashboard should render CalendarWidget."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    assert "<CalendarWidget" in content


def test_dashboard_widget_between_briefing_and_news():
    """CalendarWidget should be between BriefingCard and NewsWidget."""
    content = _read(os.path.join(BASE, "app", "dashboard", "page.tsx"))
    briefing_pos = content.index("BriefingCard")
    calendar_pos = content.index("CalendarWidget", briefing_pos)
    news_pos = content.index("NewsWidget", calendar_pos)
    assert briefing_pos < calendar_pos < news_pos


# --- Widget structure ---

def test_calendar_widget_testid():
    """Should have calendar-widget testid."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert 'data-testid="calendar-widget"' in content


def test_calendar_widget_title():
    """Should have week events title."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "이번 주 주요 일정" in content


# --- API integration ---

def test_calendar_widget_uses_api():
    """Should use calendarApi.getWeek."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "calendarApi" in content
    assert "getWeek" in content


# --- Event list ---

def test_calendar_widget_list():
    """Should have event list."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert 'data-testid="calendar-widget-list"' in content


def test_calendar_widget_item():
    """Should have event items."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert 'data-testid="calendar-widget-item"' in content


# --- Date formatting ---

def test_calendar_widget_date_display():
    """Should show date in M/D (dayname) format."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert 'data-testid="calendar-widget-date"' in content
    assert "formatEventDate" in content


def test_calendar_widget_day_names():
    """Should have Korean day names."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    for day in ["월", "화", "수", "목", "금", "토", "일"]:
        assert day in content


# --- Event type icons ---

def test_calendar_widget_type_icons():
    """Should have event type icons."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "EVENT_TYPE_ICONS" in content
    assert "earnings" in content
    assert "economic" in content
    assert "central_bank" in content
    assert "dividend" in content


# --- Tracked stock ---

def test_calendar_widget_tracked():
    """Should show star for tracked events."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert 'data-testid="calendar-widget-tracked"' in content
    assert "is_tracked" in content


# --- Max items ---

def test_calendar_widget_max_seven():
    """Should limit to 7 items."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "slice(0, 7)" in content


def test_calendar_widget_more_link():
    """Should show 'more' link when exceeding 7."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "캘린더에서 더보기" in content
    assert 'data-testid="calendar-widget-more"' in content
    assert "/calendar" in content


# --- Empty state ---

def test_calendar_widget_empty():
    """Should show empty state."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert 'data-testid="calendar-widget-empty"' in content
    assert "이번 주 예정된 이벤트가 없습니다" in content


# --- Sorting ---

def test_calendar_widget_sorted():
    """Events should be sorted by date."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "sort" in content
    assert "event_date" in content


# --- Event title ---

def test_calendar_widget_shows_title():
    """Should display event title."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "evt.title" in content or "title" in content


# --- Calendar link ---

def test_calendar_widget_calendar_link():
    """Should have link to calendar page."""
    content = _read(os.path.join(BASE, "components", "CalendarWidget.tsx"))
    assert "/calendar" in content
