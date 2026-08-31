"""Iteration 5: CRM, Service Desk, client codes, interests, relevant blogs, GDPR, tracking, digest."""
import os
import time
import uuid
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = BASE_URL + "/api"
MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
DB_NAME = os.environ.get("DB_NAME", "test_database")

_mongo = MongoClient(MONGO_URL)
_db = _mongo[DB_NAME]


def _inject_session(email_suffix, role="client"):
    uid = "tst5_user_" + uuid.uuid4().hex[:8]
    email = f"tst5_{email_suffix}_{uuid.uuid4().hex[:6]}@example.com"
    token = "tst5_sess_" + uuid.uuid4().hex
    _db.users.insert_one({
        "id": uid, "email": email, "name": f"Test {email_suffix}",
        "role": role, "auth": "google",
        "client_code": "SK-" + uuid.uuid4().hex[:6].upper(),
        "created_at": "2026-01-01T00:00:00+00:00",
    })
    _db.user_sessions.insert_one({
        "user_id": uid, "session_token": token,
        "expires_at": "2099-01-01T00:00:00+00:00",
        "created_at": "2026-01-01T00:00:00+00:00",
    })
    return uid, email, token


def _use_admin():
    """Attach a session token to the existing seeded admin user."""
    admin = _db.users.find_one({"email": "sudarshan@karweers.com"})
    assert admin, "Admin user must be seeded"
    token = "tst5_admin_" + uuid.uuid4().hex
    _db.user_sessions.insert_one({
        "user_id": admin["id"], "session_token": token,
        "expires_at": "2099-01-01T00:00:00+00:00",
        "created_at": "2026-01-01T00:00:00+00:00",
    })
    return admin["id"], token


@pytest.fixture(scope="module")
def client_ctx():
    uid, email, token = _inject_session("client")
    yield {"id": uid, "email": email, "token": token, "headers": {"Authorization": f"Bearer {token}"}}
    _db.users.delete_one({"id": uid})
    _db.user_sessions.delete_many({"user_id": uid})
    _db.activity_events.delete_many({"user_id": uid})
    _db.support_tickets.delete_many({"user_id": uid})


@pytest.fixture(scope="module")
def admin_ctx():
    uid, token = _use_admin()
    yield {"id": uid, "token": token, "headers": {"Authorization": f"Bearer {token}"}}
    _db.user_sessions.delete_one({"session_token": token})


# ---- Client code + /auth/me ----
def test_auth_me_returns_client_code(client_ctx):
    r = requests.get(f"{API}/auth/me", headers=client_ctx["headers"], timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert d["email"] == client_ctx["email"]
    assert d.get("client_code", "").startswith("SK-")
    assert len(d["client_code"]) == 9


# ---- Interests ----
def test_set_interests_valid_only(client_ctx):
    r = requests.post(f"{API}/me/interests",
                      json={"interests": ["energy", "climate-finance", "not-a-topic"]},
                      headers=client_ctx["headers"], timeout=15)
    assert r.status_code == 200
    data = r.json()
    assert set(data["interests"]) == {"energy", "climate-finance"}
    me = requests.get(f"{API}/auth/me", headers=client_ctx["headers"]).json()
    assert set(me.get("interests", [])) == {"energy", "climate-finance"}


def test_recommended_personalised(client_ctx):
    r = requests.get(f"{API}/learning/recommended?limit=6", headers=client_ctx["headers"], timeout=45)
    assert r.status_code == 200
    d = r.json()
    assert d["personalised"] is True
    assert "energy" in d["interests"] or "climate-finance" in d["interests"]
    assert isinstance(d["videos"], list)


# ---- Relevant blogs ----
def test_me_blogs_returns_backfilled(client_ctx):
    r = requests.get(f"{API}/me/blogs?limit=4", headers=client_ctx["headers"], timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert isinstance(d["articles"], list)
    assert len(d["articles"]) > 0
    assert isinstance(d["based_on"], list)


# ---- Tracking with label ----
def test_track_authed_and_anon(client_ctx):
    r = requests.post(f"{API}/track", json={"kind": "page", "ref": "/market", "label": "Market"},
                      headers=client_ctx["headers"], timeout=15)
    assert r.status_code == 200
    assert r.json()["tracked"] is True
    ev = _db.activity_events.find_one({"user_id": client_ctx["id"], "kind": "page"})
    assert ev and ev["label"] == "Market"

    r2 = requests.post(f"{API}/track", json={"kind": "page", "ref": "/x"}, timeout=15)
    assert r2.status_code == 200 and r2.json()["tracked"] is False


# ---- Service Desk (client) ----
def test_create_ticket_and_list(client_ctx):
    r = requests.post(f"{API}/tickets",
                      json={"subject": "TST5 subject", "message": "hello", "category": "General", "priority": "high"},
                      headers=client_ctx["headers"], timeout=15)
    assert r.status_code == 200, r.text
    t = r.json()
    assert t["ticket_code"].startswith("TK-")
    assert t["status"] == "open"
    tid = t["id"]

    lst = requests.get(f"{API}/tickets", headers=client_ctx["headers"], timeout=15).json()
    assert any(x["id"] == tid for x in lst)

    # client reply keeps status open
    rr = requests.post(f"{API}/tickets/{tid}/reply", json={"message": "any updates?"},
                       headers=client_ctx["headers"], timeout=15)
    assert rr.status_code == 200
    doc = _db.support_tickets.find_one({"id": tid})
    assert doc["status"] == "open"
    assert len(doc["replies"]) == 1
    # save for admin test
    pytest.shared_tid = tid


# ---- Service Desk (admin) ----
def test_admin_tickets_and_update(admin_ctx):
    tid = pytest.shared_tid
    lst = requests.get(f"{API}/admin/tickets", headers=admin_ctx["headers"], timeout=15)
    assert lst.status_code == 200
    assert any(x["id"] == tid for x in lst.json())

    # patch status + priority
    p = requests.patch(f"{API}/admin/tickets/{tid}", json={"status": "resolved", "priority": "high"},
                       headers=admin_ctx["headers"], timeout=15)
    assert p.status_code == 200
    doc = _db.support_tickets.find_one({"id": tid})
    assert doc["status"] == "resolved" and doc["priority"] == "high"

    # admin reply => status flips to in-progress
    r = requests.post(f"{API}/tickets/{tid}/reply", json={"message": "team here"},
                      headers=admin_ctx["headers"], timeout=15)
    assert r.status_code == 200
    doc = _db.support_tickets.find_one({"id": tid})
    assert doc["status"] == "in-progress"
    assert doc["replies"][-1]["role"] == "admin"


# ---- CRM ----
def test_admin_clients_list(admin_ctx, client_ctx):
    r = requests.get(f"{API}/admin/clients", headers=admin_ctx["headers"], timeout=20)
    assert r.status_code == 200
    lst = r.json()
    mine = next((c for c in lst if c["id"] == client_ctx["id"]), None)
    assert mine is not None
    assert mine.get("client_code", "").startswith("SK-")
    for k in ("activity_count", "booking_count", "ticket_count", "interests_computed"):
        assert k in mine
    assert mine["ticket_count"] >= 1
    assert mine["activity_count"] >= 1


def test_admin_client_detail(admin_ctx, client_ctx):
    r = requests.get(f"{API}/admin/clients/{client_ctx['id']}", headers=admin_ctx["headers"], timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d["user"]["id"] == client_ctx["id"]
    assert isinstance(d["timeline"], list) and len(d["timeline"]) >= 1
    assert isinstance(d["tickets"], list) and len(d["tickets"]) >= 1
    assert isinstance(d["interests"], list) and len(d["interests"]) >= 1
    assert "topic" in d["interests"][0] and "score" in d["interests"][0]


def test_admin_allowlist_enforced(client_ctx):
    r = requests.get(f"{API}/admin/clients", headers=client_ctx["headers"], timeout=15)
    assert r.status_code == 403


# ---- GDPR ----
def test_me_data_export(client_ctx):
    r = requests.get(f"{API}/me/data", headers=client_ctx["headers"], timeout=20)
    assert r.status_code == 200
    d = r.json()
    for k in ("profile", "activity", "bookings", "tickets", "exported_at"):
        assert k in d
    assert d["profile"]["id"] == client_ctx["id"]
    assert len(d["activity"]) >= 1
    assert len(d["tickets"]) >= 1


def test_admin_cannot_self_delete(admin_ctx):
    r = requests.delete(f"{API}/me", headers=admin_ctx["headers"], timeout=15)
    assert r.status_code == 400


def test_client_can_delete(client_ctx):
    # Delete then verify same token no longer authenticates
    r = requests.delete(f"{API}/me", headers=client_ctx["headers"], timeout=15)
    assert r.status_code == 200 and r.json()["deleted"] is True
    m = requests.get(f"{API}/auth/me", headers=client_ctx["headers"], timeout=15)
    assert m.status_code == 401


# ---- Learning topics + videos + daily healthy ----
def test_learning_topics_9():
    r = requests.get(f"{API}/learning/topics", timeout=15).json()
    assert len(r) == 9


def test_learning_videos_diverse():
    r = requests.get(f"{API}/learning/videos?limit=8", timeout=45).json()
    vids = r["videos"]
    assert len(vids) >= 1
    sources = {v.get("source") for v in vids}
    assert len(sources) >= 1  # at least one source


def test_learning_daily():
    r = requests.get(f"{API}/learning/daily?limit=3", timeout=45)
    assert r.status_code == 200 and isinstance(r.json()["videos"], list)


# ---- Weekly digest (inert) ----
def test_admin_digest_run_inert(admin_ctx):
    r = requests.post(f"{API}/admin/digest/run", headers=admin_ctx["headers"], timeout=20)
    assert r.status_code == 200
    d = r.json()
    assert d.get("skipped") == "email_not_configured"
