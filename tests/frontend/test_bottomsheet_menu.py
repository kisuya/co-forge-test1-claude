"""Structure tests for StockCard mobile bottom sheet menu (ui-014)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Mobile detection ---


def test_stockcard_has_mobile_detection():
    """StockCard should detect mobile viewport with matchMedia."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "isMobile" in content
    assert "matchMedia" in content
    assert "768px" in content


# --- Bottom sheet overlay ---


def test_stockcard_has_bottomsheet_overlay():
    """StockCard should have a bottom sheet overlay for mobile."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="bottomsheet-overlay"' in content


def test_bottomsheet_has_semi_transparent_bg():
    """Bottom sheet overlay should have semi-transparent background."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "bg-black/50" in content


# --- Bottom sheet content ---


def test_stockcard_has_bottomsheet_content():
    """StockCard should have bottom sheet content container."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="bottomsheet-content"' in content


def test_bottomsheet_has_slide_animation():
    """Bottom sheet should have slide-up animation."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "animate-slide-up" in content


def test_bottomsheet_has_handle():
    """Bottom sheet should have a drag handle indicator."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="bottomsheet-handle"' in content


def test_bottomsheet_has_rounded_top():
    """Bottom sheet should have rounded top corners."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "rounded-t" in content


# --- Bottom sheet menu items ---


def test_bottomsheet_has_history_item():
    """Bottom sheet should have history menu item."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="bs-menu-history"' in content


def test_bottomsheet_has_alert_toggle():
    """Bottom sheet should have alert toggle menu item."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="bs-menu-alert-toggle"' in content


def test_bottomsheet_has_threshold_panel():
    """Bottom sheet should have threshold panel."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="bs-threshold-panel"' in content


def test_bottomsheet_has_remove_item():
    """Bottom sheet should have remove menu item."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="bs-menu-remove"' in content


# --- Touch target sizes ---


def test_bottomsheet_touch_targets():
    """Bottom sheet items should have minimum 48px touch targets."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "min-h-[48px]" in content


# --- Safe area ---


def test_bottomsheet_safe_area():
    """Bottom sheet should respect safe-area-inset-bottom."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "safe-area-inset-bottom" in content


# --- Body scroll lock ---


def test_bottomsheet_body_scroll_lock():
    """Body scroll should be locked when bottom sheet is open."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "overflow" in content
    assert "hidden" in content


# --- Desktop vs mobile conditional rendering ---


def test_desktop_dropdown_hidden_on_mobile():
    """Desktop dropdown should use md:block to hide on mobile."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "md:block" in content or "!isMobile" in content


def test_mobile_bottomsheet_hidden_on_desktop():
    """Mobile bottom sheet should use md:hidden to hide on desktop."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "md:hidden" in content or "isMobile" in content


# --- Overlay click closes ---


def test_overlay_click_closes_bottomsheet():
    """Clicking overlay should close the bottom sheet."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "closeMenu" in content
    # overlay has onClick closeMenu
    assert "bottomsheet-overlay" in content


# --- CSS animation ---


def test_globals_has_slide_up_animation():
    """globals.css should define slide-up animation."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "slide-up" in content
    assert "translateY" in content
    assert "animate-slide-up" in content


def test_globals_slide_up_duration():
    """Slide-up animation should be around 300ms."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "0.3s" in content
    assert "ease-out" in content
