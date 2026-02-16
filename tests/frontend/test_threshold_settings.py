"""Structure tests for threshold settings UI (ui-007)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def test_stock_card_exists():
    path = os.path.join(BASE, "components", "StockCard.tsx")
    assert os.path.isfile(path)


def test_stock_card_has_threshold_constants():
    """StockCard should define STEP, MIN, MAX, DEFAULT threshold constants."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "STEP" in content
    assert "MIN_THRESHOLD" in content
    assert "MAX_THRESHOLD" in content
    assert "DEFAULT_THRESHOLD" in content


def test_stock_card_step_is_half_percent():
    """Threshold step should be 0.5."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "0.5" in content


def test_stock_card_min_threshold_is_1():
    """Minimum threshold should be 1%."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "MIN_THRESHOLD = 1" in content


def test_stock_card_max_threshold_is_10():
    """Maximum threshold should be 10%."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "MAX_THRESHOLD = 10" in content


def test_stock_card_has_settings_icon():
    """StockCard should have a settings gear icon button."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "settings-icon" in content


def test_stock_card_has_threshold_panel():
    """StockCard should have a collapsible threshold panel."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "threshold-panel" in content
    assert "showSettings" in content


def test_stock_card_has_stepper_buttons():
    """StockCard should have increase/decrease stepper buttons."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "threshold-decrease" in content
    assert "threshold-increase" in content


def test_stock_card_calls_update_threshold_api():
    """StockCard should call watchlistApi.updateThreshold on change."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "updateThreshold" in content
    assert "watchlistApi" in content


def test_stock_card_has_success_feedback():
    """StockCard should show success feedback after threshold save."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "threshold-success" in content
    assert "success" in content


def test_stock_card_has_error_feedback():
    """StockCard should show error message on save failure with rollback."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "threshold-error" in content
    assert "errorMsg" in content
    # Rollback: previous value restored on error
    assert "prevVal" in content
