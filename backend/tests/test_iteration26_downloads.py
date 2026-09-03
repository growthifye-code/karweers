"""Iteration 26 — Collateral download analytics, gate toggle/unlock, bulk-refresh guard."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://energy-strategy-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASSWORD = "Sudarshan@2026"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json={
        "email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": "x", "consent": True
    }, timeout=30)
    if r.status_code != 200:
        # unblock IP just in case
        pytest.skip(f"admin login failed: {r.status_code} {r.text[:200]}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


# ---------- Analytics + list surface ----------

def test_admin_collateral_list_includes_analytics(admin_headers):
    r = requests.get(f"{API}/admin/collateral", headers=admin_headers, timeout=30)
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert "total_downloads" in data
    assert "leaderboard" in data
    assert "refresh" in data
    assert isinstance(data["leaderboard"], list)
    # each item exposes counters + gated + gatable
    for it in data["items"][:3]:
        assert "downloads" in it
        assert "downloads_week" in it
        assert "gated" in it
        assert "gatable" in it


def test_strategy_tools_list_has_gated_flag():
    r = requests.get(f"{API}/strategy-tools", timeout=30)
    assert r.status_code == 200
    tools = r.json()
    assert isinstance(tools, list) and len(tools) >= 1
    assert "gated" in tools[0]


# ---------- Gate enforcement + unlock ----------

TEST_SLUG = "ansoff-matrix"
TEST_KEY = f"tool:{TEST_SLUG}"


def _find_tool_id(admin_headers, key=TEST_KEY):
    r = requests.get(f"{API}/admin/collateral", headers=admin_headers, timeout=30)
    for it in r.json()["items"]:
        if it.get("key") == key:
            return it["id"]
    return None


def test_gated_download_403_without_cookie():
    # by default tools are gated
    r = requests.get(f"{API}/strategy-tools/ansoff-matrix.pdf", allow_redirects=False, timeout=30)
    # If already unlocked in a shared cookie jar, force new session (requests default has none)
    assert r.status_code == 403, f"expected 403 got {r.status_code}"
    assert r.json().get("detail") == "gated"


def test_unlock_sets_cookie_and_upserts_subscriber_and_downloads_ok():
    s = requests.Session()
    email = "test_iter26_unlock@example.com"
    r = s.post(f"{API}/collateral/unlock", json={"name": "Tester", "email": email, "source": "test-iter26"}, timeout=30)
    assert r.status_code == 200
    assert r.json().get("ok") is True
    assert "dl_gate" in s.cookies.get_dict()
    # now the download should succeed
    r2 = s.get(f"{API}/strategy-tools/ansoff-matrix.pdf", timeout=60)
    assert r2.status_code == 200
    assert r2.headers.get("content-type", "").startswith("application/pdf")
    assert len(r2.content) > 500


def test_download_increments_counter(admin_headers):
    tid = _find_tool_id(admin_headers, "tool:ansoff-matrix")
    assert tid, "energy-strategy-hub tool not found"
    # baseline
    r0 = requests.get(f"{API}/admin/collateral", headers=admin_headers, timeout=30).json()
    before = next(i["downloads"] for i in r0["items"] if i["id"] == tid)

    # unlock + download twice
    s = requests.Session()
    s.post(f"{API}/collateral/unlock", json={"email": "test_iter26_counter@example.com"}, timeout=30)
    for _ in range(2):
        rr = s.get(f"{API}/strategy-tools/ansoff-matrix.pdf", timeout=60)
        assert rr.status_code == 200

    r1 = requests.get(f"{API}/admin/collateral", headers=admin_headers, timeout=30).json()
    after = next(i["downloads"] for i in r1["items"] if i["id"] == tid)
    assert after >= before + 2, f"counter did not increment: {before} -> {after}"
    # leaderboard contains this item (it now has downloads > 0)
    lb_ids = [x["id"] for x in r1["leaderboard"]]
    assert tid in lb_ids
    # total_downloads is a positive number
    assert r1["total_downloads"] >= after


# ---------- Gate toggle (admin) ----------

def test_gate_toggle_off_allows_direct_download_then_re_gate(admin_headers):
    tid = _find_tool_id(admin_headers, "tool:ansoff-matrix")
    assert tid
    # flip open
    r = requests.post(f"{API}/admin/collateral/{tid}/gate", json={"gated": False}, headers=admin_headers, timeout=30)
    assert r.status_code == 200
    assert r.json().get("gated") is False
    # direct download with NO cookie should now succeed
    r2 = requests.get(f"{API}/strategy-tools/ansoff-matrix.pdf", timeout=60)
    assert r2.status_code == 200
    # flip back to gated
    r3 = requests.post(f"{API}/admin/collateral/{tid}/gate", json={"gated": True}, headers=admin_headers, timeout=30)
    assert r3.status_code == 200
    assert r3.json().get("gated") is True
    # now cookieless request should 403 again
    r4 = requests.get(f"{API}/strategy-tools/ansoff-matrix.pdf", allow_redirects=False, timeout=30)
    assert r4.status_code == 403


# ---------- Bulk AI refresh guard + status (no full run) ----------

def test_bulk_refresh_status_endpoint(admin_headers):
    r = requests.get(f"{API}/admin/collateral/ai-refresh-status", headers=admin_headers, timeout=30)
    assert r.status_code == 200
    j = r.json()
    for k in ("running", "total", "done", "finished_at"):
        assert k in j


def test_bulk_refresh_409_guard_via_flag(admin_headers):
    """Set app_meta.collateral_refresh.running=true directly in Mongo, assert 409, then reset."""
    import pymongo
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = pymongo.MongoClient(mongo_url)
    coll = client[db_name].app_meta
    try:
        coll.update_one({"_id": "collateral_refresh"},
                        {"$set": {"running": True, "total": 14, "done": 0}}, upsert=True)
        r = requests.post(f"{API}/admin/collateral/ai-refresh-all", headers=admin_headers, timeout=30)
        assert r.status_code == 409, f"expected 409 got {r.status_code}: {r.text}"
    finally:
        coll.update_one({"_id": "collateral_refresh"}, {"$set": {"running": False}}, upsert=True)
    # confirm status now reports not-running
    s = requests.get(f"{API}/admin/collateral/ai-refresh-status", headers=admin_headers, timeout=30).json()
    assert s.get("running") is False


# ---------- Cleanup: subscribers created by tests ----------

def test_zzz_cleanup_test_subscribers():
    import pymongo
    mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
    db_name = os.environ.get("DB_NAME", "test_database")
    client = pymongo.MongoClient(mongo_url)
    res = client[db_name].subscribers.delete_many({"email": {"$regex": "^test_iter26_"}})
    assert res.acknowledged
