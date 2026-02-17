"""Structure tests for global footer (ui-020)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Component exists ---


def test_footer_component_exists():
    """GlobalFooter component should exist."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    assert os.path.exists(path), "GlobalFooter.tsx should exist"


def test_footer_is_client_component():
    """GlobalFooter should be a client component."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert '"use client"' in content


# --- Footer structure ---


def test_has_footer_testid():
    """Should have data-testid for footer."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert 'data-testid="global-footer"' in content


def test_footer_background():
    """Footer should have gray-50 background."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert "bg-gray-50" in content


def test_footer_border_top():
    """Footer should have border-top."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert "border-t" in content
    assert "border-gray-200" in content


def test_footer_padding():
    """Footer should have 24px padding."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert "24px" in content


# --- Disclaimer ---


def test_has_disclaimer():
    """Footer should have disclaimer text."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert 'data-testid="footer-disclaimer"' in content
    assert "본 서비스는 투자 조언을 제공하지 않습니다" in content
    assert "투자 판단의 책임은 본인에게 있습니다" in content


def test_disclaimer_text_style():
    """Disclaimer should be 12px gray text."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert "text-xs" in content
    assert "text-gray-500" in content


# --- Links ---


def test_has_terms_link():
    """Footer should have terms link."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert 'data-testid="footer-terms"' in content
    assert "이용약관" in content


def test_has_privacy_link():
    """Footer should have privacy link."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert 'data-testid="footer-privacy"' in content
    assert "개인정보처리방침" in content


def test_has_contact_link():
    """Footer should have contact link."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert 'data-testid="footer-contact"' in content
    assert "문의" in content


def test_links_hover_underline():
    """Links should have hover:underline."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert "hover:underline" in content


# --- Copyright ---


def test_has_copyright():
    """Footer should have copyright text."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert 'data-testid="footer-copyright"' in content
    assert "© 2026 oh-my-stock" in content


# --- Mobile margin ---


def test_footer_mobile_margin():
    """Footer should have margin-bottom for mobile tab bar."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert "mb-14" in content
    assert "md:mb-0" in content


# --- Shared page ---


def test_footer_hidden_on_shared():
    """Footer should not show on /shared/* pages."""
    path = os.path.join(BASE, "components", "GlobalFooter.tsx")
    content = open(path).read()
    assert "/shared" in content


# --- Layout integration ---


def test_layout_uses_footer():
    """RootLayout should import and use GlobalFooter."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "GlobalFooter" in content
