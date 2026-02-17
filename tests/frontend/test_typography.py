"""Structure tests for typography system (ui-015)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Font family ---


def test_globals_css_has_font_family_variable():
    """globals.css should define --font-pretendard variable."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--font-pretendard" in content


def test_globals_css_has_pretendard():
    """globals.css should reference Pretendard font."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "Pretendard" in content


def test_globals_css_has_fallback_fonts():
    """globals.css should have fallback fonts (Noto Sans KR, system-ui, sans-serif)."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "Noto Sans KR" in content
    assert "system-ui" in content
    assert "sans-serif" in content


def test_body_uses_font_variable():
    """body should use var(--font-pretendard)."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "font-family: var(--font-pretendard)" in content


# --- Type scale ---


def test_type_scale_xs():
    """--text-xs should be 12px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--text-xs: 12px" in content


def test_type_scale_sm():
    """--text-sm should be 14px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--text-sm: 14px" in content


def test_type_scale_base():
    """--text-base should be 16px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--text-base: 16px" in content


def test_type_scale_lg():
    """--text-lg should be 18px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--text-lg: 18px" in content


def test_type_scale_xl():
    """--text-xl should be 20px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--text-xl: 20px" in content


def test_type_scale_2xl():
    """--text-2xl should be 24px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--text-2xl: 24px" in content


def test_type_scale_3xl():
    """--text-3xl should be 30px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--text-3xl: 30px" in content


# --- Font weights ---


def test_font_weight_normal():
    """--font-normal should be 400."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--font-normal: 400" in content


def test_font_weight_medium():
    """--font-medium should be 500."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--font-medium: 500" in content


def test_font_weight_semibold():
    """--font-semibold should be 600."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--font-semibold: 600" in content


def test_font_weight_bold():
    """--font-bold should be 700."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--font-bold: 700" in content


# --- Line heights ---


def test_body_line_height():
    """Body line-height should be 1.5."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--leading-body: 1.5" in content


def test_heading_line_height():
    """Heading line-height should be 1.2."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--leading-heading: 1.2" in content


# --- Total variable count ---


def test_type_scale_count():
    """Should have 7 type scale variables."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    count = sum(1 for var in ["--text-xs", "--text-sm", "--text-base", "--text-lg",
                               "--text-xl", "--text-2xl", "--text-3xl"]
                if var in content)
    assert count == 7


def test_font_weight_count():
    """Should have 4 font weight variables."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    count = sum(1 for var in ["--font-normal", "--font-medium", "--font-semibold", "--font-bold"]
                if var in content)
    assert count == 4
