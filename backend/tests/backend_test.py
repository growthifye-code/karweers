"""Backend API tests for Sudarshan Karweer Advisory."""
import os
import time
import uuid
import json
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    # fall back to frontend env file
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip()
                break
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASSWORD = "Sudarshan@2026"


@pytest.fixture(scope="session")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data["user"]["role"] == "admin"
    return data["token"]


@pytest.fixture(scope="session")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="session")
def client_creds():
    return {"name": "TEST Client", "email": f"test_{uuid.uuid4().hex[:8]}@example.com", "password": "Test@1234"}


@pytest.fixture(scope="session")
def client_token(client_creds):
    r = requests.post(f"{API}/auth/register", json=client_creds, timeout=30)
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    d = r.json()
    assert d["user"]["role"] == "client"
    return d["token"]


# ---------------- Meta / content ----------------
class TestMeta:
    def test_meta(self):
        r = requests.get(f"{API}/meta", timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("services", "stats", "market_pulse", "testimonials"):
            assert k in d and isinstance(d[k], list) and len(d[k]) > 0


class TestArticles:
    def test_list(self):
        r = requests.get(f"{API}/articles", timeout=30)
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list) and len(arr) > 0
        assert "_id" not in arr[0]
        assert "slug" in arr[0]

    @pytest.mark.parametrize("cat", ["news", "analysis", "blog", "rd", "casestudy"])
    def test_filter_category(self, cat):
        r = requests.get(f"{API}/articles", params={"category": cat}, timeout=30)
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list) and len(arr) > 0
        for a in arr:
            assert a["category"] == cat

    def test_get_by_slug(self):
        r = requests.get(f"{API}/articles/india-record-solar-fy26", timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["slug"] == "india-record-solar-fy26"
        assert d["category"] == "news"

    def test_get_missing(self):
        r = requests.get(f"{API}/articles/does-not-exist-xxx", timeout=30)
        assert r.status_code == 404


# ---------------- Auth ----------------
class TestAuth:
    def test_admin_login(self, admin_token):
        assert isinstance(admin_token, str) and len(admin_token) > 10

    def test_me(self, admin_headers):
        r = requests.get(f"{API}/auth/me", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["email"] == ADMIN_EMAIL
        assert d["role"] == "admin"
        assert "password_hash" not in d

    def test_bad_login(self):
        r = requests.post(f"{API}/auth/login", json={"email": ADMIN_EMAIL, "password": "wrong"}, timeout=30)
        assert r.status_code == 401

    def test_register_and_login(self, client_creds, client_token):
        assert client_token
        # login again
        r = requests.post(f"{API}/auth/login", json={"email": client_creds["email"], "password": client_creds["password"]}, timeout=30)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "client"

    def test_duplicate_register(self, client_creds):
        r = requests.post(f"{API}/auth/register", json=client_creds, timeout=30)
        assert r.status_code == 400

    def test_no_token(self):
        r = requests.get(f"{API}/auth/me", timeout=30)
        assert r.status_code == 401

    def test_admin_only_forbidden_for_client(self, client_token):
        r = requests.get(f"{API}/admin/stats", headers={"Authorization": f"Bearer {client_token}"}, timeout=30)
        assert r.status_code == 403


# ---------------- Consultation ----------------
class TestConsultation:
    created_id = None

    def test_create(self):
        payload = {
            "name": "TEST Lead", "email": "test_lead@example.com",
            "phone": "1234567890", "company": "TestCo",
            "area": "Renewable Energy", "message": "Please advise."
        }
        r = requests.post(f"{API}/consultations", json=payload, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d.get("success") is True

    def test_admin_list_and_status(self, admin_headers):
        r = requests.get(f"{API}/consultations", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        arr = r.json()
        assert isinstance(arr, list) and len(arr) > 0
        cid = arr[0]["id"]
        r2 = requests.patch(f"{API}/consultations/{cid}", params={"status": "contacted"}, headers=admin_headers, timeout=30)
        assert r2.status_code == 200
        # verify
        r3 = requests.get(f"{API}/consultations", headers=admin_headers, timeout=30)
        found = [x for x in r3.json() if x["id"] == cid]
        assert found and found[0]["status"] == "contacted"

    def test_client_cannot_list(self, client_token):
        r = requests.get(f"{API}/consultations", headers={"Authorization": f"Bearer {client_token}"}, timeout=30)
        assert r.status_code == 403


# ---------------- Admin stats ----------------
class TestAdminStats:
    def test_stats(self, admin_headers):
        r = requests.get(f"{API}/admin/stats", headers=admin_headers, timeout=30)
        assert r.status_code == 200
        d = r.json()
        for k in ("articles", "consultations", "new_leads", "clients"):
            assert k in d and isinstance(d[k], int)


# ---------------- Article CRUD (admin) ----------------
class TestArticleCRUD:
    def test_create_and_delete(self, admin_headers):
        payload = {
            "title": f"TEST Article {uuid.uuid4().hex[:6]}",
            "category": "blog",
            "summary": "Test summary",
            "content": "Test content paragraph.",
            "sector": "Testing",
            "tags": ["test"],
            "image": "",
            "featured": False,
        }
        r = requests.post(f"{API}/articles", json=payload, headers=admin_headers, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        slug = d["slug"]
        assert "_id" not in d
        # verify list
        r2 = requests.get(f"{API}/articles/{slug}", timeout=30)
        assert r2.status_code == 200
        # delete
        r3 = requests.delete(f"{API}/articles/{slug}", headers=admin_headers, timeout=30)
        assert r3.status_code == 200
        # verify 404
        r4 = requests.get(f"{API}/articles/{slug}", timeout=30)
        assert r4.status_code == 404

    def test_client_cannot_create(self, client_token):
        r = requests.post(f"{API}/articles", json={
            "title": "T", "category": "blog", "summary": "s", "content": "c"
        }, headers={"Authorization": f"Bearer {client_token}"}, timeout=30)
        assert r.status_code == 403


# ---------------- AI ----------------
class TestAI:
    def test_chat_streaming(self):
        payload = {"session_id": f"test-{uuid.uuid4().hex[:8]}", "message": "In one sentence, what is BESS?"}
        with requests.post(f"{API}/ai/chat", json=payload, stream=True, timeout=90) as r:
            assert r.status_code == 200
            got_delta = False
            got_done = False
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                try:
                    ev = json.loads(line[5:].strip())
                except Exception:
                    continue
                if "error" in ev:
                    pytest.fail(f"AI chat error: {ev['error']}")
                if "delta" in ev:
                    got_delta = True
                if ev.get("done"):
                    got_done = True
                    break
            assert got_delta, "no delta events received"
            assert got_done, "no done event received"

    def test_generate_admin(self, admin_headers):
        payload = {"topic": "Green Hydrogen offtake structures", "category": "blog"}
        r = requests.post(f"{API}/ai/generate", json=payload, headers=admin_headers, timeout=120)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("title", "summary", "content", "tags"):
            assert k in d

    def test_generate_forbidden_client(self, client_token):
        r = requests.post(f"{API}/ai/generate", json={"topic": "x", "category": "blog"},
                          headers={"Authorization": f"Bearer {client_token}"}, timeout=30)
        assert r.status_code == 403
