"""Structure tests for auth page redesign (ui-021)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Login page ---


def test_login_page_has_testid():
    """Login page should have data-testid."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert 'data-testid="login-page"' in content


def test_login_has_auth_card():
    """Login should have centered auth card."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-card"' in content
    assert "400px" in content


def test_login_has_logo():
    """Login should have oh-my-stock logo."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-logo"' in content
    assert "oh-my-stock" in content


def test_login_has_title():
    """Login should have 로그인 title."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-title"' in content
    assert "로그인" in content


def test_login_has_form():
    """Login should have form with testid."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert 'data-testid="login-form"' in content


def test_login_has_labeled_inputs():
    """Login should have labeled email and password inputs."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert 'data-testid="label-email"' in content
    assert 'data-testid="input-email"' in content
    assert 'data-testid="label-password"' in content
    assert 'data-testid="input-password"' in content
    assert "이메일" in content
    assert "비밀번호" in content


def test_login_input_style():
    """Login inputs should use design tokens."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert "border-gray-300" in content
    assert "focus:ring" in content
    assert "radius-md" in content
    assert "12px" in content


def test_login_button_style():
    """Login button should be full-width blue with 48px height."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-submit-btn"' in content
    assert "w-full" in content
    assert "bg-blue-600" in content
    assert "48px" in content


def test_login_has_error_display():
    """Login should show error message."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-error"' in content
    assert "text-red-600" in content


def test_login_field_error_style():
    """Login should have field error support with red border."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert "border-red-500" in content
    assert "text-red-500" in content


def test_login_switch_link():
    """Login should have link to signup."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-switch-link"' in content
    assert "계정이 없으신가요?" in content
    assert "회원가입" in content
    assert "/signup" in content


# --- Signup page ---


def test_signup_page_has_testid():
    """Signup page should have data-testid."""
    path = os.path.join(BASE, "app", "signup", "page.tsx")
    content = open(path).read()
    assert 'data-testid="signup-page"' in content


def test_signup_has_auth_card():
    """Signup should have centered auth card."""
    path = os.path.join(BASE, "app", "signup", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-card"' in content
    assert "400px" in content


def test_signup_has_title():
    """Signup should have 회원가입 title."""
    path = os.path.join(BASE, "app", "signup", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-title"' in content
    assert "회원가입" in content


def test_signup_has_form():
    """Signup should have form with testid."""
    path = os.path.join(BASE, "app", "signup", "page.tsx")
    content = open(path).read()
    assert 'data-testid="signup-form"' in content


def test_signup_has_labeled_inputs():
    """Signup should have labeled inputs."""
    path = os.path.join(BASE, "app", "signup", "page.tsx")
    content = open(path).read()
    assert 'data-testid="label-email"' in content
    assert 'data-testid="input-email"' in content
    assert 'data-testid="label-password"' in content
    assert 'data-testid="input-password"' in content


def test_signup_button_style():
    """Signup button should be full-width blue with 48px height."""
    path = os.path.join(BASE, "app", "signup", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-submit-btn"' in content
    assert "48px" in content


def test_signup_switch_link():
    """Signup should have link to login."""
    path = os.path.join(BASE, "app", "signup", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-switch-link"' in content
    assert "이미 계정이 있으신가요?" in content
    assert "로그인" in content
    assert "/login" in content


def test_signup_has_error_display():
    """Signup should show error message."""
    path = os.path.join(BASE, "app", "signup", "page.tsx")
    content = open(path).read()
    assert 'data-testid="auth-error"' in content
