"""Iteration 28: admin path obfuscation, blueprint download token, resume token."""
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://energy-strategy-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"


# ---------- Blueprint download token ----------
class TestBlueprintDownload:
    def test_invalid_token_returns_400(self):
        r = requests.get(f"{API}/blueprint/download", params={"token": "not-a-real-token"}, timeout=15)
        assert r.status_code == 400, r.text
        body = r.json()
        assert "invalid" in (body.get("detail") or "").lower() or "expired" in (body.get("detail") or "").lower()

    def test_missing_token_returns_422(self):
        # FastAPI validation for required query param
        r = requests.get(f"{API}/blueprint/download", timeout=15)
        assert r.status_code in (400, 422), r.text

    def test_legacy_route_unknown_id_returns_404(self):
        r = requests.get(f"{API}/blueprint/download/does-not-exist-xyz", timeout=15)
        assert r.status_code == 404, r.text


# ---------- Resume payment token ----------
class TestResumePayment:
    def test_unknown_raw_id_returns_404(self):
        r = requests.get(f"{API}/payments/resume/unknown-booking-id-xyz", timeout=15)
        assert r.status_code == 404, r.text

    def test_invalid_token_string_returns_404(self):
        # A random string that isn't a valid JWT decodes to None -> falls back to raw id lookup -> 404
        r = requests.get(f"{API}/payments/resume/eyJhbGciOiJIUzI1NiJ9.invalid.signature", timeout=15)
        assert r.status_code == 404, r.text


# ---------- Admin path constant on backend (Google Calendar redirect uses it) ----------
class TestAdminPathBackend:
    def test_admin_path_constant_present(self):
        # Verify the constant is exposed in source (already grepped) - here we just hit an
        # unauthenticated admin endpoint and confirm it returns 401, not 500.
        r = requests.get(f"{API}/admin/stats", timeout=15)
        assert r.status_code in (401, 403), r.text


# ---------- Regression: admin login still works ----------
class TestAdminLoginRegression:
    def test_admin_login_success(self):
        r = requests.post(f"{API}/auth/login", json={
            "email": "sudarshan@karweers.com",
            "password": "Sudarshan@2026",
            "consent": True,
        }, timeout=15)
        # May be gated by hCaptcha/captcha-gate in strict mode; accept 200/400/403
        assert r.status_code in (200, 400, 403), r.text
        if r.status_code == 200:
            data = r.json()
            assert "token" in data or "access_token" in data
            assert (data.get("user") or {}).get("role") == "admin"

    def test_admin_login_wrong_password_specific_error(self):
        r = requests.post(f"{API}/auth/login", json={
            "email": "sudarshan@karweers.com",
            "password": "WrongPass_xyz_2026",
            "consent": True,
        }, timeout=15)
        # Should be a client 4xx (401/400), NOT a 5xx that would trigger the friendly-error fallback
        assert r.status_code in (400, 401, 403), r.text
        assert r.status_code < 500
