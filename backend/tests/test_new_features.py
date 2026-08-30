"""Backend tests for new features: payments (Stripe), market/live, newsletter."""
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
API = f"{BASE_URL.rstrip('/')}/api"

ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASSWORD = "Sudarshan@2026"


@pytest.fixture(scope="module")
def admin_headers():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200
    return {"Authorization": f"Bearer {r.json()['token']}"}


# ---------------- Payments ----------------
class TestPayments:
    def test_packages(self):
        r = requests.get(f"{API}/payments/packages", timeout=30)
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list) and len(arr) == 3
        ids = {p["id"]: p for p in arr}
        for k in ("discovery", "strategy", "deepdive"):
            assert k in ids, f"missing pkg {k}"
            for field in ("name", "amount", "duration", "features"):
                assert field in ids[k]
        assert ids["discovery"]["amount"] == 99.0
        assert ids["strategy"]["amount"] == 299.0
        assert ids["deepdive"]["amount"] == 599.0

    def test_checkout_invalid_package(self):
        r = requests.post(f"{API}/payments/checkout", json={
            "package_id": "nope", "origin_url": "https://example.com",
            "name": "TEST X", "email": "test_x@example.com",
        }, timeout=30)
        assert r.status_code == 400

    def test_checkout_valid(self):
        r = requests.post(f"{API}/payments/checkout", json={
            "package_id": "discovery",
            "origin_url": "https://example.com",
            "name": "TEST Payer",
            "email": f"test_pay_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "1234567890",
            "area": "Fundraising",
            "message": "Please advise.",
        }, timeout=60)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "checkout_url" in d and d["checkout_url"].startswith("https://checkout.stripe.com")
        assert "session_id" in d and len(d["session_id"]) > 5
        # verify /payments/status returns the record (initiated)
        s = requests.get(f"{API}/payments/status/{d['session_id']}", timeout=30)
        assert s.status_code == 200
        sd = s.json()
        assert sd["session_id"] == d["session_id"]
        assert sd["package_id"] == "discovery"
        assert sd["amount"] == 99.0
        # payment_status should be pending or paid (not yet completed in test flow)
        assert sd["payment_status"] in ("pending", "paid")

    def test_payment_status_unknown(self):
        r = requests.get(f"{API}/payments/status/does-not-exist-xyz", timeout=30)
        assert r.status_code == 404

    def test_paid_lead_appears_in_admin(self, admin_headers):
        # create a checkout and verify a corresponding consultation record with status payment_pending
        email = f"test_paid_{uuid.uuid4().hex[:6]}@example.com"
        c = requests.post(f"{API}/payments/checkout", json={
            "package_id": "strategy", "origin_url": "https://example.com",
            "name": "TEST PaidLead", "email": email, "phone": "999", "area": "Strategy", "message": "hi",
        }, timeout=60)
        assert c.status_code == 200
        r = requests.get(f"{API}/consultations", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        found = [x for x in r.json() if x.get("email") == email]
        assert found, "consultation record was not created for checkout"
        rec = found[0]
        assert rec["status"] == "payment_pending"
        assert rec.get("package") == "1:1 Strategy Session"
        assert rec.get("amount") == 299.0


# ---------------- Market Live ----------------
class TestMarketLive:
    def test_live_shape(self):
        r = requests.get(f"{API}/market/live", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "data" in d and isinstance(d["data"], list)
        # data may be empty if yahoo rate limits — soft check
        if d["data"]:
            item = d["data"][0]
            for k in ("name", "value", "change", "up"):
                assert k in item


# ---------------- Newsletter ----------------
class TestNewsletter:
    def test_subscribe_and_duplicate(self):
        email = f"test_sub_{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{API}/newsletter", json={"email": email}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True
        assert "Subscribed" in d.get("message", "") or "already" in d.get("message", "")

        # duplicate
        r2 = requests.post(f"{API}/newsletter", json={"email": email}, timeout=30)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2.get("success") is True
        assert "already" in d2["message"].lower()

    def test_subscribe_invalid_email(self):
        r = requests.post(f"{API}/newsletter", json={"email": "not-an-email"}, timeout=30)
        assert r.status_code == 422

    def test_admin_list_subscribers(self, admin_headers):
        # ensure at least one subscriber exists
        email = f"test_sub_{uuid.uuid4().hex[:8]}@example.com"
        requests.post(f"{API}/newsletter", json={"email": email}, timeout=30)
        r = requests.get(f"{API}/newsletter", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list) and len(arr) > 0
        assert "_id" not in arr[0]
        assert any(s["email"] == email for s in arr)

    def test_admin_list_forbidden(self):
        r = requests.get(f"{API}/newsletter", timeout=30)
        assert r.status_code == 401
