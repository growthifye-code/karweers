"""Iteration 9: AI homepage content engine + consent enforcement backend tests.

Covers:
  - GET /api/home/content shape (hero_headline w/ *asterisk*, hero_subtext, 3 insights, 5 feed items, generated_at)
  - POST /api/admin/home/regenerate (auth required; refreshes generated_at & shape)
  - GET /api/admin/consent-logs (+ /export CSV) auth + shape + records
  - Login/Register consent + captcha enforcement (captcha runs first — 400 without token)

hCaptcha is in STRICT mode with real keys, so a real valid captcha token
cannot be produced from a headless test. To exercise the admin-protected
endpoints we mint an admin JWT locally with the JWT_SECRET from backend/.env
(the auth mechanism is unchanged — verified in prior iterations).
"""
import os
import sys
import io
import csv
import time
import asyncio
import pytest
import requests

# Load JWT_SECRET & mint admin token by importing backend auth.
sys.path.insert(0, "/app/backend")
from auth import create_access_token  # noqa: E402

# --- Base URL ---
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
API = f"{BASE_URL.rstrip('/')}/api"

ADMIN_EMAIL = "sudarshan@karweers.com"
# Known admin user id from prior iterations (seeded/allowlisted admin).
ADMIN_UID = "f38ee7e0-033c-4c43-8a69-3bf31490e8e3"


@pytest.fixture(scope="module")
def admin_headers():
    tok = create_access_token(ADMIN_UID, ADMIN_EMAIL, "admin")
    return {"Authorization": f"Bearer {tok}"}


# ---------------- Home Content ----------------
class TestHomeContent:
    def test_home_content_shape(self):
        r = requests.get(f"{API}/home/content", timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert isinstance(d, dict) and d, "home content should not be empty"
        for k in ("hero_headline", "hero_subtext", "insights", "feed", "generated_at"):
            assert k in d, f"missing key {k}"
        # asterisk emphasis on some phrase
        assert "*" in d["hero_headline"], f"expected *asterisk* emphasis, got: {d['hero_headline']}"
        assert isinstance(d["hero_subtext"], str) and len(d["hero_subtext"]) > 30
        assert isinstance(d["insights"], list) and len(d["insights"]) == 3, \
            f"expected 3 insights, got {len(d.get('insights', []))}"
        assert all(isinstance(x, str) and x.strip() for x in d["insights"])
        assert isinstance(d["feed"], list) and len(d["feed"]) == 5, \
            f"expected 5 feed items, got {len(d.get('feed', []))}"
        for f in d["feed"]:
            assert isinstance(f, dict)
            for k in ("title", "take", "tag"):
                assert k in f and isinstance(f[k], str) and f[k].strip(), f"bad feed item {f}"

    def test_regenerate_requires_auth(self):
        r = requests.post(f"{API}/admin/home/regenerate", timeout=30)
        assert r.status_code in (401, 403), f"expected 401/403 for anon, got {r.status_code}"

    def test_regenerate_forbidden_for_non_admin(self, admin_headers):
        # non-admin JWT
        tok = create_access_token("nonadmin-uid", "nobody@example.com", "client")
        r = requests.post(f"{API}/admin/home/regenerate",
                          headers={"Authorization": f"Bearer {tok}"}, timeout=30)
        # 401 (user not found) or 403 (role check) both acceptable non-admin blocks.
        assert r.status_code in (401, 403)

    def test_regenerate_success(self, admin_headers):
        # Snapshot current generated_at
        before = requests.get(f"{API}/home/content", timeout=30).json()
        prev_ts = before.get("generated_at")
        r = requests.post(f"{API}/admin/home/regenerate", headers=admin_headers, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        # shape
        for k in ("hero_headline", "hero_subtext", "insights", "feed", "generated_at"):
            assert k in d, f"missing {k}"
        assert "*" in d["hero_headline"]
        assert len(d["insights"]) == 3
        assert len(d["feed"]) == 5
        # generated_at bumped
        assert d["generated_at"] != prev_ts, "generated_at should update after force regenerate"


# ---------------- Consent Logs (Admin) ----------------
class TestConsentLogs:
    def test_consent_logs_requires_auth(self):
        r = requests.get(f"{API}/admin/consent-logs", timeout=30)
        assert r.status_code in (401, 403)

    def test_consent_logs_forbidden_for_non_admin(self):
        tok = create_access_token("nonadmin-uid", "nobody@example.com", "client")
        r = requests.get(f"{API}/admin/consent-logs",
                         headers={"Authorization": f"Bearer {tok}"}, timeout=30)
        assert r.status_code in (401, 403)

    def test_consent_logs_shape(self, admin_headers):
        r = requests.get(f"{API}/admin/consent-logs", headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "logs" in d and "policy_version" in d and "total" in d
        assert isinstance(d["logs"], list)
        assert d["policy_version"] == "2026-06-01"
        assert d["total"] == len(d["logs"])
        # If any records exist, verify field structure
        if d["logs"]:
            rec = d["logs"][0]
            for k in ("email", "action", "agreed", "terms_version", "privacy_version",
                      "ip", "created_at"):
                assert k in rec, f"consent record missing key {k}: {rec}"
            assert rec["action"] in ("login", "register", "google")
            assert rec["agreed"] is True

    def test_consent_export_requires_auth(self):
        r = requests.get(f"{API}/admin/consent-logs/export", timeout=30)
        assert r.status_code in (401, 403)

    def test_consent_export_csv(self, admin_headers):
        r = requests.get(f"{API}/admin/consent-logs/export", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("text/csv")
        assert "consent-log.csv" in r.headers.get("content-disposition", "")
        text = r.text
        reader = csv.reader(io.StringIO(text))
        rows = list(reader)
        assert rows, "csv should have at least a header row"
        header = rows[0]
        for col in ("Timestamp (UTC)", "Name", "Email", "Action", "Agreed",
                    "Terms Version", "Privacy Version", "IP", "User Agent"):
            assert col in header, f"missing csv column {col}"


# ---------------- Consent + Captcha Enforcement on Auth ----------------
class TestAuthConsentEnforcement:
    """hCaptcha is verified FIRST — cannot bypass in tests. But we can prove
    captcha is enforced (400) which is the gate BEFORE consent. Consent
    enforcement in code is inspected in the /login and /register handlers
    (lines 255-256 and 607-608 of server.py).
    """

    def test_login_missing_captcha_rejected(self):
        r = requests.post(f"{API}/auth/login",
                          json={"email": ADMIN_EMAIL, "password": "irrelevant", "consent": True},
                          timeout=30)
        assert r.status_code in (400, 403), f"got {r.status_code} {r.text}"
        assert "captcha" in r.text.lower()

    def test_register_missing_captcha_rejected(self):
        r = requests.post(f"{API}/auth/register",
                          json={"email": "x@example.com", "password": "Test@1234",
                                "name": "X", "consent": True},
                          timeout=30)
        assert r.status_code in (400, 403)
        assert "captcha" in r.text.lower()

    def test_captcha_gate_missing_captcha_rejected(self):
        r = requests.post(f"{API}/auth/captcha-gate",
                          json={"consent": True}, timeout=30)
        assert r.status_code in (400, 403)
        assert "captcha" in r.text.lower()

    def test_session_without_gate_cookie_rejected(self):
        r = requests.post(f"{API}/auth/session",
                          json={"session_id": "fake"}, timeout=30)
        assert r.status_code == 403
        assert "captcha" in r.text.lower()


# ---------------- Direct consent-record insertion (verify CSV export includes it) ----------------
class TestConsentRecordPersistence:
    def test_direct_consent_insert_then_export(self, admin_headers):
        """Insert a synthetic consent record directly into Mongo, then verify
        it shows up in the admin list and CSV export."""
        import server as srv  # server rebound to fresh event loop by conftest fixture

        marker_email = f"test_consent_{int(time.time())}@example.com"
        doc = {
            "id": f"test-{int(time.time())}",
            "user_id": "",
            "email": marker_email,
            "name": "TEST Consent User",
            "action": "register",
            "agreed": True,
            "terms_version": "2026-06-01",
            "privacy_version": "2026-06-01",
            "ip": "127.0.0.1",
            "user_agent": "pytest",
            "created_at": "2026-01-15T00:00:00+00:00",
        }
        loop = asyncio.get_event_loop()
        loop.run_until_complete(srv.db.consent_logs.insert_one(dict(doc)))
        try:
            r = requests.get(f"{API}/admin/consent-logs", headers=admin_headers, timeout=30)
            assert r.status_code == 200
            emails = [x["email"] for x in r.json()["logs"]]
            assert marker_email in emails

            r2 = requests.get(f"{API}/admin/consent-logs/export",
                              headers=admin_headers, timeout=30)
            assert r2.status_code == 200
            assert marker_email in r2.text
        finally:
            loop.run_until_complete(srv.db.consent_logs.delete_one({"email": marker_email}))
