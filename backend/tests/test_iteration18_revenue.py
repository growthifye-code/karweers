"""Iteration 18 backend tests: promo codes, bundles, gift-a-seat, revenue analytics,
best-sellers, abandoned-nudge, blueprint download, admin CMS list (incl inactive)."""
import os
import time
import uuid
import pytest
import requests

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
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
    assert tok
    return tok


@pytest.fixture(scope="module")
def H(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------- Public catalogue including bundles ----------
class TestCatalogue:
    def test_products(self):
        r = requests.get(f"{API}/products", timeout=30)
        assert r.status_code == 200
        slugs = {p["slug"] for p in r.json()}
        assert "cxo-strategy-playbook" in slugs and "leadership-blueprint-pro" in slugs

    def test_cohorts_seats_left(self):
        r = requests.get(f"{API}/cohorts", timeout=30)
        assert r.status_code == 200
        for c in r.json():
            assert "seats_left" in c

    def test_bundles(self):
        r = requests.get(f"{API}/bundles", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data) >= 1
        b = data[0]
        for k in ("slug", "title", "price", "product_title", "cohort_title",
                 "separate_price", "savings", "cohort_seats_left"):
            assert k in b, f"missing {k} in bundle response"
        assert b["separate_price"] >= b["price"]

    def test_case_studies_and_testimonials(self):
        assert requests.get(f"{API}/case-studies", timeout=30).status_code == 200
        assert requests.get(f"{API}/testimonials", timeout=30).status_code == 200

    def test_unknown_slugs_404(self):
        assert requests.get(f"{API}/products/does-not-exist-xyz", timeout=30).status_code == 404
        assert requests.get(f"{API}/cohorts/does-not-exist-xyz", timeout=30).status_code == 404


# ---------- Commerce order (product / cohort / bundle) ----------
class TestCommerceOrder:
    def _payload(self, **over):
        p = {"kind": "product", "ref_id": "cxo-strategy-playbook",
             "name": "TEST_QA", "email": f"test_qa_{uuid.uuid4().hex[:6]}@example.com",
             "phone": "9999999999", "captcha_token": "test"}
        p.update(over)
        return p

    def test_order_product(self):
        r = requests.post(f"{API}/commerce/order", json=self._payload(), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["success"] is True
        assert d["amount"] == 99900
        assert d["order_id"].startswith("order_")
        assert d["key_id"]

    def test_order_cohort(self):
        r = requests.post(f"{API}/commerce/order", json=self._payload(
            kind="cohort", ref_id="cxo-leadership-cohort"), timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["success"] is True

    def test_order_bundle(self):
        r = requests.post(f"{API}/commerce/order", json=self._payload(
            kind="bundle", ref_id="leadership-accelerator"), timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["success"] is True
        assert d["amount"] == 2299900

    def test_invalid_kind_400(self):
        r = requests.post(f"{API}/commerce/order", json=self._payload(kind="donation"), timeout=30)
        assert r.status_code == 400

    def test_unknown_ref_404(self):
        r = requests.post(f"{API}/commerce/order", json=self._payload(ref_id="ghost-slug-xyz"), timeout=30)
        assert r.status_code == 404

    def test_order_with_gift(self):
        gift = {"recipient_name": "Alice", "recipient_email": "alice_gift@example.com",
                "message": "Enjoy this."}
        r = requests.post(f"{API}/commerce/order",
                          json=self._payload(kind="product", ref_id="cxo-strategy-playbook", gift=gift),
                          timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["success"] is True


# ---------- Full cohort -> waitlist path ----------
class TestFullCohortWaitlist:
    def test_full_cohort_returns_waitlist(self, H):
        # create a temporary cohort with 0 seats
        slug = f"test-fullcohort-{uuid.uuid4().hex[:6]}"
        body = {"slug": slug, "title": "TEST Full Cohort", "price": 100,
                "seats_total": 1, "seats_taken": 1, "active": True, "sort": 999}
        r = requests.post(f"{API}/admin/cms/cohorts", json=body, headers=H, timeout=30)
        assert r.status_code == 200
        cid = r.json()["id"]
        try:
            r = requests.post(f"{API}/commerce/order", json={
                "kind": "cohort", "ref_id": slug, "name": "T", "email": "t@t.co",
                "captcha_token": "test"}, timeout=30)
            assert r.status_code == 200
            d = r.json()
            assert d["success"] is False and d["waitlist"] is True
        finally:
            requests.delete(f"{API}/admin/cms/cohorts/{cid}", headers=H, timeout=30)


# ---------- Promo validate + order with promo ----------
class TestPromo:
    @pytest.fixture(scope="class")
    def promo(self, H):
        code = f"TESTQA{uuid.uuid4().hex[:5].upper()}"
        body = {"code": code, "type": "percent", "value": 20, "active": True,
                "applies_to": "all", "max_uses": 0, "sort": 999}
        r = requests.post(f"{API}/admin/cms/promo-codes", json=body, headers=H, timeout=30)
        assert r.status_code == 200, r.text
        pid = r.json()["id"]
        yield code, pid
        requests.delete(f"{API}/admin/cms/promo-codes/{pid}", headers=H, timeout=30)

    def test_validate_product(self, promo):
        code, _ = promo
        r = requests.post(f"{API}/promo/validate",
                          json={"code": code, "kind": "product", "ref_id": "cxo-strategy-playbook"},
                          timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["valid"] is True
        assert d["final_price"] == 799  # 999 - 20%
        assert d["original_price"] == 999

    def test_validate_bundle(self, promo):
        code, _ = promo
        r = requests.post(f"{API}/promo/validate",
                          json={"code": code, "kind": "bundle", "ref_id": "leadership-accelerator"},
                          timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["valid"] is True

    def test_validate_invalid_code(self):
        r = requests.post(f"{API}/promo/validate",
                          json={"code": "NEVERISSUED_XYZ", "kind": "product",
                                "ref_id": "cxo-strategy-playbook"}, timeout=30)
        assert r.status_code == 200
        assert r.json()["valid"] is False

    def test_order_with_valid_promo(self, promo):
        code, _ = promo
        r = requests.post(f"{API}/commerce/order", json={
            "kind": "product", "ref_id": "cxo-strategy-playbook",
            "name": "T", "email": "promo_valid@test.co", "captcha_token": "test",
            "promo_code": code}, timeout=30)
        assert r.status_code == 200, r.text
        assert r.json()["amount"] == 79900  # 799 * 100

    def test_order_with_invalid_promo_400(self):
        r = requests.post(f"{API}/commerce/order", json={
            "kind": "product", "ref_id": "cxo-strategy-playbook",
            "name": "T", "email": "promo_bad@test.co", "captcha_token": "test",
            "promo_code": "TOTALLY_BOGUS_XYZ"}, timeout=30)
        assert r.status_code == 400


# ---------- Blueprint PDFs ----------
class TestBlueprint:
    def test_starter_pdf(self):
        r = requests.get(f"{API}/blueprint/starter.pdf", timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert len(r.content) > 500 and r.content[:5] == b"%PDF-"

    def test_download_bad_id_404(self):
        r = requests.get(f"{API}/blueprint/download/nonexistent-order-id", timeout=30)
        assert r.status_code == 404


# ---------- Lead / corporate / waitlist ----------
class TestLeadFlows:
    def test_nurture_idempotent(self):
        email = f"nurture_{uuid.uuid4().hex[:6]}@test.co"
        for _ in range(2):
            r = requests.post(f"{API}/nurture/subscribe", json={
                "email": email, "name": "T", "captcha_token": "test"}, timeout=30)
            assert r.status_code == 200
            assert "AI" not in r.text  # word AI must not appear

    def test_corporate(self):
        r = requests.post(f"{API}/corporate/inquiry", json={
            "name": "T Corp", "email": f"corp_{uuid.uuid4().hex[:5]}@test.co",
            "company": "TestCo", "captcha_token": "test",
            "message": "Interested"}, timeout=30)
        assert r.status_code == 200
        assert r.json()["success"] is True
        assert "AI" not in r.text

    def test_waitlist_ok_and_404(self):
        r = requests.post(f"{API}/cohorts/cxo-leadership-cohort/waitlist", json={
            "email": f"wl_{uuid.uuid4().hex[:6]}@test.co", "captcha_token": "test"}, timeout=30)
        assert r.status_code == 200

        r2 = requests.post(f"{API}/cohorts/energy-strategy-hub/waitlist", json={
            "email": "no@test.co", "captcha_token": "test"}, timeout=30)
        assert r2.status_code == 404


# ---------- Admin CMS list (includes inactive) ----------
class TestAdminCMSList:
    @pytest.mark.parametrize("coll", ["products", "cohorts", "case-studies",
                                       "testimonials", "promo-codes", "bundles"])
    def test_list_returns_all(self, H, coll):
        r = requests.get(f"{API}/admin/cms/{coll}", headers=H, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_list_unknown_404(self, H):
        r = requests.get(f"{API}/admin/cms/unknown-thing", headers=H, timeout=30)
        assert r.status_code == 404

    def test_admin_requires_auth(self):
        r = requests.get(f"{API}/admin/cms/products", timeout=30)
        assert r.status_code in (401, 403)

    def test_inactive_item_visible_in_admin(self, H):
        slug = f"test-inactive-{uuid.uuid4().hex[:6]}"
        body = {"slug": slug, "title": "TEST inactive", "price": 100,
                "type": "playbook", "active": False, "sort": 999}
        r = requests.post(f"{API}/admin/cms/products", json=body, headers=H, timeout=30)
        assert r.status_code == 200
        pid = r.json()["id"]
        try:
            r2 = requests.get(f"{API}/admin/cms/products", headers=H, timeout=30)
            assert any(p.get("id") == pid for p in r2.json())
            # public shouldn't see it
            r3 = requests.get(f"{API}/products", timeout=30)
            assert not any(p.get("slug") == slug for p in r3.json())
        finally:
            requests.delete(f"{API}/admin/cms/products/{pid}", headers=H, timeout=30)


# ---------- Admin CMS CRUD for products / bundles / promo-codes ----------
class TestAdminCMSCRUD:
    @pytest.mark.parametrize("coll,payload_extra", [
        ("products", {"title": "TEST P", "price": 100, "type": "playbook"}),
        ("bundles", {"title": "TEST B", "price": 100,
                     "product_slug": "cxo-strategy-playbook",
                     "cohort_slug": "cxo-leadership-cohort"}),
    ])
    def test_create_update_delete(self, H, coll, payload_extra):
        slug = f"test-{coll}-{uuid.uuid4().hex[:6]}"
        body = {"slug": slug, "active": True, "sort": 999, **payload_extra}
        r = requests.post(f"{API}/admin/cms/{coll}", json=body, headers=H, timeout=30)
        assert r.status_code == 200, r.text
        item_id = r.json()["id"]
        # update
        upd = {"id": item_id, "slug": slug, "title": "TEST updated",
               "active": True, "sort": 999, **payload_extra}
        upd["title"] = "TEST updated"
        r = requests.post(f"{API}/admin/cms/{coll}", json=upd, headers=H, timeout=30)
        assert r.status_code == 200
        # delete
        r = requests.delete(f"{API}/admin/cms/{coll}/{item_id}", headers=H, timeout=30)
        assert r.status_code == 200

    def test_promo_code_crud(self, H):
        code = f"CRUDQA{uuid.uuid4().hex[:5].upper()}"
        r = requests.post(f"{API}/admin/cms/promo-codes", json={
            "code": code, "type": "percent", "value": 10,
            "active": True, "applies_to": "all", "sort": 999}, headers=H, timeout=30)
        assert r.status_code == 200
        pid = r.json()["id"]
        # duplicate -> 400
        r2 = requests.post(f"{API}/admin/cms/promo-codes", json={
            "code": code, "type": "percent", "value": 10,
            "active": True, "sort": 999}, headers=H, timeout=30)
        assert r2.status_code == 400
        # missing code -> 400
        r3 = requests.post(f"{API}/admin/cms/promo-codes", json={
            "type": "percent", "value": 5, "active": True, "sort": 999}, headers=H, timeout=30)
        assert r3.status_code == 400
        # update
        r4 = requests.post(f"{API}/admin/cms/promo-codes", json={
            "id": pid, "code": code, "type": "percent", "value": 15,
            "active": True, "sort": 999}, headers=H, timeout=30)
        assert r4.status_code == 200
        # delete
        r5 = requests.delete(f"{API}/admin/cms/promo-codes/{pid}", headers=H, timeout=30)
        assert r5.status_code == 200


# ---------- Admin analytics ----------
class TestAnalytics:
    def test_orders_list(self, H):
        r = requests.get(f"{API}/admin/commerce/orders", headers=H, timeout=30)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_promo_analytics(self, H):
        r = requests.get(f"{API}/admin/promo/analytics", headers=H, timeout=30)
        assert r.status_code == 200
        for c in r.json():
            for k in ("started", "uses", "conversion_rate", "revenue"):
                assert k in c

    def test_revenue_analytics(self, H):
        r = requests.get(f"{API}/admin/commerce/revenue-analytics", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "series" in d and len(d["series"]) == 30
        for k in ("top_items", "total_revenue", "orders", "aov"):
            assert k in d

    def test_best_sellers(self):
        r = requests.get(f"{API}/commerce/best-sellers", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert "product" in d and "cohort" in d

    def test_nudge_abandoned(self, H):
        r = requests.post(f"{API}/admin/commerce/nudge-abandoned", headers=H, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["success"] is True
        assert "sent" in d

    def test_admin_endpoints_require_auth(self):
        for path in ("/admin/commerce/orders", "/admin/promo/analytics",
                     "/admin/commerce/revenue-analytics"):
            r = requests.get(f"{API}{path}", timeout=30)
            assert r.status_code in (401, 403), f"{path} did not require auth"
        r = requests.post(f"{API}/admin/commerce/nudge-abandoned", timeout=30)
        assert r.status_code in (401, 403)
