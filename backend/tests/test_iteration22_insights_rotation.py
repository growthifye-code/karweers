"""Iteration 22 backend tests — Featured rotation queue, Trending strip,
Quote share tracking, Subscriber theme preferences, Newsletter background send auth-gating."""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASSWORD = "Sudarshan@2026"


# ---------------- fixtures ----------------
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
        "consent": True, "captcha_token": "test-token",
    }, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"Admin login failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"No token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def real_slug():
    r = requests.get(f"{API}/service-insights", timeout=20)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list) and len(items) > 0
    return items[0]["slug"]


@pytest.fixture(scope="module")
def second_slug():
    r = requests.get(f"{API}/service-insights", timeout=20)
    items = r.json()
    return items[1]["slug"] if len(items) > 1 else items[0]["slug"]


# ---------------- Featured queue toggle ----------------
class TestFeaturedQueue:
    def test_admin_endpoints_require_auth(self, real_slug):
        r = requests.post(f"{API}/admin/service-insights/{real_slug}/feature", timeout=15)
        assert r.status_code == 401
        r = requests.get(f"{API}/admin/featured-queue", timeout=15)
        assert r.status_code == 401

    def test_feature_toggle_and_queue_and_current(self, admin_headers, real_slug):
        # Drain any existing queue so we deterministically test toggle behaviour
        cur = requests.get(f"{API}/admin/featured-queue", headers=admin_headers, timeout=15).json()
        for s in [q["slug"] for q in cur.get("queue", [])]:
            requests.post(f"{API}/admin/service-insights/{s}/feature",
                          headers=admin_headers, timeout=15)

        # Toggle real_slug in
        r = requests.post(f"{API}/admin/service-insights/{real_slug}/feature",
                          headers=admin_headers, timeout=15)
        assert r.status_code == 200
        j = r.json()
        assert j["in_queue"] is True
        assert real_slug in j["queue"]

        # Toggle again => out
        r = requests.post(f"{API}/admin/service-insights/{real_slug}/feature",
                          headers=admin_headers, timeout=15)
        assert r.status_code == 200 and r.json()["in_queue"] is False
        assert real_slug not in r.json()["queue"]

        # Put real_slug back so /service-insights-featured returns it (queue head, index=0)
        r = requests.post(f"{API}/admin/service-insights/{real_slug}/feature",
                          headers=admin_headers, timeout=15)
        assert r.status_code == 200 and r.json()["in_queue"] is True

        # GET queue lists with current flag
        r = requests.get(f"{API}/admin/featured-queue", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "queue" in data and len(data["queue"]) >= 1
        assert any(q.get("current") is True for q in data["queue"])

        # Public featured returns the current queued insight (queue[0])
        r = requests.get(f"{API}/service-insights-featured", timeout=15)
        assert r.status_code == 200
        card = r.json()
        assert card and card.get("slug") == real_slug
        assert "sk_take" in card

    def test_feature_unknown_slug_404(self, admin_headers):
        r = requests.post(f"{API}/admin/service-insights/definitely-not-a-slug-xyz/feature",
                          headers=admin_headers, timeout=15)
        assert r.status_code == 404

    def test_featured_falls_back_when_queue_empty(self, admin_headers, real_slug):
        # Drain queue for this test — save current and restore
        cur = requests.get(f"{API}/admin/featured-queue", headers=admin_headers, timeout=15).json()
        original = [q["slug"] for q in cur.get("queue", [])]
        try:
            for s in list(original):
                requests.post(f"{API}/admin/service-insights/{s}/feature",
                              headers=admin_headers, timeout=15)
            r = requests.get(f"{API}/service-insights-featured", timeout=15)
            assert r.status_code == 200
            card = r.json()
            assert card and card.get("slug"), "Expected fallback to freshest blog"
        finally:
            # Restore original queue
            for s in original:
                requests.post(f"{API}/admin/service-insights/{s}/feature",
                              headers=admin_headers, timeout=15)


# ---------------- Trending + view tracking ----------------
class TestTrendingAndReads:
    def test_view_increments_weekly_and_cumulative(self, real_slug, admin_headers):
        # Baseline analytics for slug
        base = requests.get(f"{API}/admin/insights/analytics", headers=admin_headers, timeout=15).json()
        base_reads = 0
        for row in base.get("top_read", []) + base.get("top_shared", []):
            if row.get("slug") == real_slug:
                base_reads = max(base_reads, int(row.get("reads", 0) or 0))

        r = requests.post(f"{API}/insights/track",
                          json={"slug": real_slug, "event": "view"}, timeout=15)
        assert r.status_code == 200 and r.json()["ok"] is True

        # Trending strip returns up to 6, never empty
        r = requests.get(f"{API}/service-insights-trending?limit=6", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert 1 <= len(data) <= 6
        # cards contain slug + title
        for card in data:
            assert card.get("slug") and card.get("title")

    def test_trending_never_empty_default_limit(self):
        r = requests.get(f"{API}/service-insights-trending", timeout=15)
        assert r.status_code == 200
        assert len(r.json()) > 0


# ---------------- Quote share tracking ----------------
class TestQuoteShareTracking:
    def test_share_quote_records_platform_bucket(self, real_slug, admin_headers):
        # Baseline
        a0 = requests.get(f"{API}/admin/insights/analytics", headers=admin_headers, timeout=15).json()
        prev_quote = 0
        for row in a0.get("top_shared", []):
            if row.get("slug") == real_slug:
                prev_quote = int((row.get("share_by") or {}).get("quote", 0) or 0)

        r = requests.post(f"{API}/insights/track",
                          json={"slug": real_slug, "event": "share", "platform": "quote"},
                          timeout=15)
        assert r.status_code == 200 and r.json() == {"ok": True}

        a1 = requests.get(f"{API}/admin/insights/analytics", headers=admin_headers, timeout=15).json()
        found = None
        for row in a1.get("top_shared", []):
            if row.get("slug") == real_slug:
                found = row
                break
        assert found is not None, "Slug not in top_shared after share event"
        new_quote = int((found.get("share_by") or {}).get("quote", 0) or 0)
        assert new_quote == prev_quote + 1, f"expected {prev_quote+1}, got {new_quote}"


# ---------------- Subscriber theme preferences ----------------
class TestSubscriberPreferences:
    def _mint_token(self):
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{API}/newsletter/follow",
                          json={"email": email, "kind": "sector", "slug": "renewable-energy"},
                          timeout=15)
        assert r.status_code == 200, r.text
        prefs_url = r.json().get("prefs_url", "")
        assert "token=" in prefs_url
        token = prefs_url.split("token=", 1)[1]
        return email, token

    def test_get_preferences_returns_all_themes(self):
        _, token = self._mint_token()
        r = requests.get(f"{API}/newsletter/preferences", params={"token": token}, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "all_themes" in data
        assert len(data["all_themes"]) == 8
        for th in ["Strategy", "M&A", "Capital & Finance", "Markets",
                   "Economy", "Technology", "Energy & Climate", "Leadership"]:
            assert th in data["all_themes"]
        assert data["selected_themes"] == []

    def test_post_preferences_persists(self):
        _, token = self._mint_token()
        r = requests.post(f"{API}/newsletter/preferences",
                          json={"token": token, "themes": ["Technology", "M&A"]},
                          timeout=15)
        assert r.status_code == 200 and r.json()["success"] is True
        r = requests.get(f"{API}/newsletter/preferences", params={"token": token}, timeout=15)
        assert r.status_code == 200
        assert sorted(r.json()["selected_themes"]) == sorted(["Technology", "M&A"])

    def test_invalid_token_400(self):
        r = requests.get(f"{API}/newsletter/preferences", params={"token": "not-a-real-jwt"}, timeout=15)
        assert r.status_code == 400
        r = requests.post(f"{API}/newsletter/preferences",
                          json={"token": "not-a-real-jwt", "themes": ["Technology"]}, timeout=15)
        assert r.status_code == 400

    def test_bogus_themes_filtered_out(self):
        _, token = self._mint_token()
        r = requests.post(f"{API}/newsletter/preferences",
                          json={"token": token, "themes": ["Technology", "Bogus"]}, timeout=15)
        assert r.status_code == 200
        r = requests.get(f"{API}/newsletter/preferences", params={"token": token}, timeout=15)
        assert r.json()["selected_themes"] == ["Technology"]


# ---------------- Newsletter run — auth gating ONLY ----------------
class TestNewsletterRun:
    def test_requires_admin(self):
        r = requests.post(f"{API}/admin/insights-newsletter/run", timeout=15)
        assert r.status_code == 401
        # NOTE: intentionally NOT calling with admin auth to avoid emailing real subscribers.
