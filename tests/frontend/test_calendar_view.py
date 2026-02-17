"""Structure tests for market calendar monthly view UI (calendar-003)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def _read(path: str) -> str:
    with open(path) as f:
        return f.read()


# --- Page existence ---

def test_calendar_page_exists():
    """Calendar page should exist at /calendar."""
    path = os.path.join(BASE, "app", "calendar", "page.tsx")
    assert os.path.isfile(path)


def test_calendar_page_is_client_component():
    """Calendar page must be a client component."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert '"use client"' in content


# --- Page title ---

def test_calendar_page_title():
    """Should have page title."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "마켓 캘린더" in content
    assert 'data-testid="calendar-page-title"' in content


def test_calendar_document_title():
    """Should set document title."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "document.title" in content
    assert "oh-my-stock" in content


# --- Month navigation ---

def test_calendar_navigation():
    """Should have month navigation."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-nav"' in content
    assert 'data-testid="calendar-prev"' in content
    assert 'data-testid="calendar-next"' in content


def test_calendar_month_label():
    """Should show current month label."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-month-label"' in content
    assert "년" in content
    assert "월" in content


# --- Calendar grid ---

def test_calendar_grid():
    """Should have 7-column calendar grid."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-grid"' in content
    assert "grid-cols-7" in content


def test_calendar_day_names():
    """Should show Korean day names."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    for day in ["월", "화", "수", "목", "금", "토", "일"]:
        assert day in content


def test_calendar_date_cells():
    """Should have clickable date cells."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-date-cell"' in content
    assert "setSelectedDate" in content


# --- Today highlight ---

def test_calendar_today_highlight():
    """Should highlight today's date."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "calendar-today" in content
    assert "bg-blue-600" in content
    assert "todayStr" in content


# --- Event dots ---

def test_calendar_event_dots():
    """Should show event dots on dates with events."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-event-dots"' in content
    assert 'data-testid="calendar-dot"' in content


def test_calendar_dot_colors():
    """Should have different colors per event type."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "bg-green-500" in content  # earnings
    assert "bg-blue-500" in content   # economic
    assert "bg-red-500" in content    # central_bank
    assert "bg-purple-500" in content # dividend


def test_calendar_tracked_dot():
    """Tracked stock events should have yellow dot."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "bg-yellow-400" in content
    assert "is_tracked" in content


# --- Market tabs ---

def test_calendar_market_tabs():
    """Should have market filter tabs."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-market-tabs"' in content
    assert "전체" in content
    assert "한국" in content
    assert "미국" in content
    assert "marketFilter" in content


# --- Date click / event detail ---

def test_calendar_detail_panel():
    """Should have event detail panel."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-detail-panel"' in content


def test_calendar_event_list():
    """Should have event list in detail panel."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-event-list"' in content
    assert 'data-testid="calendar-event-item"' in content


def test_calendar_event_type_badge():
    """Should show event type badge."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-event-type-badge"' in content
    assert "실적" in content
    assert "경제" in content
    assert "금리" in content
    assert "배당" in content


def test_calendar_event_title():
    """Should show event title."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-event-title"' in content
    assert "title" in content


def test_calendar_no_events():
    """Should show empty state for date with no events."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-no-events"' in content
    assert "예정된 이벤트가 없습니다" in content


def test_calendar_tracked_badge():
    """Should show tracked stock badge."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-tracked-badge"' in content
    assert "내 관심 종목" in content


def test_calendar_tracked_highlight():
    """Tracked stock events should have yellow highlight."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "bg-yellow-50" in content


# --- Error state ---

def test_calendar_error():
    """Should show error state."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-error"' in content
    assert "캘린더를 불러올 수 없습니다" in content


def test_calendar_retry():
    """Should have retry button."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert 'data-testid="calendar-retry"' in content
    assert "다시 시도" in content


# --- Loading state ---

def test_calendar_skeleton():
    """Should show skeleton during loading."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "Skeleton" in content
    assert 'data-testid="calendar-skeleton"' in content


# --- API integration ---

def test_calendar_uses_api():
    """Should use calendarApi."""
    content = _read(os.path.join(BASE, "app", "calendar", "page.tsx"))
    assert "calendarApi" in content


def test_calendar_api_exists():
    """queries.ts should have calendarApi."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "calendarApi" in content
    assert "/api/calendar" in content


def test_calendar_api_list_method():
    """calendarApi should have list method with date params."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "start_date" in content
    assert "end_date" in content


def test_calendar_api_week_method():
    """calendarApi should have getWeek method."""
    content = _read(os.path.join(BASE, "lib", "queries.ts"))
    assert "getWeek" in content
    assert "/api/calendar/week" in content


# --- Types ---

def test_calendar_types_exist():
    """types/index.ts should have CalendarEvent type."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "CalendarEvent" in content


def test_calendar_type_fields():
    """CalendarEvent should have required fields."""
    content = _read(os.path.join(BASE, "types", "index.ts"))
    assert "event_type" in content
    assert "event_date" in content
    assert "is_tracked" in content
    assert "stock_name" in content
