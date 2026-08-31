"""Backend tests for Leadership Library + CXO Strategy Simulation games."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://energy-strategy-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

EXPECTED_BOOK_FIELDS = {"slug", "title", "author", "year", "theme", "blurb", "why_sk",
                       "lessons", "ritual", "ritual_pro", "ritual_personal",
                       "public_domain", "has_read", "has_audio", "amazon"}


# ---------------- Library ----------------
class TestBooksList:
    def test_shelf_returns_12(self):
        r = requests.get(f"{API}/books", timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        assert len(data) == 12, f"expected 12 books on daily shelf, got {len(data)}"
        for b in data:
            missing = EXPECTED_BOOK_FIELDS - set(b.keys())
            assert not missing, f"missing fields {missing} in book {b.get('slug')}"

    def test_scope_all_returns_39(self):
        r = requests.get(f"{API}/books", params={"scope": "all"}, timeout=30)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 39, f"expected 39 books total, got {len(data)}"

    def test_daily_shelf_deterministic(self):
        r1 = requests.get(f"{API}/books", timeout=30).json()
        r2 = requests.get(f"{API}/books", timeout=30).json()
        s1 = [b["slug"] for b in r1]
        s2 = [b["slug"] for b in r2]
        assert s1 == s2, "daily shelf not deterministic within the same day"


class TestBookDetail:
    def test_public_domain_book(self):
        r = requests.get(f"{API}/books/art-of-war", timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["has_read"] is True
        assert "videos" in d
        # videos may be empty if YouTube scraping is briefly unreachable (acceptable per request)
        assert isinstance(d["videos"], list)

    def test_book_text(self):
        r = requests.get(f"{API}/books/art-of-war/text", timeout=60)
        assert r.status_code == 200
        assert len(r.text) > 500, f"text too short: {len(r.text)}"

    def test_unknown_book_404(self):
        r = requests.get(f"{API}/books/does-not-exist-xyz", timeout=30)
        assert r.status_code == 404


# ---------------- Games ----------------
class TestGamesList:
    def test_six_games(self):
        r = requests.get(f"{API}/games", timeout=30)
        assert r.status_code == 200
        games = r.json()
        assert len(games) == 6
        expected_slugs = {"art-of-war", "extreme-ownership", "team-trust",
                          "hiring", "financial-management", "supply-chain"}
        assert {g["slug"] for g in games} == expected_slugs
        for g in games:
            for f in ("slug", "title", "framework", "rounds", "max_score", "tag", "blurb"):
                assert f in g, f"missing {f} in {g.get('slug')}"
            assert isinstance(g["rounds"], int)
            assert g["max_score"] == 15


class TestGameDetail:
    def test_game_detail(self):
        r = requests.get(f"{API}/games/art-of-war", timeout=30)
        assert r.status_code == 200
        g = r.json()
        assert len(g["rounds"]) == 5
        for rd in g["rounds"]:
            assert len(rd["options"]) >= 2
            for opt in rd["options"]:
                assert set(("id", "text", "score", "feedback")).issubset(opt.keys())

    def test_unknown_game_404(self):
        r = requests.get(f"{API}/games/no-such-game", timeout=30)
        assert r.status_code == 404


class TestGameScore:
    def _best_answers(self, slug):
        g = requests.get(f"{API}/games/{slug}", timeout=30).json()
        answers = {}
        for rd in g["rounds"]:
            best = max(rd["options"], key=lambda o: o["score"])
            answers[str(rd["id"])] = best["id"]
        return g, answers

    def test_best_answers_score_max_high(self):
        g, answers = self._best_answers("extreme-ownership")
        r = requests.post(f"{API}/games/extreme-ownership/score",
                          json={"answers": answers}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        assert d["score"] == d["max_score"] == 15
        assert d["band"] == "high"
        assert isinstance(d["lessons"], list) and len(d["lessons"]) > 0
        assert isinstance(d["breakdown"], list) and len(d["breakdown"]) == 5

    def test_mixed_answers_band(self):
        # Choose the WORST option in each round -> band should be low
        g = requests.get(f"{API}/games/hiring", timeout=30).json()
        worst = {}
        for rd in g["rounds"]:
            wo = min(rd["options"], key=lambda o: o["score"])
            worst[str(rd["id"])] = wo["id"]
        r = requests.post(f"{API}/games/hiring/score", json={"answers": worst}, timeout=30)
        assert r.status_code == 200
        d = r.json()
        pct = d["score"] / d["max_score"]
        assert pct < 0.5
        assert d["band"] == "low"

    def test_score_unknown_game_404(self):
        r = requests.post(f"{API}/games/unknown-slug-xyz/score",
                          json={"answers": {}}, timeout=30)
        assert r.status_code == 404
