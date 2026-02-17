"""Structure tests for landing page (ui-019)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Route exists ---


def test_landing_page_exists():
    """Landing page route should exist."""
    path = os.path.join(BASE, "app", "page.tsx")
    assert os.path.exists(path), "app/page.tsx should exist"


def test_landing_page_is_client_component():
    """Landing page should be a client component."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Auth redirect ---


def test_landing_redirects_logged_in():
    """Logged-in users should be redirected to /dashboard."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert "isLoggedIn" in content
    assert "/dashboard" in content


# --- Loading state ---


def test_landing_has_skeleton():
    """Should show skeleton while checking auth."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert 'data-testid="landing-skeleton"' in content
    assert "animate-pulse" in content


# --- Hero section ---


def test_has_hero_section():
    """Should have hero section."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert 'data-testid="hero-section"' in content


def test_hero_title():
    """Hero should have main title."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert 'data-testid="hero-title"' in content
    assert "주가가 급변했을 때, AI가 이유를 알려드립니다" in content


def test_hero_title_bold_36px():
    """Hero title should be 36px bold."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert "font-bold" in content
    assert "36px" in content


def test_hero_subtitle():
    """Hero should have subtitle."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert 'data-testid="hero-subtitle"' in content
    assert "뉴스와 공시를 분석해 변동 원인을 심층 리포트로 제공합니다" in content


def test_hero_cta_button():
    """Hero should have CTA button linking to /signup."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert 'data-testid="hero-cta"' in content
    assert "무료로 시작하기" in content
    assert "/signup" in content


# --- Feature cards ---


def test_has_features_section():
    """Should have features section."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert 'data-testid="features-section"' in content


def test_feature_card_detection():
    """Should have feature-card testid."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert 'data-testid="feature-card"' in content


def test_feature_icons():
    """Should have feature icons."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert "⚡" in content
    assert "🤖" in content
    assert "📊" in content


def test_feature_titles():
    """Should have feature titles."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert "급변동 감지" in content
    assert "AI 분석" in content
    assert "이벤트 히스토리" in content


def test_feature_cards_responsive():
    """Feature cards should stack on mobile, 3 cols on desktop."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert "grid-cols-1" in content
    assert "md:grid-cols-3" in content


# --- Mobile responsive hero ---


def test_hero_mobile_responsive():
    """Hero title should be 28px on mobile."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert "28px" in content


# --- Bottom CTA ---


def test_has_bottom_cta():
    """Should have bottom CTA section."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert 'data-testid="bottom-cta"' in content
    assert "지금 바로 시작하세요" in content


def test_landing_testid():
    """Should have landing-page testid."""
    path = os.path.join(BASE, "app", "page.tsx")
    content = open(path).read()
    assert 'data-testid="landing-page"' in content
