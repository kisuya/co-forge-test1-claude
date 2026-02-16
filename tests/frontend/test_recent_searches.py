"""Structure tests for recent searches feature (ui-006)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def test_recent_searches_utility_exists():
    path = os.path.join(BASE, "lib", "recentSearches.ts")
    assert os.path.isfile(path)


def test_recent_searches_has_crud_functions():
    """recentSearches utility should have get/add/remove/clear functions."""
    path = os.path.join(BASE, "lib", "recentSearches.ts")
    content = open(path).read()
    assert "getRecentSearches" in content
    assert "addRecentSearch" in content
    assert "removeRecentSearch" in content
    assert "clearRecentSearches" in content


def test_recent_searches_uses_local_storage():
    """recentSearches should use localStorage."""
    path = os.path.join(BASE, "lib", "recentSearches.ts")
    content = open(path).read()
    assert "localStorage" in content


def test_recent_searches_max_10_items():
    """recentSearches should limit to 10 items (FIFO)."""
    path = os.path.join(BASE, "lib", "recentSearches.ts")
    content = open(path).read()
    assert "MAX_ITEMS" in content or "10" in content


def test_recent_searches_component_exists():
    path = os.path.join(BASE, "components", "RecentSearches.tsx")
    assert os.path.isfile(path)


def test_recent_searches_has_clock_icon():
    """RecentSearches should display a clock icon."""
    path = os.path.join(BASE, "components", "RecentSearches.tsx")
    content = open(path).read()
    # Clock emoji or icon
    assert "🕐" in content or "clock" in content.lower()


def test_recent_searches_has_remove_button():
    """RecentSearches should have X button for individual deletion."""
    path = os.path.join(BASE, "components", "RecentSearches.tsx")
    content = open(path).read()
    assert "remove-recent-btn" in content or "removeRecentSearch" in content


def test_recent_searches_has_clear_all():
    """RecentSearches should have '최근 검색어 전체 삭제' link."""
    path = os.path.join(BASE, "components", "RecentSearches.tsx")
    content = open(path).read()
    assert "최근 검색어 전체 삭제" in content
    assert "clearRecentSearches" in content


def test_stock_search_integrates_recent_searches():
    """StockSearch should use RecentSearches component."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "RecentSearches" in content
    assert "addRecentSearch" in content


def test_stock_search_shows_recent_on_focus():
    """StockSearch should show recent searches on focus when input is empty."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "onFocus" in content
    assert "focused" in content
    assert "showRecent" in content
