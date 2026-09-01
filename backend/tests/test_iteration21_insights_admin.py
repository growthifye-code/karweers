"""Iteration 21 — SK Insights admin: featured, tracking, analytics, admin edit/refresh/editions/newsletter."""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://energy-strategy-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASS = "Sudarshan@2026"

TEST_SLUG = "energy-strategy-hub"  # per review request
FEATURE_SLUG = "energy-strategy-hub"


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


@pytest.fixture(scope="module")
def auth_h(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def real_slug(s, admin_token):
    """Pick a real slug that exists — prefer TEST_SLUG if present, otherwise first from list."""
    h = {"Authorization": f"Bearer {admin_token}"}
    r = s.get(f"{API}/admin/service-insights", headers=h)
    assert r.status_code == 200, r.text
    rows = r.json()
    slugs = [x["slug"] for x in rows]
    if TEST_SLUG in slugs:
        return TEST_SLUG
    return slugs[0]


# ---------- Featured insight ----------
def test_featured_returns_card_with_sk_take(s):
    r = s.get(f"{API}/service-insights-featured")
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d, dict) and d, "expected non-empty card"
    for k in ("slug", "title"):
        assert k in d, f"missing {k}"
    assert "sk_take" in d, "sk_take should be present (possibly empty string)"


def test_feature_requires_admin(s, real_slug):
    r = s.post(f"{API}/admin/service-insights/{real_slug}/feature")
    assert r.status_code in (401, 403), r.status_code


def test_feature_pin_and_verify(s, auth_h, real_slug):
    r = s.post(f"{API}/admin/service-insights/{real_slug}/feature", headers=auth_h)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("success") is True
    assert body.get("featured") == real_slug
    r2 = s.get(f"{API}/service-insights-featured")
    assert r2.status_code == 200
    assert r2.json().get("slug") == real_slug


# ---------- Reading & share tracking ----------
def test_track_view(s, real_slug):
    r = s.post(f"{API}/insights/track", json={"slug": real_slug, "event": "view"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_track_share_with_platform(s, real_slug):
    r = s.post(f"{API}/insights/track", json={"slug": real_slug, "event": "share", "platform": "linkedin"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_track_unknown_slug_silently_accepted(s):
    r = s.post(f"{API}/insights/track", json={"slug": "does-not-exist-xyz-123", "event": "view"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_track_invalid_event_400(s, real_slug):
    r = s.post(f"{API}/insights/track", json={"slug": real_slug, "event": "bogus"})
    assert r.status_code == 400


# ---------- Analytics ----------
def test_analytics_requires_admin(s):
    r = s.get(f"{API}/admin/insights/analytics")
    assert r.status_code in (401, 403)


def test_analytics_structure_and_reflects_tracks(s, auth_h, real_slug):
    r = s.get(f"{API}/admin/insights/analytics", headers=auth_h)
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("total_reads", "total_shares", "top_read", "top_shared", "by_theme"):
        assert k in d, f"missing {k}"
    assert isinstance(d["top_read"], list)
    assert isinstance(d["top_shared"], list)
    assert isinstance(d["by_theme"], list)
    assert d["total_reads"] >= 1
    assert d["total_shares"] >= 1
    # The slug we tracked should be in top_read
    top_slugs = [row.get("slug") for row in d["top_read"]]
    assert real_slug in top_slugs, f"tracked slug {real_slug} not in top_read {top_slugs}"


# ---------- Admin list ----------
def test_admin_list_requires_admin(s):
    r = s.get(f"{API}/admin/service-insights")
    assert r.status_code in (401, 403)


def test_admin_list_rows(s, auth_h):
    r = s.get(f"{API}/admin/service-insights", headers=auth_h)
    assert r.status_code == 200
    rows = r.json()
    assert isinstance(rows, list)
    assert len(rows) >= 80, f"expected >=80 rows, got {len(rows)}"
    required = {"slug", "title", "service_title", "category", "sort", "version", "featured", "reads", "shares", "editions"}
    missing = required - set(rows[0].keys())
    assert not missing, f"missing keys: {missing}"
    # at least one row must be featured
    assert any(r.get("featured") for r in rows), "no featured row after pin"


# ---------- Admin edit ----------
def test_admin_edit_requires_admin(s, real_slug):
    r = s.patch(f"{API}/admin/service-insights/{real_slug}", json={"dek": "no-auth"})
    assert r.status_code in (401, 403)


def test_admin_edit_dek_and_sort_persists(s, auth_h, real_slug):
    new_dek = f"edited standfirst {int(time.time())}"
    r = s.patch(f"{API}/admin/service-insights/{real_slug}",
                json={"dek": new_dek, "sort": 5}, headers=auth_h)
    assert r.status_code == 200, r.text
    assert r.json().get("success") is True
    r2 = s.get(f"{API}/service-insights/{real_slug}")
    assert r2.status_code == 200
    assert r2.json().get("dek") == new_dek


# ---------- Editions (archive list) ----------
def test_editions_requires_admin(s, real_slug):
    r = s.get(f"{API}/admin/service-insights/{real_slug}/editions")
    assert r.status_code in (401, 403)


def test_editions_returns_list(s, auth_h, real_slug):
    r = s.get(f"{API}/admin/service-insights/{real_slug}/editions", headers=auth_h)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# ---------- Refresh (real Claude call — ONE slug only) ----------
def test_refresh_requires_admin(s, real_slug):
    r = s.post(f"{API}/admin/service-insights/{real_slug}/refresh")
    assert r.status_code in (401, 403)


@pytest.mark.slow
def test_refresh_single_slug_and_archives_edition(s, auth_h, real_slug):
    # Snapshot prior editions count
    e0 = s.get(f"{API}/admin/service-insights/{real_slug}/editions", headers=auth_h).json()
    prior_count = len(e0)
    r = s.post(f"{API}/admin/service-insights/{real_slug}/refresh",
               headers=auth_h, timeout=90)
    assert r.status_code == 200, r.text
    assert r.json().get("success") is True
    e1 = s.get(f"{API}/admin/service-insights/{real_slug}/editions", headers=auth_h).json()
    assert len(e1) >= max(1, prior_count + 1), f"editions did not grow: {prior_count} -> {len(e1)}"


# ---------- Newsletter run — auth-only (do NOT trigger a real send) ----------
def test_newsletter_run_requires_admin(s):
    r = s.post(f"{API}/admin/insights-newsletter/run")
    assert r.status_code in (401, 403)
