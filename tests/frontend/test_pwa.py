"""Structure tests for PWA manifest and icons (ui-029)."""
import json
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend")
SRC = os.path.join(BASE, "src")
PUBLIC = os.path.join(BASE, "public")


def test_manifest_exists():
    """manifest.json should exist in public directory."""
    path = os.path.join(PUBLIC, "manifest.json")
    assert os.path.exists(path), "public/manifest.json should exist"


def test_manifest_valid_json():
    """manifest.json should be valid JSON."""
    path = os.path.join(PUBLIC, "manifest.json")
    with open(path) as f:
        data = json.load(f)
    assert isinstance(data, dict)


def test_manifest_name():
    """manifest.json should have name field."""
    path = os.path.join(PUBLIC, "manifest.json")
    data = json.load(open(path))
    assert data.get("name") == "oh-my-stock"


def test_manifest_short_name():
    """manifest.json short_name should be max 12 chars."""
    path = os.path.join(PUBLIC, "manifest.json")
    data = json.load(open(path))
    short = data.get("short_name", "")
    assert short == "oh-my-stock"
    assert len(short) <= 12


def test_manifest_start_url():
    """manifest.json should have start_url."""
    path = os.path.join(PUBLIC, "manifest.json")
    data = json.load(open(path))
    assert data.get("start_url") == "/"


def test_manifest_display():
    """manifest.json should have display standalone."""
    path = os.path.join(PUBLIC, "manifest.json")
    data = json.load(open(path))
    assert data.get("display") == "standalone"


def test_manifest_theme_color():
    """manifest.json should have theme_color."""
    path = os.path.join(PUBLIC, "manifest.json")
    data = json.load(open(path))
    assert data.get("theme_color") == "#2563EB"


def test_manifest_background_color():
    """manifest.json should have background_color."""
    path = os.path.join(PUBLIC, "manifest.json")
    data = json.load(open(path))
    assert data.get("background_color") == "#FFFFFF"


def test_manifest_icons():
    """manifest.json should have icons array with 192 and 512."""
    path = os.path.join(PUBLIC, "manifest.json")
    data = json.load(open(path))
    icons = data.get("icons", [])
    assert len(icons) >= 2
    sizes = [i.get("sizes") for i in icons]
    assert "192x192" in sizes
    assert "512x512" in sizes


def test_icon_192_exists():
    """192x192 icon should exist."""
    path = os.path.join(PUBLIC, "icon-192x192.png")
    assert os.path.exists(path)


def test_icon_512_exists():
    """512x512 icon should exist."""
    path = os.path.join(PUBLIC, "icon-512x512.png")
    assert os.path.exists(path)


def test_favicon_exists():
    """favicon.ico should exist in app directory."""
    path = os.path.join(SRC, "app", "favicon.ico")
    assert os.path.exists(path), "app/favicon.ico should exist"


def test_apple_icon_exists():
    """apple-icon.png should exist in public directory."""
    path = os.path.join(PUBLIC, "apple-icon.png")
    assert os.path.exists(path), "public/apple-icon.png should exist"


def test_layout_manifest_link():
    """layout.tsx should have link rel manifest."""
    path = os.path.join(SRC, "app", "layout.tsx")
    content = open(path).read()
    assert 'rel="manifest"' in content
    assert "manifest.json" in content


def test_layout_theme_color():
    """layout.tsx should have meta theme-color."""
    path = os.path.join(SRC, "app", "layout.tsx")
    content = open(path).read()
    assert "theme-color" in content
    assert "#2563EB" in content
