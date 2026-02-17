"""Structure tests for event timeline UI component (history-003)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Component exists ---


def test_event_timeline_component_exists():
    """EventTimeline component should exist."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    assert os.path.exists(path), "EventTimeline.tsx should exist"


def test_event_timeline_is_client_component():
    """EventTimeline should be a client component."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Timeline section ---


def test_timeline_has_section_wrapper():
    """Timeline should have a section wrapper with testid."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="timeline-section"' in content


def test_timeline_has_title():
    """Timeline should display '📈 이벤트 히스토리' title."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="timeline-title"' in content
    assert "이벤트 히스토리" in content
    assert "📈" in content


def test_timeline_shows_tracking_since():
    """Timeline should show tracking_since date."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="tracking-since"' in content
    assert "부터 추적 중" in content


# --- Event card ---


def test_timeline_has_event_cards():
    """Timeline should render event cards."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="timeline-event"' in content
    assert 'data-testid="event-card"' in content


def test_event_card_shows_date():
    """Event card should show date in YYYY.MM.DD format."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="event-date"' in content
    assert "formatDate" in content


def test_event_card_shows_change_pct():
    """Event card should display change percentage with ▲/▼ prefix."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="event-change"' in content
    assert "▲" in content
    assert "▼" in content
    assert "font-bold" in content


def test_event_card_change_colors():
    """Event card should use red for up, blue for down."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "text-red-500" in content
    assert "text-blue-500" in content


def test_event_card_shows_summary():
    """Event card should show 1-line summary with ellipsis for long text."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="event-summary"' in content
    assert "line-clamp" in content


def test_event_card_shows_confidence_badge():
    """Event card should show confidence badge (높음/중간/낮음)."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="event-confidence"' in content
    # Confidence levels with colors
    assert "bg-green-100" in content   # high
    assert "bg-yellow-100" in content  # medium
    assert "bg-gray-100" in content    # low


def test_event_card_has_hover_effect():
    """Event card should have hover shadow and lift effect."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "hover:shadow" in content
    assert "cursor-pointer" in content


def test_event_card_click_navigates_to_report():
    """Clicking event card should navigate to /reports/{report_id}."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "/reports/" in content
    assert "report_id" in content
    assert "router.push" in content


# --- Timeline visual ---


def test_timeline_has_vertical_line():
    """Timeline should have a vertical dashed line on the left."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="timeline-line"' in content
    assert "border-dashed" in content


def test_timeline_has_list_wrapper():
    """Timeline should have a list wrapper."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="timeline-list"' in content


# --- Error handling ---


def test_timeline_shows_error_on_load_failure():
    """Timeline should show error message on data load failure."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "이벤트를 불러올 수 없습니다" in content
    assert 'data-testid="timeline-error"' in content


def test_timeline_has_retry_button():
    """Timeline should have retry button on error."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="retry-button"' in content
    assert "다시 시도" in content
