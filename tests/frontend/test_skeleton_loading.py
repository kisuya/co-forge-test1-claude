"""Structure tests for skeleton loading UI (ui-026)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Skeleton component ---


def test_skeleton_component_exists():
    """Skeleton component should exist."""
    path = os.path.join(BASE, "components", "Skeleton.tsx")
    assert os.path.exists(path), "Skeleton.tsx should exist"


def test_skeleton_is_client_component():
    """Skeleton should be a client component."""
    path = os.path.join(BASE, "components", "Skeleton.tsx")
    content = open(path).read()
    assert '"use client"' in content


def test_skeleton_has_animate_pulse():
    """Skeleton should use animate-pulse."""
    path = os.path.join(BASE, "components", "Skeleton.tsx")
    content = open(path).read()
    assert "animate-pulse" in content


def test_skeleton_has_bg_gray():
    """Skeleton should have gray background."""
    path = os.path.join(BASE, "components", "Skeleton.tsx")
    content = open(path).read()
    assert "bg-gray-200" in content


def test_skeleton_accepts_width_prop():
    """Skeleton should accept width prop."""
    path = os.path.join(BASE, "components", "Skeleton.tsx")
    content = open(path).read()
    assert "width" in content


def test_skeleton_accepts_height_prop():
    """Skeleton should accept height prop."""
    path = os.path.join(BASE, "components", "Skeleton.tsx")
    content = open(path).read()
    assert "height" in content


def test_skeleton_accepts_rounded_prop():
    """Skeleton should accept rounded prop."""
    path = os.path.join(BASE, "components", "Skeleton.tsx")
    content = open(path).read()
    assert "rounded" in content


def test_skeleton_has_testid():
    """Skeleton should have data-testid."""
    path = os.path.join(BASE, "components", "Skeleton.tsx")
    content = open(path).read()
    assert 'data-testid="skeleton"' in content


# --- Dashboard loading ---


def test_dashboard_loading_exists():
    """Dashboard loading.tsx should exist."""
    path = os.path.join(BASE, "app", "dashboard", "loading.tsx")
    assert os.path.exists(path), "dashboard/loading.tsx should exist"


def test_dashboard_loading_has_skeleton():
    """Dashboard loading should use Skeleton component."""
    path = os.path.join(BASE, "app", "dashboard", "loading.tsx")
    content = open(path).read()
    assert "Skeleton" in content


def test_dashboard_loading_has_stockcard_skeletons():
    """Dashboard loading should show stockcard-shaped skeletons."""
    path = os.path.join(BASE, "app", "dashboard", "loading.tsx")
    content = open(path).read()
    assert 'data-testid="stockcard-skeleton"' in content or 'data-testid="dashboard-loading"' in content


# --- Report loading ---


def test_report_loading_exists():
    """Report loading.tsx should exist."""
    path = os.path.join(BASE, "app", "reports", "[id]", "loading.tsx")
    assert os.path.exists(path), "reports/[id]/loading.tsx should exist"


def test_report_loading_has_skeleton():
    """Report loading should use Skeleton component."""
    path = os.path.join(BASE, "app", "reports", "[id]", "loading.tsx")
    content = open(path).read()
    assert "Skeleton" in content


def test_report_loading_has_testid():
    """Report loading should have testid."""
    path = os.path.join(BASE, "app", "reports", "[id]", "loading.tsx")
    content = open(path).read()
    assert 'data-testid="report-loading"' in content


# --- Stock detail loading ---


def test_stock_loading_exists():
    """Stock detail loading.tsx should exist."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "loading.tsx")
    assert os.path.exists(path), "stocks/[stockId]/loading.tsx should exist"


def test_stock_loading_has_skeleton():
    """Stock loading should use Skeleton component."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "loading.tsx")
    content = open(path).read()
    assert "Skeleton" in content


def test_stock_loading_has_testid():
    """Stock loading should have testid."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "loading.tsx")
    content = open(path).read()
    assert 'data-testid="stock-detail-skeleton"' in content
