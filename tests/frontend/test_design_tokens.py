"""Structure tests for design tokens (ui-016)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


# --- Color tokens ---


def test_color_primary():
    """--color-primary should be defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--color-primary:" in content
    assert "#2563EB" in content


def test_color_danger():
    """--color-danger should be defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--color-danger:" in content
    assert "#DC2626" in content


def test_color_success():
    """--color-success should be defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--color-success:" in content
    assert "#16A34A" in content


def test_color_warning():
    """--color-warning should be defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--color-warning:" in content
    assert "#D97706" in content


def test_color_up():
    """--color-up should be defined (상승 빨강)."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--color-up:" in content


def test_color_down():
    """--color-down should be defined (하락 파랑)."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--color-down:" in content


# --- Gray scale ---


def test_gray_scale_50():
    """--color-gray-50 should be defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--color-gray-50:" in content


def test_gray_scale_500():
    """--color-gray-500 should be defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--color-gray-500:" in content


def test_gray_scale_900():
    """--color-gray-900 should be defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--color-gray-900:" in content


def test_gray_scale_count():
    """Should have 9 gray scale variables."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    count = sum(1 for level in ["50", "100", "200", "300", "400", "500", "600", "700", "800", "900"]
                if f"--color-gray-{level}:" in content)
    assert count >= 9


# --- Spacing ---


def test_spacing_1():
    """--space-1 should be 4px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--space-1: 4px" in content


def test_spacing_12():
    """--space-12 should be 48px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--space-12: 48px" in content


def test_spacing_count():
    """Should have 12 spacing variables."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    count = sum(1 for i in range(1, 13) if f"--space-{i}:" in content)
    assert count == 12


# --- Border radius ---


def test_radius_sm():
    """--radius-sm should be 4px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--radius-sm: 4px" in content


def test_radius_md():
    """--radius-md should be 8px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--radius-md: 8px" in content


def test_radius_lg():
    """--radius-lg should be 12px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--radius-lg: 12px" in content


def test_radius_full():
    """--radius-full should be 9999px."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--radius-full: 9999px" in content


# --- Shadows ---


def test_shadow_sm():
    """--shadow-sm should be defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--shadow-sm:" in content


def test_shadow_md():
    """--shadow-md should be defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--shadow-md:" in content


def test_shadow_lg():
    """--shadow-lg should be defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert "--shadow-lg:" in content


# --- Total count ---


def test_total_variable_count():
    """Should have 30+ CSS variables defined."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    # Count unique CSS variable definitions
    import re
    variables = re.findall(r'--[\w-]+:', content)
    unique_vars = set(variables)
    assert len(unique_vars) >= 30, f"Found {len(unique_vars)} variables, expected 30+"


# --- Root definition ---


def test_variables_in_root():
    """Variables should be defined in :root."""
    path = os.path.join(BASE, "app", "globals.css")
    content = open(path).read()
    assert ":root" in content
