"""Structure tests for onboarding flow (ui-023)."""
import os
import json

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
BACKEND = os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app")


# --- Backend: User model has last_login_at ---


def test_user_model_has_last_login_at():
    """User model should have last_login_at column."""
    path = os.path.join(BACKEND, "models", "user.py")
    content = open(path).read()
    assert "last_login_at" in content
    assert "DateTime" in content


def test_login_endpoint_updates_last_login_at():
    """Login endpoint should update last_login_at."""
    path = os.path.join(BACKEND, "api", "auth.py")
    content = open(path).read()
    assert "last_login_at" in content


def test_login_returns_is_first_login():
    """Login should return is_first_login flag."""
    path = os.path.join(BACKEND, "api", "auth.py")
    content = open(path).read()
    assert "is_first_login" in content


def test_token_response_has_is_first_login():
    """TokenResponse model should include is_first_login."""
    path = os.path.join(BACKEND, "api", "auth.py")
    content = open(path).read()
    assert "is_first_login" in content
    assert "bool" in content


# --- Frontend: Login page stores onboarding flag ---


def test_login_stores_onboarding_pending():
    """Login page should store onboarding_pending in localStorage on first login."""
    path = os.path.join(BASE, "app", "login", "page.tsx")
    content = open(path).read()
    assert "onboarding_pending" in content
    assert "is_first_login" in content


# --- OnboardingOverlay component ---


def test_onboarding_component_exists():
    """OnboardingOverlay component should exist."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    assert os.path.exists(path), "OnboardingOverlay.tsx should exist"


def test_onboarding_is_client_component():
    """OnboardingOverlay should be a client component."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert '"use client"' in content


def test_onboarding_has_overlay():
    """Should have overlay with semi-transparent background."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert 'data-testid="onboarding-overlay"' in content
    assert "rgba(0,0,0,0.5)" in content


def test_onboarding_step1_welcome():
    """Step 1 should show welcome modal."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert 'data-testid="onboarding-step-1"' in content
    assert 'data-testid="onboarding-welcome-modal"' in content
    assert "환영합니다!" in content


def test_onboarding_welcome_has_description():
    """Welcome modal should have service description."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert 'data-testid="onboarding-welcome-desc"' in content


def test_onboarding_welcome_has_start_button():
    """Welcome modal should have start button."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert 'data-testid="onboarding-start-btn"' in content
    assert "시작하기" in content


def test_onboarding_step2_search_highlight():
    """Step 2 should highlight search area with tooltip."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert 'data-testid="onboarding-step-2"' in content
    assert 'data-testid="onboarding-search-tooltip"' in content
    assert "관심 종목을 추가해보세요" in content


def test_onboarding_step3_stockcard_highlight():
    """Step 3 should explain AI analysis."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert 'data-testid="onboarding-step-3"' in content
    assert 'data-testid="onboarding-stockcard-tooltip"' in content
    assert "급변동이 감지되면 AI가 분석합니다" in content


def test_onboarding_has_skip():
    """Should have skip link."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert 'data-testid="onboarding-skip"' in content
    assert "건너뛰기" in content


def test_onboarding_clears_localstorage():
    """Skip/complete should clear onboarding_pending from localStorage."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert "onboarding_pending" in content
    assert "removeItem" in content


# --- Dashboard integration ---


def test_dashboard_imports_onboarding():
    """Dashboard should import OnboardingOverlay."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "OnboardingOverlay" in content


def test_dashboard_checks_onboarding_pending():
    """Dashboard should check onboarding_pending in localStorage."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "onboarding_pending" in content


def test_dashboard_renders_onboarding():
    """Dashboard should conditionally render OnboardingOverlay."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "showOnboarding" in content
    assert "<OnboardingOverlay" in content


def test_onboarding_not_shown_on_re_login():
    """Onboarding should only show when onboarding_pending is set."""
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    # The dashboard only shows onboarding when localStorage has onboarding_pending
    assert 'onboarding_pending' in content
    assert 'setShowOnboarding' in content


def test_onboarding_step_state():
    """OnboardingOverlay should track step state."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert "useState" in content
    assert "step" in content


def test_onboarding_escape_key():
    """Pressing Escape should skip onboarding."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert "Escape" in content
    assert "handleSkip" in content


def test_onboarding_three_steps():
    """Should have 3 onboarding steps."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert "step === 1" in content
    assert "step === 2" in content
    assert "step === 3" in content


def test_onboarding_complete_callback():
    """OnboardingOverlay should accept onComplete callback."""
    path = os.path.join(BASE, "components", "OnboardingOverlay.tsx")
    content = open(path).read()
    assert "onComplete" in content


# --- API type update ---


def test_api_token_response_has_first_login():
    """Frontend TokenResponse should include is_first_login."""
    path = os.path.join(BASE, "lib", "api.ts")
    content = open(path).read()
    assert "is_first_login" in content
