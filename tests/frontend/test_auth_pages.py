"""Tests for frontend auth pages and structure."""
from __future__ import annotations

import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")


def test_frontend_package_json_exists() -> None:
    """Frontend should have a package.json."""
    assert os.path.exists(os.path.join(BASE, "package.json"))


def test_frontend_tsconfig_exists() -> None:
    """Frontend should have a tsconfig.json."""
    assert os.path.exists(os.path.join(BASE, "tsconfig.json"))


def test_frontend_layout_exists() -> None:
    """Frontend should have a root layout."""
    assert os.path.exists(os.path.join(BASE, "src", "app", "layout.tsx"))


def test_frontend_login_page_exists() -> None:
    """Frontend should have a login page."""
    assert os.path.exists(os.path.join(BASE, "src", "app", "login", "page.tsx"))


def test_frontend_signup_page_exists() -> None:
    """Frontend should have a signup page."""
    assert os.path.exists(os.path.join(BASE, "src", "app", "signup", "page.tsx"))


def test_frontend_api_client_exists() -> None:
    """Frontend should have an API client module."""
    assert os.path.exists(os.path.join(BASE, "src", "lib", "api.ts"))


def test_frontend_auth_helper_exists() -> None:
    """Frontend should have an auth helper module."""
    assert os.path.exists(os.path.join(BASE, "src", "lib", "auth.ts"))


def test_login_page_has_form() -> None:
    """Login page should contain a form with email and password."""
    path = os.path.join(BASE, "src", "app", "login", "page.tsx")
    with open(path) as f:
        content = f.read()
    assert "email" in content.lower()
    assert "password" in content.lower()
    assert "submit" in content.lower() or "login" in content.lower()


def test_signup_page_has_form() -> None:
    """Signup page should contain a form with email and password."""
    path = os.path.join(BASE, "src", "app", "signup", "page.tsx")
    with open(path) as f:
        content = f.read()
    assert "email" in content.lower()
    assert "password" in content.lower()
    assert "sign" in content.lower()


def test_api_client_has_auth_endpoints() -> None:
    """API client should have login and signup methods."""
    path = os.path.join(BASE, "src", "lib", "api.ts")
    with open(path) as f:
        content = f.read()
    assert "signup" in content
    assert "login" in content
    assert "/api/auth" in content
