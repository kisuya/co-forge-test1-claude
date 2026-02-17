"""Structure tests for custom error page (ui-028)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def test_error_page_exists():
    """error.tsx should exist in app directory."""
    path = os.path.join(BASE, "app", "error.tsx")
    assert os.path.exists(path), "app/error.tsx should exist"


def test_error_is_client_component():
    """error.tsx must be a client component."""
    path = os.path.join(BASE, "app", "error.tsx")
    content = open(path).read()
    assert '"use client"' in content


def test_error_has_testid():
    """Should have error-boundary testid."""
    path = os.path.join(BASE, "app", "error.tsx")
    content = open(path).read()
    assert 'data-testid="error-boundary"' in content


def test_error_title():
    """Should show '문제가 발생했습니다' at 24px."""
    path = os.path.join(BASE, "app", "error.tsx")
    content = open(path).read()
    assert "문제가 발생했습니다" in content
    assert "24px" in content


def test_error_description():
    """Should show description '잠시 후 다시 시도해주세요' at 14px."""
    path = os.path.join(BASE, "app", "error.tsx")
    content = open(path).read()
    assert "잠시 후 다시 시도해주세요" in content
    assert "14px" in content


def test_error_reset_button():
    """Should have '다시 시도' button that calls reset()."""
    path = os.path.join(BASE, "app", "error.tsx")
    content = open(path).read()
    assert "다시 시도" in content
    assert "reset" in content
    assert 'data-testid="error-reset-btn"' in content


def test_error_dashboard_link():
    """Should have '대시보드로 돌아가기' link."""
    path = os.path.join(BASE, "app", "error.tsx")
    content = open(path).read()
    assert "대시보드로 돌아가기" in content
    assert "/dashboard" in content
    assert 'data-testid="error-dashboard-link"' in content


def test_error_dev_stack():
    """Should show error stack in development mode."""
    path = os.path.join(BASE, "app", "error.tsx")
    content = open(path).read()
    assert "development" in content
    assert "error.message" in content


def test_error_accepts_props():
    """Should accept error and reset props."""
    path = os.path.join(BASE, "app", "error.tsx")
    content = open(path).read()
    assert "error" in content
    assert "reset" in content
