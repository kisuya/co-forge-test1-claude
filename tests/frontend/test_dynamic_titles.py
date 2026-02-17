"""Structure tests for dynamic page titles (ui-025)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Layout title template ---


def test_layout_has_title_template():
    """Layout should have title template with oh-my-stock."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "template" in content
    assert "oh-my-stock" in content


# --- Dashboard title ---


def test_dashboard_sets_title():
    """Dashboard should set document.title."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "document.title" in content
    assert "내 관심 종목" in content
    assert "oh-my-stock" in content


# --- Report detail title ---


def test_report_sets_dynamic_title():
    """Report detail should set document.title with stock name."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "document.title" in content
    assert "변동 분석" in content
    assert "oh-my-stock" in content


def test_report_title_uses_stock_name():
    """Report title should use stock_name from response data."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "stock_name" in content
    assert "document.title" in content


def test_report_title_fallback():
    """Report should fallback to oh-my-stock on error."""
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    # Check that error path also sets a title
    lines = content.split("\n")
    title_count = sum(1 for l in lines if "document.title" in l)
    assert title_count >= 2, "Should set title in both success and error paths"


# --- Stock detail title ---


def test_stock_sets_dynamic_title():
    """Stock detail should set document.title with stock name."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    assert "document.title" in content
    assert "이벤트 히스토리" in content
    assert "oh-my-stock" in content


def test_stock_title_fallback():
    """Stock should fallback title on error."""
    path = os.path.join(BASE, "app", "stocks", "[stockId]", "page.tsx")
    content = open(path).read()
    lines = content.split("\n")
    title_count = sum(1 for l in lines if "document.title" in l)
    assert title_count >= 2, "Should set title in both success and error paths"


# --- MyPage title ---


def test_mypage_sets_title():
    """MyPage should set document.title."""
    path = os.path.join(BASE, "app", "mypage", "page.tsx")
    content = open(path).read()
    assert "document.title" in content
    assert "마이페이지" in content
    assert "oh-my-stock" in content


# --- Shared report title ---


def test_shared_sets_dynamic_title():
    """Shared report should set document.title with stock name."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "document.title" in content
    assert "변동 분석 공유" in content
    assert "oh-my-stock" in content


def test_shared_has_og_meta():
    """Shared report should have OG meta tags."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "og:title" in content or "og-title" in content
    assert "og:description" in content or "og-description" in content


def test_shared_og_uses_stock_name():
    """Shared OG title should include stock_name."""
    path = os.path.join(BASE, "app", "shared", "[token]", "page.tsx")
    content = open(path).read()
    assert "stock_name" in content
    assert "oh-my-stock" in content
