"""Structure tests for StockCard kebab menu (ui-013)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
BACKEND = os.path.join(os.path.dirname(__file__), "..", "..", "backend")


# --- Kebab menu button ---


def test_stockcard_has_kebab_button():
    """StockCard should have a ⋮ kebab menu button."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "⋮" in content
    assert 'data-testid="kebab-menu-button"' in content


def test_stockcard_kebab_replaces_settings_icon():
    """StockCard should no longer have separate ⚙️ settings icon as standalone button."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    # ⚙️ should exist in the menu but not as standalone settings-icon button
    assert 'data-testid="settings-icon"' not in content
    assert "⚙️" in content  # still in dropdown menu


def test_stockcard_kebab_has_aria():
    """Kebab button should have aria-label and aria-haspopup."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'aria-label="종목 관리 메뉴"' in content
    assert 'aria-haspopup="menu"' in content
    assert "aria-expanded" in content


# --- Dropdown menu ---


def test_stockcard_has_dropdown():
    """StockCard should have a dropdown menu container."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="kebab-dropdown"' in content
    assert 'role="menu"' in content


def test_dropdown_has_max_width():
    """Dropdown should have a max-width around 240px."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "w-60" in content  # 240px in Tailwind


def test_dropdown_has_z_index():
    """Dropdown should have z-index management."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "z-50" in content


# --- Menu items ---


def test_menu_has_history_item():
    """Menu should have '이벤트 히스토리' item."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="menu-history"' in content
    assert "이벤트 히스토리" in content
    assert "📊" in content


def test_menu_history_navigates():
    """History menu item should navigate to /stocks/{stock_id}."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "router.push" in content
    assert "/stocks/" in content
    assert "stock_id" in content


def test_menu_has_alert_toggle():
    """Menu should have '알림 ON/OFF' toggle item."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="menu-alert-toggle"' in content
    assert "🔔" in content
    assert "알림" in content


def test_menu_alert_toggle_calls_api():
    """Alert toggle should call watchlistApi.updateAlert."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "handleAlertToggle" in content
    assert "updateAlert" in content


def test_menu_alert_toggle_toast():
    """Alert toggle success should show toast."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "알림이 켜졌습니다" in content
    assert "알림이 꺼졌습니다" in content
    assert "addToast" in content


def test_menu_alert_error_toast():
    """Alert toggle failure should show error toast."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "알림 설정에 실패했습니다" in content


def test_menu_has_threshold_stepper():
    """Menu should have inline threshold stepper."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "변동 감지 임계값" in content
    assert 'data-testid="threshold-panel"' in content
    assert 'data-testid="threshold-decrease"' in content
    assert 'data-testid="threshold-increase"' in content
    assert 'data-testid="threshold-value"' in content


def test_menu_has_remove_item():
    """Menu should have '관심목록에서 제거' item in red."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="menu-remove"' in content
    assert "관심목록에서 제거" in content
    assert "🗑️" in content
    assert "text-red" in content


# --- Confirm delete dialog ---


def test_menu_remove_shows_confirm():
    """Remove should show a confirmation dialog."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="confirm-delete-dialog"' in content
    assert 'role="dialog"' in content
    assert "종목 제거" in content
    assert "관심목록에서 제거하시겠습니까" in content


def test_confirm_dialog_has_buttons():
    """Confirm dialog should have cancel and confirm buttons."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'data-testid="confirm-cancel"' in content
    assert 'data-testid="confirm-delete"' in content
    assert "취소" in content


# --- Keyboard navigation ---


def test_menu_escape_closes():
    """Pressing Escape should close the menu."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert '"Escape"' in content
    assert "closeMenu" in content


def test_menu_outside_click_closes():
    """Clicking outside should close the menu."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert "mousedown" in content
    assert "menuRef" in content
    assert "contains" in content


def test_menu_arrow_key_navigation():
    """Arrow keys should navigate menu items."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert '"ArrowDown"' in content
    assert '"ArrowUp"' in content
    assert "menuFocusIndex" in content


# --- API: updateAlert ---


def test_queries_has_update_alert():
    """watchlistApi should export updateAlert method."""
    path = os.path.join(BASE, "lib", "queries.ts")
    content = open(path).read()
    assert "updateAlert" in content
    assert "alert_enabled" in content


# --- Backend: alert_enabled ---


def test_backend_watchlist_model_has_alert_enabled():
    """Watchlist model should have alert_enabled column."""
    path = os.path.join(BACKEND, "app", "models", "watchlist.py")
    content = open(path).read()
    assert "alert_enabled" in content


def test_backend_watchlist_response_has_alert_enabled():
    """WatchlistItemResponse should include alert_enabled field."""
    path = os.path.join(BACKEND, "app", "api", "watchlist.py")
    content = open(path).read()
    assert "alert_enabled" in content


def test_backend_patch_supports_alert_enabled():
    """PATCH endpoint should support alert_enabled field."""
    path = os.path.join(BACKEND, "app", "api", "watchlist.py")
    content = open(path).read()
    assert "alert_enabled" in content
    # The update request model should accept alert_enabled
    assert "WatchlistUpdateRequest" in content


# --- WatchlistItem type ---


def test_watchlist_type_has_alert_enabled():
    """WatchlistItem TypeScript interface should include alert_enabled."""
    path = os.path.join(BASE, "types", "index.ts")
    content = open(path).read()
    assert "alert_enabled" in content


# --- Menu items have role="menuitem" ---


def test_menu_items_have_role():
    """Menu items should have role='menuitem'."""
    path = os.path.join(BASE, "components", "StockCard.tsx")
    content = open(path).read()
    assert 'role="menuitem"' in content
