"""Iteration 15: game score persistence + leaderboard + my/simulations + library-digest admin."""
import os
import uuid
import requests
import pytest
from dotenv import load_dotenv

load_dotenv("/app/frontend/.env")
BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = BASE + "/api"
GAME = "art-of-war"

ADMIN = {"email": "sudarshan@karweers.com", "password": "Sudarshan@2026",
         "captcha_token": "preview", "consent": True}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def client_token():
    email = f"TEST_sim_{uuid.uuid4().hex[:8]}@test.com"
    payload = {"name": "TEST Sim", "email": email, "password": "Test@1234",
               "captcha_token": "preview", "consent": True}
    r = requests.post(f"{API}/auth/register", json=payload, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["token"]


def _first_round_ids(game_slug):
    g = requests.get(f"{API}/games/{game_slug}", timeout=15).json()
    # Pick first option per round for repeatable payload
    return {str(r["id"]): r["options"][0]["id"] for r in g["rounds"]}


# ---------------- Game score (anon vs auth) ----------------
def test_score_anon_returns_saved_false():
    answers = _first_round_ids(GAME)
    r = requests.post(f"{API}/games/{GAME}/score", json={"answers": answers}, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["saved"] is False
    for k in ("score", "band", "lessons", "breakdown", "max_score"):
        assert k in d, f"missing {k}"
    assert isinstance(d["breakdown"], list) and len(d["breakdown"]) == 5


def test_score_auth_returns_saved_true_persists(client_token):
    answers = _first_round_ids(GAME)
    h = {"Authorization": f"Bearer {client_token}"}
    r = requests.post(f"{API}/games/{GAME}/score", json={"answers": answers}, headers=h, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["saved"] is True
    assert "score" in d and "band" in d
    # Verify persistence via leaderboard my_runs
    lb = requests.get(f"{API}/games/{GAME}/leaderboard", headers=h, timeout=15).json()
    assert lb.get("plays", 0) >= 1
    assert lb.get("my_best") is not None


# ---------------- Leaderboard ----------------
def test_leaderboard_public_shape():
    r = requests.get(f"{API}/games/{GAME}/leaderboard", timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert "top" in d and isinstance(d["top"], list)
    assert "max_score" in d
    assert len(d["top"]) <= 10
    # Should NOT expose my_* fields on public call
    assert "my_best" not in d
    assert "my_runs" not in d


def test_leaderboard_authed_includes_my_data(client_token):
    h = {"Authorization": f"Bearer {client_token}"}
    r = requests.get(f"{API}/games/{GAME}/leaderboard", headers=h, timeout=15)
    assert r.status_code == 200
    d = r.json()
    assert "my_best" in d and "my_runs" in d and "plays" in d
    assert isinstance(d["my_runs"], list)


# ---------------- My simulations ----------------
def test_my_simulations_requires_auth():
    r = requests.get(f"{API}/me/simulations", timeout=15)
    assert r.status_code in (401, 403)


def test_my_simulations_aggregates(client_token):
    h = {"Authorization": f"Bearer {client_token}"}
    r = requests.get(f"{API}/me/simulations", headers=h, timeout=15)
    assert r.status_code == 200, r.text
    d = r.json()
    assert "games" in d and "total_runs" in d
    assert d["total_runs"] >= 1
    entry = next((x for x in d["games"] if x["game_slug"] == GAME), None)
    assert entry is not None
    for k in ("best", "plays", "last_played", "max_score", "game_title"):
        assert k in entry


# ---------------- Library digest admin ----------------
def test_library_digest_admin_only():
    r = requests.post(f"{API}/admin/library-digest/run", timeout=15)
    assert r.status_code in (401, 403)


def test_library_digest_run_admin(admin_token):
    h = {"Authorization": f"Bearer {admin_token}"}
    r = requests.post(f"{API}/admin/library-digest/run", headers=h, timeout=60)
    assert r.status_code == 200, r.text
    d = r.json()
    # Either email is configured (sent:true, subscribers:N) OR skipped
    assert ("sent" in d)
    if d.get("sent"):
        assert "subscribers" in d and isinstance(d["subscribers"], int)
