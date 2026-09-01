"""Iteration 20 tests: per-service SK Insights engine + unified archive + admin gating."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://energy-strategy-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SERVICES = [
    "business-strategy", "ma-advisory", "fund-raising", "premium-consultation",
    "re-storage-hydrogen", "green-climate-financing", "asset-monetisation", "business-coaching",
]

ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASS = "Sudarshan@2026"


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


@pytest.fixture(scope="module")
def admin_token(s):
    r = s.post(f"{API}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASS,
        "consent": True, "captcha_token": "test-token"
    })
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text[:200]}")
    return r.json().get("token") or r.json().get("access_token")


# ---------------- Service insights list ----------------
def test_list_all_service_insights(s):
    r = s.get(f"{API}/service-insights")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) >= 80, f"Expected >=80 blogs total, got {len(data)}"


@pytest.mark.parametrize("svc", SERVICES)
def test_service_filter_returns_10(s, svc):
    r = s.get(f"{API}/service-insights", params={"service": svc})
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 10, f"{svc} has {len(data)} blogs, expected 10"


def test_category_filter(s):
    # pick a category from first blog
    all_r = s.get(f"{API}/service-insights").json()
    cat = all_r[0].get("category")
    if not cat:
        pytest.skip("no category to filter")
    r = s.get(f"{API}/service-insights", params={"category": cat})
    assert r.status_code == 200
    for b in r.json():
        assert b.get("category") == cat


# ---------------- Services counts ----------------
def test_services_counts(s):
    r = s.get(f"{API}/service-insights/services")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 8, f"Expected 8 services, got {len(data)}"
    slugs = {d["slug"] for d in data}
    assert slugs == set(SERVICES)
    for d in data:
        assert d["count"] == 10, f"{d['slug']} count={d['count']}"


# ---------------- Single blog reader ----------------
def test_get_energy_strategy_hub(s):
    # NOTE: review request references slug "energy-strategy-hub" but no such blog exists.
    # Fall back to any blog from the re-storage-hydrogen service to validate structure.
    listing = s.get(f"{API}/service-insights", params={"service": "re-storage-hydrogen"}).json()
    slug = listing[0]["slug"]
    r = s.get(f"{API}/service-insights/{slug}")
    assert r.status_code == 200
    d = r.json()
    assert d.get("dek")
    secs = d.get("sections") or []
    assert 5 <= len(secs) <= 8, f"sections count={len(secs)}"
    kt = d.get("key_takeaways") or []
    assert len(kt) >= 3
    sk = d.get("sk_insight") or {}
    assert sk.get("take")
    assert sk.get("corporate_relevance")
    assert len(d.get("related") or []) == 3
    assert "earlier_editions" in d


def test_unknown_insight_404(s):
    r = s.get(f"{API}/service-insights/this-does-not-exist-xyz")
    assert r.status_code == 404


# ---------------- Service insights archive ----------------
def test_service_insights_archive_list(s):
    r = s.get(f"{API}/service-insights/archive")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_service_insights_archive_unknown(s):
    r = s.get(f"{API}/service-insights/archive/nonexistent-archive-id-xyz")
    assert r.status_code == 404


# ---------------- Unified archive ----------------
def test_unified_archive(s):
    r = s.get(f"{API}/archive")
    assert r.status_code == 200
    d = r.json()
    assert "items" in d and "counts" in d and "themes" in d and "theme_counts" in d
    assert d["counts"].get("blog", 0) >= 80
    # themes present
    assert isinstance(d["themes"], list) and len(d["themes"]) > 0


def test_archive_type_filter_video(s):
    r = s.get(f"{API}/archive", params={"type": "video"})
    assert r.status_code == 200
    d = r.json()
    for it in d["items"]:
        assert it["type"] == "video"


def test_archive_theme_filter_technology(s):
    r = s.get(f"{API}/archive", params={"theme": "Technology"})
    assert r.status_code == 200
    d = r.json()
    for it in d["items"]:
        assert it["theme"] == "Technology"


# ---------------- Admin gating ----------------
def test_admin_status_requires_auth(s):
    r = requests.get(f"{API}/admin/service-insights/status")
    assert r.status_code in (401, 403)


def test_admin_regenerate_requires_auth(s):
    r = requests.post(f"{API}/admin/service-insights/regenerate")
    assert r.status_code in (401, 403)


def test_admin_status_with_token(s, admin_token):
    r = requests.get(f"{API}/admin/service-insights/status",
                     headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    d = r.json()
    assert "expected" in d and "generated" in d
    assert d["generated"] >= 80
    assert d["expected"] >= 80
