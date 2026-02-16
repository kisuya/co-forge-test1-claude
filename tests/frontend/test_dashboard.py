"""Structure tests for dashboard and watchlist UI (ui-002)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def test_types_index_exists():
    path = os.path.join(BASE, "types", "index.ts")
    assert os.path.isfile(path)


def test_types_has_stock_and_watchlist():
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "export interface Stock" in content
    assert "export interface WatchlistItem" in content
    assert "export interface Report" in content


def test_queries_module_exists():
    path = os.path.join(BASE, "lib", "queries.ts")
    assert os.path.isfile(path)


def test_queries_has_api_objects():
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "stocksApi" in content
    assert "watchlistApi" in content
    assert "reportsApi" in content


def test_stock_card_component_exists():
    path = os.path.join(BASE, "components", "StockCard.tsx")
    assert os.path.isfile(path)


def test_stock_card_has_change_highlighting():
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "text-red" in content  # positive change color
    assert "text-blue" in content  # negative change color
    assert "급변동" in content  # spike badge


def test_stock_search_component_exists():
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    assert os.path.isfile(path)


def test_watchlist_manager_component_exists():
    path = os.path.join(BASE, "components", "WatchlistManager.tsx")
    assert os.path.isfile(path)


def test_watchlist_manager_has_crud_ops():
    path = os.path.join(BASE, "components", "WatchlistManager.tsx")
    content = open(path).read()
    assert "watchlistApi.getAll" in content
    assert "watchlistApi.add" in content
    assert "watchlistApi.remove" in content


def test_dashboard_page_exists():
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    assert os.path.isfile(path)


def test_dashboard_uses_watchlist_manager():
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "WatchlistManager" in content


def test_dashboard_has_auth_guard():
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "isLoggedIn" in content
