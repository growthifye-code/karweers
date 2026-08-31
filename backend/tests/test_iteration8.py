"""Iteration 8: Legal pages, Google Calendar sync (no-op path), Vault lockout status."""
import os
import sys
import uuid
import pytest
import requests
from datetime import datetime, timezone, timedelta, date
from pymongo import MongoClient

sys.path.insert(0, "/app/backend")
from auth import create_access_token  # noqa: E402

BASE = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE}/api"
mongo = MongoClient(os.environ["MONGO_URL"])
db = mongo[os.environ["DB_NAME"]]
ADMIN_EMAIL = "sudarshan@karweers.com"


@pytest.fixture(scope="module")
def admin_headers():
    u = db.users.find_one({"email": ADMIN_EMAIL})
    assert u, "admin user not found"
    tok = create_access_token(u["id"], u["email"], u.get("role", "admin"))
    return {"Authorization": f"Bearer {tok}"}


def _monday(d):
    return d - timedelta(days=d.weekday())


def _pick_future_slot():
    meta = db.app_meta.find_one({"_id": "availability"}) or {}
    ws = date.fromisoformat(meta.get("published_week_start") or _monday(datetime.now(timezone.utc).date()).isoformat())
    now = datetime.now(timezone.utc)
    for i in range(7):
        d = ws + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        for t in ["15:00", "16:00", "14:00", "11:00", "10:00"]:
            h, m = map(int, t.split(":"))
            dt = datetime(d.year, d.month, d.day, h, m, tzinfo=timezone.utc)
            if dt > now + timedelta(minutes=30):
                return d.isoformat(), t
    pytest.skip("no slot")


# ---------------- Legal pages content ----------------
class TestLegalPages:
    def _fetch(self, path):
        r = requests.get(f"{BASE}{path}", timeout=15)
        assert r.status_code == 200
        return r.text.lower()

    def test_terms_no_stripe(self):
        # Legal pages are rendered client-side (React); check the JS bundle source is served
        # instead test the source file directly since the DOCS object lives in JS
        with open("/app/frontend/src/pages/LegalPage.jsx") as f:
            src = f.read().lower()
        assert "stripe" not in src, "Stripe reference still present in LegalPage.jsx"
        assert "paid in advance" not in src
        assert "bookings & confirmation" in src
        assert "booking & cancellation policy" in src

    def test_refund_title_renamed(self):
        with open("/app/frontend/src/pages/LegalPage.jsx") as f:
            src = f.read()
        assert '"Booking & Cancellation Policy"' in src

    def test_privacy_no_stripe(self):
        with open("/app/frontend/src/pages/LegalPage.jsx") as f:
            src = f.read().lower()
        assert "stripe" not in src
        # "card details" appears only as a NEGATION ("We do not take card details")
        # which is acceptable — verify it's not listed as data we collect
        assert "we do not take card details" in src


# ---------------- Vault lockout status ----------------
class TestVaultStatus:
    def test_vault_status_shape(self, admin_headers):
        r = requests.get(f"{API}/admin/vault/status", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("lock_frozen", "lock_seconds_left", "fails", "max_fails"):
            assert k in d, f"missing {k}"
        assert d["max_fails"] == 5
        assert isinstance(d["lock_frozen"], bool)


# ---------------- Google Calendar endpoints ----------------
class TestCalendarEndpoints:
    def test_status_initial(self, admin_headers):
        # Ensure no connection doc
        db.app_meta.delete_one({"_id": "google_calendar"})
        r = requests.get(f"{API}/admin/calendar/status", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["configured"] is True
        assert d["connected"] is False
        assert d["email"] is None

    def test_oauth_start(self, admin_headers):
        r = requests.get(f"{API}/admin/calendar/oauth/start", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        url = r.json().get("authorization_url", "")
        assert "accounts.google.com" in url
        assert "client_id=" in url
        assert "state=" in url

    def test_oauth_start_requires_admin(self):
        r = requests.get(f"{API}/admin/calendar/oauth/start", timeout=15)
        assert r.status_code == 401

    def test_disconnect(self, admin_headers):
        r = requests.post(f"{API}/admin/calendar/disconnect", headers=admin_headers, json={}, timeout=15)
        assert r.status_code == 200
        assert r.json().get("success") is True

    def test_callback_error_redirects(self):
        r = requests.get(f"{API}/admin/calendar/oauth/callback",
                         params={"error": "access_denied"},
                         allow_redirects=False, timeout=15)
        assert r.status_code in (302, 307)
        assert "/admin?calendar=error" in r.headers.get("location", "")

    def test_callback_invalid_state_no_tokens_stored(self):
        db.app_meta.delete_one({"_id": "google_calendar"})
        r = requests.get(f"{API}/admin/calendar/oauth/callback",
                         params={"code": "fake", "state": "invalid-state"},
                         allow_redirects=False, timeout=15)
        assert r.status_code in (302, 307)
        assert "/admin?calendar=error" in r.headers.get("location", "")
        # ensure nothing persisted
        assert db.app_meta.find_one({"_id": "google_calendar"}) is None


# ---------------- Booking actions with calendar disconnected (safe no-op) ----------------
class TestBookingActionsWithoutCalendar:
    @pytest.fixture(autouse=True)
    def _no_calendar_conn(self):
        db.app_meta.delete_one({"_id": "google_calendar"})
        yield

    def _seed_booking(self, date_str, time_str):
        bid = str(uuid.uuid4())
        db.consultations.insert_one({
            "id": bid, "name": "Test", "email": f"test-booking-{bid[:8]}@x.io",
            "status": "pending_confirmation", "package": "Strategy",
            "package_id": "strategy", "minutes": 60, "amount": 299.0,
            "slot_date": date_str, "slot_time": time_str,
            "occupied": [time_str], "source": "booking-form",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        return bid

    def test_confirm_no_calendar(self, admin_headers):
        date_str, time_str = _pick_future_slot()
        bid = self._seed_booking(date_str, time_str)
        try:
            r = requests.post(f"{API}/admin/bookings/{bid}/confirm",
                              headers=admin_headers, json={}, timeout=20)
            assert r.status_code == 200, r.text
            doc = db.consultations.find_one({"id": bid})
            assert doc["status"] == "confirmed"
            # no gcal_event_id should be set since not connected
            assert not doc.get("gcal_event_id")
        finally:
            db.consultations.delete_one({"id": bid})

    def test_reschedule_no_calendar(self, admin_headers):
        date_str, time_str = _pick_future_slot()
        bid = self._seed_booking(date_str, time_str)
        try:
            requests.post(f"{API}/admin/bookings/{bid}/confirm",
                          headers=admin_headers, json={}, timeout=20)
            new_time = "17:00" if time_str != "17:00" else "16:00"
            r = requests.post(f"{API}/admin/bookings/{bid}/reschedule",
                              headers=admin_headers,
                              json={"date": date_str, "time": new_time}, timeout=20)
            assert r.status_code == 200, r.text
            doc = db.consultations.find_one({"id": bid})
            assert doc["slot_time"] == new_time
        finally:
            db.consultations.delete_one({"id": bid})

    def test_decline_no_calendar(self, admin_headers):
        date_str, time_str = _pick_future_slot()
        bid = self._seed_booking(date_str, time_str)
        try:
            r = requests.post(f"{API}/admin/bookings/{bid}/decline",
                              headers=admin_headers, json={"reason": "t"}, timeout=20)
            assert r.status_code == 200, r.text
            doc = db.consultations.find_one({"id": bid})
            assert doc["status"] == "declined"
        finally:
            db.consultations.delete_one({"id": bid})
