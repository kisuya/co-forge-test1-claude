"""Structure tests for report views and responsive design (ui-003)."""
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "src")


def test_alert_badge_component_exists():
    path = os.path.join(BASE, "components", "AlertBadge.tsx")
    assert os.path.isfile(path)


def test_alert_badge_has_spike_indicator():
    path = os.path.join(BASE, "components", "AlertBadge.tsx")
    content = open(path).read()
    assert "changePct" in content
    assert "data-testid" in content


def test_report_view_component_exists():
    path = os.path.join(BASE, "components", "ReportView.tsx")
    assert os.path.isfile(path)


def test_report_view_has_summary_and_causes():
    path = os.path.join(BASE, "components", "ReportView.tsx")
    content = open(path).read()
    assert "summary" in content
    assert "causes" in content
    assert "sources" in content


def test_report_view_shows_confidence():
    path = os.path.join(BASE, "components", "ReportView.tsx")
    content = open(path).read()
    assert "confidence" in content
    assert "high" in content
    assert "medium" in content
    assert "low" in content


def test_reports_list_page_exists():
    path = os.path.join(BASE, "app", "reports", "page.tsx")
    assert os.path.isfile(path)


def test_report_detail_page_exists():
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    assert os.path.isfile(path)


def test_report_detail_uses_report_view():
    path = os.path.join(BASE, "app", "reports", "[id]", "page.tsx")
    content = open(path).read()
    assert "ReportView" in content


def test_reports_by_stock_page_exists():
    path = os.path.join(BASE, "app", "reports", "stock", "[stockId]", "page.tsx")
    assert os.path.isfile(path)


def test_responsive_classes_in_report_view():
    """Check that responsive breakpoint classes (sm:, lg:) are used."""
    path = os.path.join(BASE, "components", "ReportView.tsx")
    content = open(path).read()
    assert "sm:" in content


def test_responsive_classes_in_reports_list():
    path = os.path.join(BASE, "app", "reports", "page.tsx")
    content = open(path).read()
    assert "sm:" in content


def test_responsive_classes_in_dashboard():
    path = os.path.join(BASE, "app", "dashboard", "page.tsx")
    content = open(path).read()
    assert "sm:" in content or "lg:" in content
