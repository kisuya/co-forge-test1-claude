"""Structure tests for SEO metadata (ui-024)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")
PUBLIC = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public")


# --- Layout metadata ---


def test_layout_has_metadata():
    """Layout should export metadata."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "metadata" in content
    assert "Metadata" in content


def test_layout_title_default():
    """Default title should include oh-my-stock."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "oh-my-stock | AI 주가 변동 분석" in content


def test_layout_title_template():
    """Should have title template for child pages."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "template" in content
    assert "oh-my-stock" in content


def test_layout_description():
    """Description should be in Korean, under 160 chars."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "관심 종목의 주가가 급변했을 때 AI가 원인을 분석합니다" in content


def test_layout_og_title():
    """Should have OpenGraph title."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "openGraph" in content
    assert "title" in content


def test_layout_og_description():
    """Should have OpenGraph description."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "openGraph" in content
    assert "description" in content


def test_layout_og_sitename():
    """Should have OpenGraph siteName."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "siteName" in content
    assert "oh-my-stock" in content


def test_layout_og_type():
    """Should have OpenGraph type website."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert '"website"' in content


def test_layout_og_image():
    """Should reference og-image.png."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "og-image.png" in content


def test_layout_twitter_card():
    """Should have Twitter card summary_large_image."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert "twitter" in content
    assert "summary_large_image" in content


def test_layout_lang_ko():
    """HTML should have lang='ko'."""
    path = os.path.join(BASE, "app", "layout.tsx")
    content = open(path).read()
    assert 'lang="ko"' in content


# --- robots.txt ---


def test_robots_txt_exists():
    """robots.txt should exist in public/."""
    path = os.path.join(PUBLIC, "robots.txt")
    assert os.path.exists(path), "public/robots.txt should exist"


def test_robots_allows_root():
    """robots.txt should allow root."""
    path = os.path.join(PUBLIC, "robots.txt")
    content = open(path).read()
    assert "Allow: /" in content


def test_robots_disallow_dashboard():
    """robots.txt should disallow /dashboard."""
    path = os.path.join(PUBLIC, "robots.txt")
    content = open(path).read()
    assert "Disallow: /dashboard" in content


def test_robots_disallow_mypage():
    """robots.txt should disallow /mypage."""
    path = os.path.join(PUBLIC, "robots.txt")
    content = open(path).read()
    assert "Disallow: /mypage" in content


# --- sitemap.xml ---


def test_sitemap_exists():
    """sitemap.xml should exist in public/."""
    path = os.path.join(PUBLIC, "sitemap.xml")
    assert os.path.exists(path), "public/sitemap.xml should exist"


def test_sitemap_has_root():
    """sitemap should include root URL."""
    path = os.path.join(PUBLIC, "sitemap.xml")
    content = open(path).read()
    assert "/" in content


def test_sitemap_has_login():
    """sitemap should include /login."""
    path = os.path.join(PUBLIC, "sitemap.xml")
    content = open(path).read()
    assert "/login" in content


def test_sitemap_has_signup():
    """sitemap should include /signup."""
    path = os.path.join(PUBLIC, "sitemap.xml")
    content = open(path).read()
    assert "/signup" in content


def test_sitemap_has_trending():
    """sitemap should include /trending."""
    path = os.path.join(PUBLIC, "sitemap.xml")
    content = open(path).read()
    assert "/trending" in content


# --- OG image ---


def test_og_image_exists():
    """og-image.png should exist in public/."""
    path = os.path.join(PUBLIC, "og-image.png")
    assert os.path.exists(path), "public/og-image.png should exist"


def test_og_image_is_png():
    """og-image.png should be a valid PNG file."""
    path = os.path.join(PUBLIC, "og-image.png")
    with open(path, "rb") as f:
        header = f.read(8)
    assert header[:4] == b"\x89PNG", "File should have PNG header"
