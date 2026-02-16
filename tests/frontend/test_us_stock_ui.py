"""Structure tests for US stock integrated UI (ui-008)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Stock type includes name_kr ---


def test_stock_type_has_name_kr():
    """Stock interface should include name_kr field."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "name_kr" in content
    assert "string | null" in content


def test_watchlist_type_has_stock_market():
    """WatchlistItem interface should include stock_market field."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "stock_market" in content


# --- Market tabs in StockSearch ---


def test_stock_search_has_market_tabs():
    """StockSearch should have market tab buttons."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "market-tabs" in content
    assert "market-tab-" in content
    assert "MARKET_TABS" in content


def test_stock_search_market_tab_labels():
    """Market tabs should show Korean labels with flags."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "전체" in content
    assert "한국" in content
    assert "미국" in content


def test_stock_search_market_state():
    """StockSearch should manage market state (all/kr/us)."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "MarketTab" in content
    assert '"all"' in content
    assert '"kr"' in content
    assert '"us"' in content
    assert "setMarket" in content


def test_stock_search_passes_market_to_api():
    """StockSearch should pass market to stocksApi.search."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "marketRef.current" in content
    assert "stocksApi.search" in content


def test_stock_search_re_searches_on_tab_change():
    """Search effect should depend on market state for re-triggering."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "[query, market, executeSearch]" in content


# --- name_kr highlight ---


def test_stock_search_shows_name_kr():
    """StockSearch should display name_kr for US stocks."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "nameKrParts" in content
    assert "name_kr" in content
    assert 'data-testid="name-kr"' in content


def test_stock_search_highlights_name_kr():
    """StockSearch should highlight matching text in name_kr."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "highlightMatch(stock.name_kr" in content


# --- Market badges in search results ---


def test_stock_search_has_market_badge():
    """Search results should show colored market badges."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "MARKET_BADGE" in content
    assert 'data-testid="market-badge"' in content


def test_search_market_badge_colors():
    """Market badges should have distinct colors for KRX/NYSE/NASDAQ."""
    path = os.path.join(BASE, "components", "StockSearch.tsx")
    content = open(path).read()
    assert "blue" in content  # KRX
    assert "green" in content  # NYSE
    assert "purple" in content  # NASDAQ


# --- Market badges in StockCard ---


def test_stock_card_has_market_badge():
    """StockCard should display a market badge."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "MARKET_BADGE" in content
    assert 'data-testid="card-market-badge"' in content


def test_stock_card_uses_stock_market():
    """StockCard should use item.stock_market for the badge."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "stock_market" in content


def test_stock_card_market_badge_colors():
    """StockCard market badge should distinguish KRX/NYSE/NASDAQ."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "KRX" in content
    assert "NYSE" in content
    assert "NASDAQ" in content


# --- queries.ts market parameter ---


def test_queries_search_accepts_market():
    """stocksApi.search should accept a market parameter."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "market" in content
    assert "stocksApi" in content


def test_queries_search_passes_market_param():
    """stocksApi.search should pass market as query param."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "params" in content
    assert "market" in content


# --- Backend watchlist response includes stock_market ---


def test_backend_watchlist_response_has_stock_market():
    """WatchlistItemResponse should include stock_market field."""
    backend = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
    path = os.path.join(backend, "app", "api", "watchlist.py")
    content = open(path).read()
    assert "stock_market" in content
    assert "stock.market" in content


def test_backend_stock_response_has_market():
    """StockResponse should include market field."""
    backend = os.path.join(os.path.dirname(__file__), "..", "..", "backend")
    path = os.path.join(backend, "app", "api", "stocks.py")
    content = open(path).read()
    assert "market" in content
