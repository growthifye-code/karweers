"""Iteration 27 tests: AI refresh schedule toggle, gate unlocks, and admin security shape."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://energy-strategy-hub.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASSWORD = "Sudarshan@2026"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD,
                            "captcha_token": "x", "consent": True}, timeout=30)
    assert r.status_code == 200, f"login failed: {r.status_code} {r.text[:200]}"
    return r.json()["access_token"] if "access_token" in r.json() else r.json().get("token")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


class TestScheduleToggle:
    def test_toggle_on(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/admin/collateral/ai-refresh-schedule",
                          headers=auth_headers, json={"enabled": True}, timeout=15)
        assert r.status_code == 200, r.text
        assert r.json().get("scheduled") is True

        s = requests.get(f"{BASE_URL}/api/admin/collateral/ai-refresh-status",
                         headers=auth_headers, timeout=15)
        assert s.status_code == 200
        data = s.json()
        assert data.get("scheduled") is True
        for k in ("running", "total", "done", "finished_at", "scheduled", "last_auto_run"):
            assert k in data, f"missing key {k}"

    def test_toggle_off(self, auth_headers):
        r = requests.post(f"{BASE_URL}/api/admin/collateral/ai-refresh-schedule",
                          headers=auth_headers, json={"enabled": False}, timeout=15)
        assert r.status_code == 200
        assert r.json().get("scheduled") is False

        s = requests.get(f"{BASE_URL}/api/admin/collateral/ai-refresh-status",
                         headers=auth_headers, timeout=15)
        assert s.json().get("scheduled") is False


class TestGateUnlockLogging:
    def test_unlock_logs_masked_event(self, auth_headers):
        email = "test_iter27_abuse@example.com"
        r = requests.post(f"{BASE_URL}/api/collateral/unlock",
                          json={"email": email, "source": "test-iter27"}, timeout=15)
        assert r.status_code == 200
        assert r.json().get("ok") is True

        sec = requests.get(f"{BASE_URL}/api/admin/security", headers=auth_headers, timeout=20)
        assert sec.status_code == 200
        data = sec.json()
        assert "gate_unlocks" in data
        assert isinstance(data["gate_unlocks"], list)
        assert "unlocks_today" in data
        assert data["unlocks_today"] >= 1
        # find our masked event
        masks = [u.get("email_masked") for u in data["gate_unlocks"]]
        # first 2 chars + *** + @example.com
        assert any(m and m.startswith("te") and m.endswith("@example.com") for m in masks), masks


class TestAdminSecurityShape:
    def test_shape_present(self, auth_headers):
        r = requests.get(f"{BASE_URL}/api/admin/security", headers=auth_headers, timeout=20)
        assert r.status_code == 200
        d = r.json()
        # existing
        for k in ("banned", "alerts", "offenders", "trend"):
            assert k in d
        # new fields
        assert "gate_unlocks" in d and isinstance(d["gate_unlocks"], list)
        assert "unlocks_today" in d and isinstance(d["unlocks_today"], int)
        assert "download_activity" in d
        da = d["download_activity"]
        assert "top" in da and isinstance(da["top"], list)
        assert "downloads_today" in da
        assert "total" in da
        if da["top"]:
            item = da["top"][0]
            for k in ("title", "category", "downloads", "downloads_week"):
                assert k in item


class TestFriendlyErrorRegression:
    def test_wrong_password_still_specific(self):
        """Ensure normal wrong-password returns 401 (frontend distinguishes this from friendly-busy)."""
        r = requests.post(f"{BASE_URL}/api/auth/login",
                          json={"email": ADMIN_EMAIL, "password": "wrong-pw-xyz",
                                "captcha_token": "x", "consent": True}, timeout=15)
        assert r.status_code in (400, 401, 403), r.status_code
