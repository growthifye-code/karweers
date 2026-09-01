"""Iteration 23 - Auto-feature winner, Weekly recap, Theme signup, Related-by-theme."""
import os
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE}/api"
ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASS = "Sudarshan@2026"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASS,
        "consent": True, "captcha_token": "test-token"
    }, timeout=30)
    assert r.status_code == 200, f"Admin login failed: {r.status_code} {r.text}"
    return r.json()["access_token"] if "access_token" in r.json() else r.json().get("token")


@pytest.fixture(scope="module")
def real_slug():
    r = requests.get(f"{API}/service-insights", timeout=30)
    assert r.status_code == 200
    payload = r.json()
    items = payload if isinstance(payload, list) else (payload.get("items") or [])
    for it in items:
        if it.get("slug"):
            return it["slug"]
    raise AssertionError("no slug found in service-insights")


# ---------- Auth gating ----------
def test_recap_preview_requires_auth():
    r = requests.get(f"{API}/admin/insights/recap-preview?week=current", timeout=15)
    assert r.status_code in (401, 403)


def test_recap_run_requires_auth():
    r = requests.post(f"{API}/admin/insights/recap-run?week=current", timeout=15)
    assert r.status_code in (401, 403)


def test_auto_feature_run_requires_auth():
    r = requests.post(f"{API}/admin/insights/auto-feature-run?week=current", timeout=15)
    assert r.status_code in (401, 403)


# ---------- Auto-feature winner ----------
def test_auto_feature_winner(admin_token, real_slug):
    # Track several views this week to make real_slug the top read
    for _ in range(6):
        r = requests.post(f"{API}/insights/track", json={"slug": real_slug, "event": "view"}, timeout=10)
        assert r.status_code == 200
    hdr = {"Authorization": f"Bearer {admin_token}"}
    r = requests.post(f"{API}/admin/insights/auto-feature-run?week=current", headers=hdr, timeout=20)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("success") is True
    assert data.get("winner") == real_slug, f"expected {real_slug}, got {data.get('winner')}"

    # Featured endpoint should now reflect winner
    r2 = requests.get(f"{API}/service-insights-featured", timeout=15)
    assert r2.status_code == 200
    feat = r2.json()
    slug_out = feat.get("slug") or (feat.get("insight") or {}).get("slug")
    assert slug_out == real_slug, f"featured slug mismatch: {slug_out} vs {real_slug} :: {feat}"


# ---------- Weekly recap preview ----------
def test_recap_preview_structure(admin_token, real_slug):
    # add a share to enrich preview
    r = requests.post(f"{API}/insights/track",
                      json={"slug": real_slug, "event": "share", "platform": "quote"}, timeout=10)
    assert r.status_code == 200
    hdr = {"Authorization": f"Bearer {admin_token}"}
    r = requests.get(f"{API}/admin/insights/recap-preview?week=current", headers=hdr, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    for k in ("total_reads", "total_shares", "top_read", "top_shared", "by_theme"):
        assert k in d, f"missing key {k} in {d}"
    assert isinstance(d["top_read"], list) and isinstance(d["by_theme"], list)
    assert d["total_reads"] >= 6
    assert d["total_shares"] >= 1
    # our slug should appear in top_read
    slugs = [x.get("slug") for x in d["top_read"]]
    assert real_slug in slugs
    shared_slugs = [x.get("slug") for x in d["top_shared"]]
    assert real_slug in shared_slugs


def test_recap_run_admin(admin_token):
    hdr = {"Authorization": f"Bearer {admin_token}"}
    r = requests.post(f"{API}/admin/insights/recap-run?week=current", headers=hdr, timeout=20)
    assert r.status_code == 200, r.text
    d = r.json()
    # Either queued to send OR skipped because email not configured
    assert (d.get("sent") is True and d.get("queued") is True) or d.get("skipped") == "email_not_configured", d


# ---------- Theme signup ----------
TEST_EMAIL = "themesignup_test@example.com"


def test_newsletter_theme_signup():
    r = requests.post(f"{API}/newsletter", json={
        "email": TEST_EMAIL, "captcha_token": "x",
        "themes": ["Technology", "M&A", "NotARealTheme"]
    }, timeout=15)
    assert r.status_code == 200, r.text
    assert r.json().get("success") is True

    # idempotent
    r2 = requests.post(f"{API}/newsletter", json={
        "email": TEST_EMAIL, "captcha_token": "x",
        "themes": ["Technology", "M&A"]
    }, timeout=15)
    assert r2.status_code == 200
    assert "already" in (r2.json().get("message") or "").lower()


def test_newsletter_theme_persisted(admin_token):
    hdr = {"Authorization": f"Bearer {admin_token}"}
    r = requests.get(f"{API}/newsletter", headers=hdr, timeout=15)
    assert r.status_code == 200
    subs = r.json()
    row = next((s for s in subs if s.get("email") == TEST_EMAIL), None)
    assert row is not None, f"subscriber {TEST_EMAIL} not found"
    themes = row.get("interests_themes") or []
    assert "Technology" in themes and "M&A" in themes
    assert "NotARealTheme" not in themes


def test_cleanup_test_subscriber(admin_token):
    """Cleanup - delete the test subscriber via mongo direct or admin api."""
    # Try admin delete endpoint patterns
    hdr = {"Authorization": f"Bearer {admin_token}"}
    for path in [f"/newsletter/{TEST_EMAIL}", f"/newsletter?email={TEST_EMAIL}",
                 f"/admin/newsletter/{TEST_EMAIL}"]:
        r = requests.delete(f"{API}{path}", headers=hdr, timeout=10)
        if r.status_code in (200, 204):
            return
    # Fallback via direct mongo
    try:
        from pymongo import MongoClient
        c = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))
        c[os.environ.get("DB_NAME", "test_database")].subscribers.delete_one({"email": TEST_EMAIL})
    except Exception as e:
        print(f"cleanup fallback: {e}")


# ---------- Related by theme ----------
def test_related_by_theme(real_slug):
    r = requests.get(f"{API}/service-insights/{real_slug}", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert "theme" in d and d["theme"], "theme missing"
    assert "related_by_theme" in d
    rel = d["related_by_theme"]
    assert isinstance(rel, list)
    assert len(rel) <= 4
    for card in rel:
        assert card.get("slug") != real_slug
