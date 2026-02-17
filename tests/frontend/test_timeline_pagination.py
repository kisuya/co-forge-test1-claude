"""Structure tests for timeline pagination and empty state (history-004)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Pagination ---


def test_timeline_has_load_more_button():
    """Timeline should have 'load more' button when hasMore is true."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="load-more-button"' in content
    assert "이전 이벤트 더 보기" in content


def test_load_more_button_has_loading_state():
    """Load more button should show spinner while loading."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "loadingMore" in content
    assert "animate-spin" in content
    assert "불러오는 중" in content


def test_load_more_button_disabled_during_loading():
    """Load more button should be disabled during loading."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "disabled" in content
    assert "disabled:opacity" in content


def test_load_more_fetches_next_page():
    """Load more should fetch next page and append events."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "page + 1" in content or "nextPage" in content
    # Should append, not replace
    assert "...prev" in content or "[...prev" in content


def test_load_more_hidden_when_no_more():
    """Load more button should be hidden when hasMore is false."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "hasMore" in content


def test_load_more_section_has_testid():
    """Load more section should have a testid."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="load-more-section"' in content


# --- Empty state ---


def test_timeline_has_empty_state():
    """Timeline should show empty state when no events."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="timeline-empty"' in content


def test_empty_state_has_icon():
    """Empty state should have clock icon."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert "🕐" in content


def test_empty_state_has_title():
    """Empty state should show '아직 추적 이벤트가 없습니다'."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="empty-title"' in content
    assert "아직 추적 이벤트가 없습니다" in content


def test_empty_state_has_description():
    """Empty state should show description about auto-recording."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="empty-description"' in content
    assert "급변동이 감지되면 자동으로 기록됩니다" in content


# --- Error during load more ---


def test_load_more_error_has_testid():
    """Load more error should have a testid."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    assert 'data-testid="load-more-error"' in content


def test_load_more_error_shows_retry():
    """Load more error should show retry button."""
    path = os.path.join(BASE, "components", "EventTimeline.tsx")
    content = open(path).read()
    # Should have a retry mechanism for load more errors
    assert "다시 시도" in content
