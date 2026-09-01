"""Iteration 16 backend tests: Tier-1 revenue features (products, cohorts, commerce, CMS, PDF)."""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://energy-strategy-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASSWORD = "Sudarshan@2026"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
        "consent": True, "captcha_token": "test",
    }, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    tok = r.json().get("token") or r.json().get("access_token")
    assert tok, f"no token in login response: {r.json()}"
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------- Public catalogue ----------

class TestCatalogue:
    def test_list_products(self):
        r = requests.get(f"{API}/products", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) >= 3
        slugs = {p["slug"] for p in data}
        for s in ("leadership-blueprint-pro", "cxo-strategy-playbook", "fundraising-toolkit"):
            assert s in slugs, f"missing seeded slug {s}"
        assert all("_id" not in p for p in data)

    def test_get_product_ok(self):
        r = requests.get(f"{API}/products/cxo-strategy-playbook", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["slug"] == "cxo-strategy-playbook"
        assert d.get("price")

    def test_get_product_404(self):
        r = requests.get(f"{API}/products/energy-strategy-hub", timeout=30)
        assert r.status_code == 404

    def test_list_cohorts(self):
        r = requests.get(f"{API}/cohorts", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) >= 1
        for c in data:
            assert "seats_left" in c
            assert isinstance(c["seats_left"], int)

    def test_get_cohort_ok(self):
        r = requests.get(f"{API}/cohorts/cxo-leadership-cohort", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["slug"] == "cxo-leadership-cohort"
        assert "seats_left" in d

    def test_get_cohort_404(self):
        r = requests.get(f"{API}/cohorts/energy-strategy-hub", timeout=30)
        assert r.status_code == 404

    def test_case_studies(self):
        r = requests.get(f"{API}/case-studies", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) >= 1
        for c in data:
            assert c.get("headline") and c.get("sector")
            assert isinstance(c.get("metrics"), list)

    def test_testimonials(self):
        r = requests.get(f"{API}/testimonials", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list) and len(data) >= 1
        assert all("quote" in t for t in data)


# ---------- Nurture / corporate ----------

class TestFunnels:
    def test_nurture_subscribe_idempotent(self):
        email = f"test.nurture.{uuid.uuid4().hex[:8]}@test.com"
        payload = {"email": email, "name": "Test", "source": "lead-magnet", "captcha_token": "test"}
        r1 = requests.post(f"{API}/nurture/subscribe", json=payload, timeout=30)
        assert r1.status_code == 200, r1.text
        assert r1.json().get("success") is True
        # Idempotent
        r2 = requests.post(f"{API}/nurture/subscribe", json=payload, timeout=30)
        assert r2.status_code == 200
        assert r2.json().get("success") is True

    def test_corporate_inquiry(self):
        payload = {
            "name": "Test Corp Contact", "email": "test.corp@test.com", "company": "TestCo",
            "phone": "+91-9999999999", "budget": "5-10L", "engagement": "retainer",
            "message": "Please reach out.", "captcha_token": "test",
        }
        r = requests.post(f"{API}/corporate/inquiry", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("success") is True
        assert "AI" not in j.get("message", "")
        assert "artificial intelligence" not in j.get("message", "").lower()


# ---------- Blueprint PDFs ----------

class TestBlueprintPDF:
    def test_starter_pdf(self):
        r = requests.get(f"{API}/blueprint/starter.pdf", timeout=60)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert len(r.content) > 500
        assert r.content[:4] == b"%PDF"

    def test_download_unknown_order_404(self):
        r = requests.get(f"{API}/blueprint/download/{uuid.uuid4().hex}", timeout=30)
        assert r.status_code == 404


# ---------- Commerce (Razorpay LIVE — order create only, no capture) ----------

class TestCommerce:
    def test_commerce_order_product(self):
        payload = {
            "kind": "product", "ref_id": "cxo-strategy-playbook",
            "name": "TEST Buyer", "email": "test.buyer@test.com", "phone": "+91-9000000001",
            "captcha_token": "test",
        }
        r = requests.post(f"{API}/commerce/order", json=payload, timeout=60)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("success") is True
        assert j.get("our_order_id") and j.get("order_id")
        assert j.get("key_id")
        assert isinstance(j.get("amount"), int) and j["amount"] > 0
        assert j.get("currency") == "INR"

    def test_commerce_order_cohort(self):
        payload = {
            "kind": "cohort", "ref_id": "cxo-leadership-cohort",
            "name": "TEST Cohort Buyer", "email": "test.cohort@test.com", "phone": "",
            "captcha_token": "test",
        }
        r = requests.post(f"{API}/commerce/order", json=payload, timeout=60)
        assert r.status_code == 200, r.text
        j = r.json()
        # Either success (seats available) or waitlist:true (full)
        if j.get("success") is False:
            assert j.get("waitlist") is True
        else:
            assert j.get("our_order_id") and j.get("order_id")

    def test_commerce_order_invalid_kind(self):
        payload = {
            "kind": "widget", "ref_id": "cxo-strategy-playbook",
            "name": "T", "email": "t@t.com", "captcha_token": "test",
        }
        r = requests.post(f"{API}/commerce/order", json=payload, timeout=30)
        assert r.status_code == 400

    def test_commerce_order_unknown_ref(self):
        payload = {
            "kind": "product", "ref_id": "no-such-product-slug",
            "name": "T", "email": "t@t.com", "captcha_token": "test",
        }
        r = requests.post(f"{API}/commerce/order", json=payload, timeout=30)
        assert r.status_code == 404

    def test_commerce_verify_bogus(self):
        payload = {
            "our_order_id": uuid.uuid4().hex,
            "razorpay_order_id": "order_" + uuid.uuid4().hex[:14],
            "razorpay_payment_id": "pay_" + uuid.uuid4().hex[:14],
            "razorpay_signature": "deadbeef" * 8,
        }
        r = requests.post(f"{API}/commerce/verify", json=payload, timeout=30)
        assert r.status_code in (400, 404), f"unexpected {r.status_code}: {r.text}"

    def test_cohort_waitlist_ok(self):
        payload = {"email": f"test.wait.{uuid.uuid4().hex[:6]}@test.com", "captcha_token": "test"}
        r = requests.post(f"{API}/cohorts/cxo-leadership-cohort/waitlist", json=payload, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json().get("success") is True

    def test_cohort_waitlist_404(self):
        payload = {"email": "test.wait2@test.com", "captcha_token": "test"}
        r = requests.post(f"{API}/cohorts/no-such-cohort/waitlist", json=payload, timeout=30)
        assert r.status_code == 404


# ---------- Admin CMS ----------

class TestAdminCMS:
    def test_admin_orders_unauth(self):
        r = requests.get(f"{API}/admin/commerce/orders", timeout=30)
        assert r.status_code in (401, 403)

    def test_admin_orders_ok(self, admin_headers):
        r = requests.get(f"{API}/admin/commerce/orders", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_cms_unknown_collection(self, admin_headers):
        r = requests.post(f"{API}/admin/cms/widgets", headers=admin_headers,
                          json={"title": "x"}, timeout=30)
        assert r.status_code == 404
        r2 = requests.delete(f"{API}/admin/cms/widgets/abc", headers=admin_headers, timeout=30)
        assert r2.status_code == 404

    @pytest.mark.parametrize("collection,payload", [
        ("products", {"title": "TEST_Product", "slug": f"test-prod-{uuid.uuid4().hex[:6]}",
                      "price": 499, "type": "playbook", "description": "TEST"}),
        ("cohorts", {"title": "TEST_Cohort", "slug": f"test-cohort-{uuid.uuid4().hex[:6]}",
                     "price": 9999, "seats_total": 10, "description": "TEST"}),
        ("case-studies", {"headline": "TEST_Case", "slug": f"test-case-{uuid.uuid4().hex[:6]}",
                          "sector": "Test", "client": "TEST", "metrics": []}),
        ("testimonials", {"name": "TEST_Person", "role": "Tester", "quote": "TEST quote"}),
    ])
    def test_cms_crud(self, admin_headers, collection, payload):
        # Create
        r = requests.post(f"{API}/admin/cms/{collection}", headers=admin_headers,
                          json=payload, timeout=30)
        assert r.status_code == 200, r.text
        j = r.json()
        assert j.get("success") is True and j.get("id")
        new_id = j["id"]
        # Update
        upd = {**payload, "id": new_id, "description": "TEST_UPDATED"} if "description" in payload else {**payload, "id": new_id}
        upd["_marker"] = "updated"
        r2 = requests.post(f"{API}/admin/cms/{collection}", headers=admin_headers,
                           json=upd, timeout=30)
        assert r2.status_code == 200, r2.text
        assert r2.json().get("id") == new_id
        # Delete
        r3 = requests.delete(f"{API}/admin/cms/{collection}/{new_id}", headers=admin_headers, timeout=30)
        assert r3.status_code == 200
        assert r3.json().get("success") is True
