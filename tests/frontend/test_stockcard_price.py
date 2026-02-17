"""Structure tests for StockCard price display UI (ui-011)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- WatchlistItem type includes price fields ---


def test_watchlist_type_has_latest_price():
    """WatchlistItem should include latest_price field."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "latest_price" in content


def test_watchlist_type_has_price_change():
    """WatchlistItem should include price_change and price_change_pct fields."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "price_change:" in content
    assert "price_change_pct" in content


def test_watchlist_type_has_price_currency():
    """WatchlistItem should include price_currency field."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "price_currency" in content


def test_watchlist_type_has_price_updated_at():
    """WatchlistItem should include price_updated_at field."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "price_updated_at" in content


def test_watchlist_type_has_is_price_available():
    """WatchlistItem should include is_price_available boolean."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "is_price_available" in content


def test_watchlist_type_has_price_freshness():
    """WatchlistItem should include price_freshness field."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "price_freshness" in content


def test_watchlist_type_has_tracking_count():
    """WatchlistItem should include tracking_count field."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "tracking_count" in content


# --- StockCard price display ---


def test_stockcard_has_price_section():
    """StockCard should have a price section with test id."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="price-section"' in content


def test_stockcard_displays_current_price():
    """StockCard should display current price with testid."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="current-price"' in content
    assert "font-bold" in content


def test_stockcard_displays_price_change():
    """StockCard should display price change with testid."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="price-change"' in content


def test_stockcard_has_price_unavailable_state():
    """StockCard should show '시세 대기중' when price unavailable."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "시세 대기중" in content
    assert 'data-testid="price-unavailable"' in content
    assert "italic" in content


def test_stockcard_formats_krw_price():
    """StockCard should format KRW prices with ₩ symbol."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "₩" in content
    assert "KRW" in content


def test_stockcard_formats_usd_price():
    """StockCard should format USD prices with $ symbol."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "$" in content
    assert "USD" in content


def test_stockcard_uses_intl_numberformat():
    """StockCard should use Intl.NumberFormat for price formatting."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "Intl.NumberFormat" in content


def test_stockcard_price_change_colors():
    """StockCard price change should use red for up, blue for down."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "text-red" in content
    assert "text-blue" in content


def test_stockcard_price_change_arrows():
    """StockCard should show ▲ for up and ▼ for down."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "▲" in content
    assert "▼" in content


def test_stockcard_stale_warning():
    """StockCard should show ⚠ warning for stale prices."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="stale-warning"' in content
    assert "stale" in content
    assert "업데이트 지연" in content


def test_stockcard_relative_time():
    """StockCard should show relative time for price_updated_at."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="price-updated-at"' in content
    assert "formatRelativeTime" in content
    assert "분 전" in content


def test_stockcard_tracking_count_display():
    """StockCard should display tracking count with 👥 icon."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="tracking-count"' in content
    assert "👥" in content
    assert "추적 중" in content


def test_stockcard_tracking_count_100_plus():
    """StockCard should show '100명+' for 100+ trackers."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "100명+ 추적 중" in content


def test_stockcard_is_price_available_check():
    """StockCard should check is_price_available before displaying price."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "is_price_available" in content


def test_stockcard_price_freshness_check():
    """StockCard should check price_freshness for stale warning."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "price_freshness" in content
    assert '"stale"' in content
