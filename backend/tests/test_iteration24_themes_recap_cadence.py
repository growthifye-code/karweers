"""Iteration 24 — SK Insights: themes API, trending slugs, recap cadence."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASS = "Sudarshan@2026"

EXPECTED_THEME_SLUGS = {"strategy", "m-and-a", "capital-finance", "economy",
                       "technology", "energy-climate", "leadership"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASS,
        "consent": True, "captcha_token": "test-token"
    }, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------- Themes API ----------
class TestThemesAPI:
    def test_list_themes(self):
        r = requests.get(f"{API}/service-insights-themes", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) > 0
        slugs = {t["slug"] for t in data}
        # Every returned theme must have count > 0 and a slug in expected set
        for t in data:
            assert t["count"] > 0
            assert t["slug"] in EXPECTED_THEME_SLUGS | {"markets"}
            assert "blurb" in t and isinstance(t["blurb"], str)
            assert "theme" in t
        # Expected core themes should be present (markets may be zero)
        # At minimum technology + strategy present.
        assert "technology" in slugs
        assert "strategy" in slugs

    def test_theme_technology(self):
        r = requests.get(f"{API}/service-insights-theme/technology", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert data["theme"] == "Technology"
        assert data["slug"] == "technology"
        assert data["count"] >= 1
        assert isinstance(data["items"], list)
        assert len(data["items"]) == data["count"]
        # each item is a blog card w/ slug + title
        for it in data["items"]:
            assert "slug" in it and "title" in it

    def test_theme_invalid_404(self):
        r = requests.get(f"{API}/service-insights-theme/not-a-real-theme", timeout=15)
        assert r.status_code == 404


# ---------- Trending slugs ----------
class TestTrendingSlugs:
    def test_default(self):
        r = requests.get(f"{API}/service-insights-trending-slugs", timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_tracked_view_appears_with_min1(self):
        # Get a real slug
        r = requests.get(f"{API}/service-insights", timeout=15)
        assert r.status_code == 200
        slugs = [x["slug"] for x in r.json()][:1]
        assert slugs, "no insights to track"
        slug = slugs[0]
        # Track 3 views to be safe
        for _ in range(3):
            tr = requests.post(f"{API}/insights/track",
                              json={"slug": slug, "event": "view"}, timeout=15)
            assert tr.status_code == 200
        time.sleep(1)
        r = requests.get(f"{API}/service-insights-trending-slugs",
                         params={"min_reads": 1}, timeout=15)
        assert r.status_code == 200
        assert slug in r.json()


# ---------- Reader detail has theme + theme_slug + related_by_theme ----------
class TestReaderThemeFields:
    def test_energy_strategy_hub_or_first_slug(self):
        r = requests.get(f"{API}/service-insights", timeout=15)
        slugs = [x["slug"] for x in r.json()]
        # try energy-strategy-hub first, then first real slug
        target = "energy-strategy-hub" if "energy-strategy-hub" in slugs else slugs[0]
        r = requests.get(f"{API}/service-insights/{target}", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "theme" in data and data["theme"]
        assert "theme_slug" in data and data["theme_slug"]
        assert "related_by_theme" in data
        assert isinstance(data["related_by_theme"], list)


# ---------- Recap Cadence ----------
class TestRecapCadence:
    def test_401_without_token(self):
        r = requests.get(f"{API}/admin/insights/recap-settings", timeout=15)
        assert r.status_code in (401, 403)
        r2 = requests.post(f"{API}/admin/insights/recap-settings",
                          json={"cadence": "monthly"}, timeout=15)
        assert r2.status_code in (401, 403)

    def test_get_returns_cadence(self, admin_headers):
        r = requests.get(f"{API}/admin/insights/recap-settings",
                        headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert "cadence" in r.json()

    def test_invalid_cadence_400(self, admin_headers):
        r = requests.post(f"{API}/admin/insights/recap-settings",
                        headers=admin_headers,
                        json={"cadence": "hourly"}, timeout=15)
        assert r.status_code == 400

    def test_set_monthly_then_reset_weekly(self, admin_headers):
        # Set monthly
        r = requests.post(f"{API}/admin/insights/recap-settings",
                        headers=admin_headers,
                        json={"cadence": "monthly"}, timeout=15)
        assert r.status_code == 200
        assert r.json().get("cadence") == "monthly"
        # Verify persistence via GET
        g = requests.get(f"{API}/admin/insights/recap-settings",
                        headers=admin_headers, timeout=15)
        assert g.json()["cadence"] == "monthly"
        # RESET to weekly (mandatory per review request)
        r2 = requests.post(f"{API}/admin/insights/recap-settings",
                        headers=admin_headers,
                        json={"cadence": "weekly"}, timeout=15)
        assert r2.status_code == 200
        g2 = requests.get(f"{API}/admin/insights/recap-settings",
                        headers=admin_headers, timeout=15)
        assert g2.json()["cadence"] == "weekly"
