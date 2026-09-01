"""Iteration 19: new services + strategy toolkit + insights backend tests."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/") or "https://energy-strategy-hub.preview.emergentagent.com"
API = f"{BASE_URL}/api"

EXPECTED_ORDER = [
    "business-strategy", "ma-advisory", "fund-raising", "premium-consultation",
    "business-coaching", "re-storage-hydrogen", "green-climate-financing", "asset-monetisation",
]


# ---------------- Services ----------------
class TestServices:
    def test_list_services_order_and_signature(self):
        r = requests.get(f"{API}/services", timeout=20)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)
        slugs = [s["slug"] for s in data]
        assert slugs == EXPECTED_ORDER, f"Got order: {slugs}"
        # signature flags
        sig_map = {s["slug"]: s["signature"] for s in data}
        for slug in ["business-strategy", "ma-advisory", "fund-raising"]:
            assert sig_map[slug] is True, f"{slug} must be signature"
        for slug in EXPECTED_ORDER[3:]:
            assert sig_map[slug] is False, f"{slug} should not be signature"

    def test_business_strategy_workflow(self):
        r = requests.get(f"{API}/services/business-strategy", timeout=15)
        assert r.status_code == 200
        d = r.json()
        keys = [p["key"] for p in d["workflow"]]
        assert keys == ["entry", "feasibility", "growth", "portfolio"]
        assert isinstance(d.get("approach"), list) and len(d["approach"]) >= 1
        assert isinstance(d.get("outcomes"), list) and len(d["outcomes"]) >= 1

    def test_ma_advisory_airline_loyalty(self):
        r = requests.get(f"{API}/services/ma-advisory", timeout=15)
        assert r.status_code == 200
        text = r.text.lower()
        assert "airline" in text and ("loyalty" in text or "frequent-flyer" in text or "frequent flyer" in text)

    def test_fund_raising_3billion(self):
        r = requests.get(f"{API}/services/fund-raising", timeout=15)
        assert r.status_code == 200
        text = r.text.lower()
        assert "3 billion" in text or "$3b" in text or "3b+" in text or "3b " in text

    def test_unknown_service_404(self):
        r = requests.get(f"{API}/services/does-not-exist", timeout=15)
        assert r.status_code == 404


# ---------------- Strategy tools ----------------
class TestStrategyTools:
    def test_list_13(self):
        r = requests.get(f"{API}/strategy-tools", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 13
        for t in data:
            assert {"slug", "name", "category", "tagline"}.issubset(t.keys())

    def test_ansoff_detail(self):
        r = requests.get(f"{API}/strategy-tools/ansoff-matrix", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert "grid" in d and "when_to_use" in d and "how_to" in d and "watch_outs" in d

    def test_unknown_tool_404(self):
        r = requests.get(f"{API}/strategy-tools/nope", timeout=15)
        assert r.status_code == 404

    def test_ansoff_pdf(self):
        r = requests.get(f"{API}/strategy-tools/ansoff-matrix.pdf", timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert len(r.content) > 500
        assert r.content[:4] == b"%PDF"

    def test_fishbone_pdf(self):
        r = requests.get(f"{API}/strategy-tools/fishbone-ishikawa.pdf", timeout=30)
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")
        assert len(r.content) > 500

    def test_unknown_pdf_404(self):
        r = requests.get(f"{API}/strategy-tools/nope.pdf", timeout=15)
        assert r.status_code == 404


# ---------------- Strategy insights ----------------
class TestStrategyInsights:
    def test_list_6(self):
        r = requests.get(f"{API}/strategy-insights", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert len(data) == 6
        for a in data:
            assert {"slug", "title", "dek", "read_time", "category"}.issubset(a.keys())

    def test_get_ma_value_creation(self):
        r = requests.get(f"{API}/strategy-insights/ma-value-creation", timeout=15)
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d.get("sections"), list) and len(d["sections"]) >= 1

    def test_unknown_insight_404(self):
        r = requests.get(f"{API}/strategy-insights/nope", timeout=15)
        assert r.status_code == 404
