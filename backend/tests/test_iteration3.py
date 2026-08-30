"""Iteration-3 backend tests: hCaptcha enforcement, services, deals, bookings, security headers, SEO."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
ROOT = BASE_URL.rstrip("/")
API = f"{ROOT}/api"

ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASSWORD = "Sudarshan@2026"
# hCaptcha test sitekey / any non-empty response passes with 0x000..0 test secret
CAPTCHA = "10000000-aaaa-bbbb-cccc-000000000001"


@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(f"{API}/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": CAPTCHA},
                      timeout=30)
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


# ---------------- hCaptcha enforcement ----------------
class TestCaptchaEnforcement:
    def test_login_missing_captcha_400(self):
        r = requests.post(f"{API}/auth/login",
                          json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=15)
        assert r.status_code == 400, r.text

    def test_register_missing_captcha_400(self):
        r = requests.post(f"{API}/auth/register",
                          json={"name": "X", "email": f"tst_{uuid.uuid4().hex[:6]}@e.com", "password": "Pass@1234"},
                          timeout=15)
        assert r.status_code == 400

    def test_consultation_missing_captcha_400(self):
        r = requests.post(f"{API}/consultations",
                          json={"name": "X", "email": "x@e.com", "area": "RE", "message": "hi"}, timeout=15)
        assert r.status_code == 400

    def test_newsletter_missing_captcha_400(self):
        r = requests.post(f"{API}/newsletter", json={"email": f"tst_{uuid.uuid4().hex[:6]}@e.com"}, timeout=15)
        assert r.status_code == 400

    def test_checkout_missing_captcha_400(self):
        r = requests.post(f"{API}/payments/checkout",
                          json={"package_id": "discovery", "origin_url": "https://example.com",
                                "name": "X", "email": "x@e.com"}, timeout=15)
        assert r.status_code == 400

    def test_login_with_captcha_ok(self):
        r = requests.post(f"{API}/auth/login",
                          json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": CAPTCHA},
                          timeout=20)
        assert r.status_code == 200
        assert "token" in r.json()

    def test_consultation_with_captcha_ok(self):
        r = requests.post(f"{API}/consultations",
                          json={"name": "TEST Consult", "email": f"tst_c_{uuid.uuid4().hex[:6]}@e.com",
                                "area": "Renewables", "message": "please advise", "captcha_token": CAPTCHA},
                          timeout=20)
        assert r.status_code == 200
        assert r.json().get("success") is True

    def test_newsletter_with_captcha_ok(self):
        email = f"tst_n_{uuid.uuid4().hex[:6]}@e.com"
        r = requests.post(f"{API}/newsletter",
                          json={"email": email, "captcha_token": CAPTCHA}, timeout=20)
        assert r.status_code == 200
        assert r.json().get("success") is True


# ---------------- Services ----------------
class TestServices:
    def test_list_services(self):
        r = requests.get(f"{API}/services", timeout=15)
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list) and len(arr) == 5
        slugs = {s["slug"] for s in arr}
        expected = {"premium-consultation", "re-storage-hydrogen", "green-climate-financing",
                    "asset-monetisation", "business-coaching"}
        assert expected.issubset(slugs)
        for s in arr:
            for k in ("slug", "title", "tagline", "overview", "portrait", "hero_image"):
                assert k in s and s[k]

    def test_service_detail(self):
        # sample slug from features_or_bugs_to_test
        r = requests.get(f"{API}/services/business-coaching", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert d["slug"] == "business-coaching"
        assert "workflow" in d and isinstance(d["workflow"], list) and len(d["workflow"]) >= 1
        assert "approach" in d and len(d["approach"]) >= 1
        assert "outcomes" in d and len(d["outcomes"]) >= 1
        # phase keys used by URL /services/:slug/:phase
        keys = {p["key"] for p in d["workflow"]}
        assert "baseline" in keys
        for phase in d["workflow"]:
            for k in ("key", "title", "summary", "detail", "steps"):
                assert k in phase

    def test_service_energy_hub_placeholder_should_404(self):
        # The request mentions /api/services/energy-strategy-hub — no such slug exists in services_data.
        # Unknown slugs must return 404
        r = requests.get(f"{API}/services/energy-strategy-hub", timeout=15)
        assert r.status_code == 404

    def test_service_unknown_404(self):
        r = requests.get(f"{API}/services/not-a-service", timeout=15)
        assert r.status_code == 404


# ---------------- Deals ----------------
class TestDeals:
    def test_deals_endpoint(self):
        r = requests.get(f"{API}/deals", timeout=25)
        assert r.status_code == 200
        d = r.json()
        assert "data" in d and isinstance(d["data"], list)
        # Empty (rate-limited) feed treated as soft/non-blocking. If populated, sanity check fields.
        if d["data"]:
            it = d["data"][0]
            for k in ("title", "link"):
                assert k in it


# ---------------- Bookings schedule ----------------
class TestBookings:
    def test_schedule_requires_paid(self):
        # Create checkout to get a session_id in payment_pending state
        c = requests.post(f"{API}/payments/checkout",
                          json={"package_id": "discovery", "origin_url": "https://example.com",
                                "name": "TEST Book", "email": f"tst_b_{uuid.uuid4().hex[:6]}@e.com",
                                "captcha_token": CAPTCHA}, timeout=30)
        assert c.status_code == 200
        sid = c.json()["session_id"]
        r = requests.post(f"{API}/bookings/schedule",
                          json={"session_id": sid, "start": "2026-02-01T10:00:00Z", "end": "2026-02-01T11:00:00Z"},
                          timeout=15)
        assert r.status_code == 402, r.text

    def test_schedule_unknown_session_404(self):
        r = requests.post(f"{API}/bookings/schedule",
                          json={"session_id": "no-such-session", "start": "2026-02-01T10:00:00Z",
                                "end": "2026-02-01T11:00:00Z"}, timeout=15)
        assert r.status_code == 404

    def test_schedule_success_when_paid(self):
        # Simulate paid state by inserting into DB via admin — we can't easily.
        # Instead: create checkout, then flip payment_status through direct backend call is not exposed.
        # We rely on the /payments/status polling that would flip if paid; skipping unless env allows.
        pytest.skip("Cannot complete Stripe hosted-page payment automatically; covered by 402 path.")


# ---------------- Security headers ----------------
class TestSecurityHeaders:
    def test_headers_present(self):
        r = requests.get(f"{API}/", timeout=15)
        assert r.status_code == 200
        h = {k.lower(): v for k, v in r.headers.items()}
        assert h.get("x-content-type-options") == "nosniff"
        assert "x-frame-options" in h
        assert "referrer-policy" in h


# ---------------- SEO ----------------
class TestSEO:
    def test_robots_txt(self):
        r = requests.get(f"{ROOT}/robots.txt", timeout=15)
        assert r.status_code == 200
        assert "user-agent" in r.text.lower() or "sitemap" in r.text.lower()

    def test_sitemap_xml(self):
        r = requests.get(f"{ROOT}/sitemap.xml", timeout=15)
        assert r.status_code == 200
        assert "<urlset" in r.text or "<sitemapindex" in r.text


# ---------------- Regression: admin locked to sudarshan ----------------
class TestAdminLock:
    def test_new_user_is_client_not_admin(self, admin_headers):
        email = f"tst_client_{uuid.uuid4().hex[:6]}@e.com"
        r = requests.post(f"{API}/auth/register",
                          json={"name": "Reg Test", "email": email, "password": "Pass@1234",
                                "captcha_token": CAPTCHA}, timeout=20)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "client"
        # non-admin cannot access admin endpoints
        token = r.json()["token"]
        s = requests.get(f"{API}/admin/stats", headers={"Authorization": f"Bearer {token}"}, timeout=15)
        assert s.status_code == 403

    def test_admin_can_list_consultations(self, admin_headers):
        r = requests.get(f"{API}/consultations", headers=admin_headers, timeout=15)
        assert r.status_code == 200
        assert isinstance(r.json(), list)
