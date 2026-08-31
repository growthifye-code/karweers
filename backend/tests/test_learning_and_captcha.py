"""Tests for iteration 4: Learning Hub, recommendation engine, Google session auth, and strict hCaptcha."""
import os
import time
import uuid
import pytest
import requests
from pymongo import MongoClient
from datetime import datetime, timezone, timedelta

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL") or open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split("\n")[0].strip()
BASE_URL = BASE_URL.rstrip("/")
API = f"{BASE_URL}/api"

MONGO_URL = os.environ.get("MONGO_URL")
DB_NAME = os.environ.get("DB_NAME")
if not MONGO_URL:
    # Read from backend/.env
    for line in open("/app/backend/.env").read().splitlines():
        if line.startswith("MONGO_URL="):
            MONGO_URL = line.split("=", 1)[1].strip().strip('"')
        if line.startswith("DB_NAME="):
            DB_NAME = line.split("=", 1)[1].strip().strip('"')

mongo = MongoClient(MONGO_URL)
db = mongo[DB_NAME]


# --------- hCaptcha strict enforcement ---------
CAPTCHA_ENDPOINTS = [
    ("/newsletter", {"email": f"tst_cap_{uuid.uuid4().hex[:6]}@example.com"}),
    ("/auth/login", {"email": "nobody@example.com", "password": "wrong"}),
    ("/auth/register", {"name": "T", "email": f"tst_cap_{uuid.uuid4().hex[:6]}@example.com", "password": "P@ssword1"}),
    ("/consultations", {"name": "T", "email": f"tst_cap_{uuid.uuid4().hex[:6]}@example.com", "area": "energy", "message": "hi"}),
    ("/payments/checkout", {"package_id": "discovery", "origin_url": BASE_URL, "name": "T", "email": f"tst_cap_{uuid.uuid4().hex[:6]}@example.com"}),
]


@pytest.mark.parametrize("path,body", CAPTCHA_ENDPOINTS)
def test_missing_captcha_returns_400(path, body):
    r = requests.post(f"{API}{path}", json=body, timeout=15)
    assert r.status_code == 400, f"{path}: expected 400 missing captcha, got {r.status_code} {r.text[:200]}"


@pytest.mark.parametrize("path,body", CAPTCHA_ENDPOINTS)
def test_invalid_captcha_returns_403(path, body):
    payload = dict(body)
    payload["captcha_token"] = "invalid-fake-token-abc123"
    r = requests.post(f"{API}{path}", json=payload, timeout=20)
    assert r.status_code == 403, f"{path}: expected 403 invalid captcha, got {r.status_code} {r.text[:200]}"
    assert "captcha" in r.text.lower()


# --------- Learning endpoints ---------

def test_learning_topics():
    r = requests.get(f"{API}/learning/topics", timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 9
    for t in data:
        assert "id" in t and "label" in t and "blurb" in t


def test_learning_videos_default():
    r = requests.get(f"{API}/learning/videos?limit=12", timeout=60)
    assert r.status_code == 200
    videos = r.json()["videos"]
    assert isinstance(videos, list)
    assert len(videos) > 0, "no videos returned from RSS pool"
    for v in videos:
        for k in ("video_id", "title", "source", "source_url", "topics", "thumbnail"):
            assert k in v, f"missing {k} in {v}"
        assert isinstance(v["topics"], list)
    # diversity: sources should be interleaved (not all same)
    sources = [v["source"] for v in videos]
    assert len(set(sources)) >= 3, f"low source diversity: {sources}"
    # first two should not be from same source (interleaved)
    if len(videos) >= 2:
        # allow occasional adjacency but ensure top 3 aren't identical
        top3 = sources[:3]
        assert len(set(top3)) >= 2, f"top-3 not interleaved: {top3}"


def test_learning_videos_energy_filter():
    r = requests.get(f"{API}/learning/videos?topic=energy&limit=20", timeout=60)
    assert r.status_code == 200
    videos = r.json()["videos"]
    assert len(videos) > 0
    for v in videos:
        assert "energy" in v["topics"], f"video {v['video_id']} does not have energy topic: {v['topics']}"


def test_learning_daily():
    r = requests.get(f"{API}/learning/daily?limit=10", timeout=60)
    assert r.status_code == 200
    videos = r.json()["videos"]
    assert 0 < len(videos) <= 10
    # variety of topics
    topics_seen = set()
    for v in videos:
        for t in v.get("topics", []):
            topics_seen.add(t)
    assert len(topics_seen) >= 3, f"low topic variety in daily: {topics_seen}"


def test_learning_recommended_unauth():
    r = requests.get(f"{API}/learning/recommended?limit=8", timeout=60)
    assert r.status_code == 200
    data = r.json()
    assert data["personalised"] is False
    assert isinstance(data["videos"], list)
    assert len(data["videos"]) > 0


# --------- Google session auth flow ---------
@pytest.fixture
def google_session():
    uid = f"tst_user_{uuid.uuid4().hex[:8]}"
    token = f"test_session_{uuid.uuid4().hex}"
    email = f"tst.google.{uuid.uuid4().hex[:8]}@example.com"
    db.users.insert_one({
        "id": uid, "email": email, "name": "Google Test",
        "picture": "https://via.placeholder.com/150", "role": "client",
        "auth": "google", "created_at": datetime.now(timezone.utc).isoformat(),
    })
    db.user_sessions.insert_one({
        "user_id": uid, "session_token": token,
        "expires_at": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    yield {"uid": uid, "token": token, "email": email}
    db.users.delete_one({"id": uid})
    db.user_sessions.delete_one({"session_token": token})
    db.activity_events.delete_many({"user_id": uid})


def test_auth_me_bearer_session(google_session):
    h = {"Authorization": f"Bearer {google_session['token']}"}
    r = requests.get(f"{API}/auth/me", headers=h, timeout=10)
    assert r.status_code == 200, r.text
    u = r.json()
    assert u["id"] == google_session["uid"]
    assert u["email"] == google_session["email"]
    assert u["role"] == "client"


def test_track_with_auth_returns_topics(google_session):
    h = {"Authorization": f"Bearer {google_session['token']}"}
    r = requests.post(f"{API}/track", json={"kind": "service", "ref": "re-storage-hydrogen"}, headers=h, timeout=10)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["tracked"] is True
    assert "energy" in d["topics"]


def test_track_without_auth_returns_tracked_false():
    r = requests.post(f"{API}/track", json={"kind": "service", "ref": "re-storage-hydrogen"}, timeout=10)
    assert r.status_code == 200
    assert r.json()["tracked"] is False


def test_recommended_personalised_after_tracking(google_session):
    h = {"Authorization": f"Bearer {google_session['token']}"}
    # multiple energy-related tracks
    for ref in ["re-storage-hydrogen", "re-storage-hydrogen", "green-climate-financing"]:
        requests.post(f"{API}/track", json={"kind": "service", "ref": ref}, headers=h, timeout=10)
    requests.post(f"{API}/track", json={"kind": "topic", "ref": "energy"}, headers=h, timeout=10)
    r = requests.get(f"{API}/learning/recommended?limit=8", headers=h, timeout=60)
    assert r.status_code == 200
    d = r.json()
    assert d["personalised"] is True, d
    assert len(d["videos"]) > 0
    # interests should include an energy-related topic
    energy_topics = {"energy", "climate-finance", "technology"}
    assert any(t in energy_topics for t in d["interests"]), d["interests"]


# --------- JWT login reachability (strict captcha) ---------

def test_admin_login_rejects_invalid_captcha():
    r = requests.post(f"{API}/auth/login", json={
        "email": "sudarshan@karweers.com", "password": "Sudarshan@2026",
        "captcha_token": "fake-token"
    }, timeout=15)
    assert r.status_code == 403, r.text
