"""
Iteration 7 backend tests: Stripe removal + FREE booking + availability + admin queue.

We mint an admin JWT locally (captcha bypasses login) and interact with the
external REACT_APP_BACKEND_URL. Booking creation itself calls verify_captcha,
so instead of POSTing /consultation/book we insert a consultation doc directly
into Mongo (per review instructions) to test slot-conflict logic.
"""
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
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "sudarshan@karweers.com")

mongo = MongoClient(MONGO_URL)
db = mongo[DB_NAME]


# ---------------- Fixtures ----------------
@pytest.fixture(scope="module")
def admin_token():
    u = db.users.find_one({"email": ADMIN_EMAIL})
    assert u, f"admin user {ADMIN_EMAIL} not seeded"
    return create_access_token(u["id"], u["email"], u.get("role", "admin"))


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture(scope="module")
def orig_availability():
    doc = db.app_meta.find_one({"_id": "availability"})
    yield doc
    # restore
    if doc is None:
        db.app_meta.delete_one({"_id": "availability"})
    else:
        db.app_meta.replace_one({"_id": "availability"}, doc, upsert=True)


@pytest.fixture(autouse=True)
def _cleanup_test_bookings():
    yield
    db.consultations.delete_many({"email": {"$regex": "^test-booking-"}})


def _monday(d):
    return d - timedelta(days=d.weekday())


def _pick_future_slot():
    """Return (date_str, time_str) for a future weekday slot within published week."""
    meta = db.app_meta.find_one({"_id": "availability"}) or {}
    ws = date.fromisoformat(meta.get("published_week_start") or _monday(datetime.now(timezone.utc).date()).isoformat())
    now = datetime.now(timezone.utc)
    for i in range(7):
        d = ws + timedelta(days=i)
        if d.weekday() >= 5:
            continue
        # try 15:00, 16:00 etc — well within 09:30-18:30
        for t in ["15:00", "16:00", "14:00", "11:00", "10:00"]:
            h, m = map(int, t.split(":"))
            dt = datetime(d.year, d.month, d.day, h, m, tzinfo=timezone.utc)
            if dt > now + timedelta(minutes=30):
                return d.isoformat(), t
    pytest.skip("No future weekday slot in published week")


# ---------------- Stripe removal ----------------
class TestStripeRemoved:
    @pytest.mark.parametrize("path,method", [
        ("/payments/packages", "get"),
        ("/payments/checkout", "post"),
        ("/payments/status/xyz", "get"),
        ("/webhook/stripe", "post"),
        ("/bookings/schedule", "post"),
    ])
    def test_endpoint_removed(self, path, method):
        r = requests.request(method, f"{API}{path}", json={}, timeout=15)
        assert r.status_code in (404, 405), f"{path} still exists (status {r.status_code})"


# ---------------- Consultation packages ----------------
class TestPackages:
    def test_three_packages(self):
        r = requests.get(f"{API}/consultation/packages", timeout=15)
        assert r.status_code == 200
        data = r.json()
        ids = {p["id"] for p in data}
        assert ids == {"discovery", "strategy", "deepdive"}
        by_id = {p["id"]: p for p in data}
        assert by_id["discovery"]["minutes"] == 30
        assert by_id["strategy"]["minutes"] == 60
        assert by_id["deepdive"]["minutes"] == 90
        for p in data:
            assert "amount" in p and "duration" in p and "features" in p
            assert isinstance(p["features"], list) and len(p["features"]) > 0


# ---------------- Public availability ----------------
class TestPublicAvailability:
    def test_shape_and_working_hours(self):
        r = requests.get(f"{API}/consultation/availability", timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "week_start" in data and "days" in data
        assert data.get("hours") and "09:30" in data["hours"]
        assert data.get("days_label") == "Mon\u2013Fri"
        ws = date.fromisoformat(data["week_start"])
        assert ws.weekday() == 0  # Monday
        now = datetime.now(timezone.utc)
        for day in data["days"]:
            d = date.fromisoformat(day["date"])
            assert d.weekday() < 5, f"non-weekday returned: {d}"
            for t in day["slots"]:
                h, m = map(int, t.split(":"))
                mins = h * 60 + m
                assert 9 * 60 + 30 <= mins <= 18 * 60 + 30
                # future only
                dt = datetime(d.year, d.month, d.day, h, m, tzinfo=timezone.utc)
                assert dt > now, f"past slot returned {day['date']} {t}"

    def test_no_auth_required(self):
        r = requests.get(f"{API}/consultation/availability", timeout=15)
        assert r.status_code == 200


# ---------------- Slot conflict (via direct DB insert) ----------------
class TestSlotConflict:
    def test_60min_booking_blocks_two_slots(self):
        date_str, time_str = _pick_future_slot()
        # baseline
        before = requests.get(f"{API}/consultation/availability", timeout=15).json()
        by_date = {d["date"]: set(d["slots"]) for d in before["days"]}
        assert time_str in by_date.get(date_str, set()), f"expected {time_str} available first"
        h, m = map(int, time_str.split(":"))
        occupied = [time_str, f"{h + (m + 30) // 60:02d}:{(m + 30) % 60:02d}"]
        booking_id = str(uuid.uuid4())
        db.consultations.insert_one({
            "id": booking_id,
            "name": "Test Booker",
            "email": f"test-booking-{booking_id[:8]}@x.io",
            "status": "pending_confirmation",
            "package": "Strategy", "package_id": "strategy", "minutes": 60,
            "amount": 299.0,
            "slot_date": date_str, "slot_time": time_str,
            "occupied": occupied, "source": "booking-form",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        try:
            after = requests.get(f"{API}/consultation/availability", timeout=15).json()
            by_date2 = {d["date"]: set(d["slots"]) for d in after["days"]}
            for occ in occupied:
                assert occ not in by_date2.get(date_str, set()), f"{occ} still available after booking"
        finally:
            db.consultations.delete_one({"id": booking_id})

    def test_90min_booking_blocks_three_slots(self):
        date_str, time_str = _pick_future_slot()
        before = requests.get(f"{API}/consultation/availability", timeout=15).json()
        by_date = {d["date"]: set(d["slots"]) for d in before["days"]}
        # find a slot with 2 following free
        h, m = map(int, time_str.split(":"))
        slots_needed = []
        cur_h, cur_m = h, m
        for _ in range(3):
            slots_needed.append(f"{cur_h:02d}:{cur_m:02d}")
            cur_m += 30
            if cur_m == 60:
                cur_m = 0
                cur_h += 1
        if not all(s in by_date.get(date_str, set()) for s in slots_needed):
            pytest.skip("no 3 contiguous slots available")
        booking_id = str(uuid.uuid4())
        db.consultations.insert_one({
            "id": booking_id, "name": "Deep",
            "email": f"test-booking-{booking_id[:8]}@x.io",
            "status": "pending_confirmation",
            "package": "Deep-Dive", "package_id": "deepdive", "minutes": 90,
            "slot_date": date_str, "slot_time": time_str,
            "occupied": slots_needed, "source": "booking-form",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        try:
            after = requests.get(f"{API}/consultation/availability", timeout=15).json()
            by_date2 = {d["date"]: set(d["slots"]) for d in after["days"]}
            for s in slots_needed:
                assert s not in by_date2.get(date_str, set())
        finally:
            db.consultations.delete_one({"id": booking_id})


# ---------------- Admin auth ----------------
class TestAdminAuth:
    def test_availability_requires_auth(self):
        r = requests.get(f"{API}/admin/availability", timeout=15)
        assert r.status_code == 401

    def test_bookings_requires_auth(self):
        r = requests.get(f"{API}/admin/bookings", timeout=15)
        assert r.status_code == 401


# ---------------- Admin availability management ----------------
class TestAdminAvailability:
    def test_get_admin_availability(self, admin_headers):
        r = requests.get(f"{API}/admin/availability", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        d = r.json()
        assert "week_start" in d and "published_week_start" in d
        assert "is_published" in d and "slot_times" in d
        assert "days" in d and len(d["days"]) == 5  # Mon-Fri
        for day in d["days"]:
            for s in day["slots"]:
                assert s["state"] in {"available", "blocked", "booked"}
                assert "time" in s
        assert d["slot_times"][0] == "09:30"
        assert d["slot_times"][-1] == "18:30"

    def test_toggle_blocks_slot_publicly(self, admin_headers, orig_availability):
        date_str, time_str = _pick_future_slot()
        # block
        r = requests.post(f"{API}/admin/availability/toggle",
                          headers=admin_headers,
                          json={"date": date_str, "time": time_str, "blocked": True}, timeout=15)
        assert r.status_code == 200
        pub = requests.get(f"{API}/consultation/availability", timeout=15).json()
        by_date = {d["date"]: set(d["slots"]) for d in pub["days"]}
        assert time_str not in by_date.get(date_str, set())
        # unblock
        r2 = requests.post(f"{API}/admin/availability/toggle",
                           headers=admin_headers,
                           json={"date": date_str, "time": time_str, "blocked": False}, timeout=15)
        assert r2.status_code == 200
        pub2 = requests.get(f"{API}/consultation/availability", timeout=15).json()
        by_date2 = {d["date"]: set(d["slots"]) for d in pub2["days"]}
        assert time_str in by_date2.get(date_str, set())

    def test_block_day(self, admin_headers, orig_availability):
        date_str, _ = _pick_future_slot()
        r = requests.post(f"{API}/admin/availability/block-day",
                          headers=admin_headers,
                          json={"date": date_str, "blocked": True}, timeout=15)
        assert r.status_code == 200
        pub = requests.get(f"{API}/consultation/availability", timeout=15).json()
        by_date = {d["date"]: d["slots"] for d in pub["days"]}
        assert date_str not in by_date or by_date[date_str] == []
        # restore
        requests.post(f"{API}/admin/availability/block-day",
                      headers=admin_headers,
                      json={"date": date_str, "blocked": False}, timeout=15)

    def test_publish_week(self, admin_headers, orig_availability):
        # publish next week
        today = datetime.now(timezone.utc).date()
        next_mon = _monday(today) + timedelta(days=7)
        r = requests.post(f"{API}/admin/availability/publish",
                          headers=admin_headers,
                          json={"week_start": next_mon.isoformat()}, timeout=15)
        assert r.status_code == 200
        assert r.json()["published_week_start"] == next_mon.isoformat()
        pub = requests.get(f"{API}/consultation/availability", timeout=15).json()
        assert pub["week_start"] == next_mon.isoformat()


# ---------------- Admin bookings queue ----------------
class TestAdminBookings:
    def test_lifecycle_confirm_reschedule_decline(self, admin_headers):
        date_str, time_str = _pick_future_slot()
        bid = str(uuid.uuid4())
        db.consultations.insert_one({
            "id": bid, "name": "Test", "email": f"test-booking-{bid[:8]}@x.io",
            "status": "pending_confirmation", "package": "Strategy",
            "package_id": "strategy", "minutes": 60, "amount": 299.0,
            "slot_date": date_str, "slot_time": time_str,
            "occupied": [time_str], "source": "booking-form",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        try:
            # list
            r = requests.get(f"{API}/admin/bookings", headers=admin_headers, timeout=15)
            assert r.status_code == 200
            assert any(b["id"] == bid for b in r.json())

            # confirm
            r = requests.post(f"{API}/admin/bookings/{bid}/confirm",
                              headers=admin_headers, json={}, timeout=15)
            assert r.status_code == 200
            doc = db.consultations.find_one({"id": bid})
            assert doc["status"] == "confirmed"

            # reschedule
            # pick a different future slot
            _, new_time = _pick_future_slot()
            if new_time == time_str:
                new_time = "17:00"
            r = requests.post(f"{API}/admin/bookings/{bid}/reschedule",
                              headers=admin_headers,
                              json={"date": date_str, "time": new_time}, timeout=15)
            assert r.status_code == 200, r.text
            doc = db.consultations.find_one({"id": bid})
            assert doc["slot_time"] == new_time
            assert doc["status"] == "confirmed"

            # decline (should free slot)
            r = requests.post(f"{API}/admin/bookings/{bid}/decline",
                              headers=admin_headers,
                              json={"reason": "test"}, timeout=15)
            assert r.status_code == 200
            doc = db.consultations.find_one({"id": bid})
            assert doc["status"] == "declined"

            pub = requests.get(f"{API}/consultation/availability", timeout=15).json()
            by_date = {d["date"]: set(d["slots"]) for d in pub["days"]}
            # declined booking's slot should be free again
            assert new_time in by_date.get(date_str, set()) or date_str not in by_date
        finally:
            db.consultations.delete_one({"id": bid})

    def test_reschedule_invalid_time(self, admin_headers):
        bid = str(uuid.uuid4())
        db.consultations.insert_one({
            "id": bid, "name": "X", "email": f"test-booking-{bid[:8]}@x.io",
            "status": "pending_confirmation", "package_id": "strategy",
            "minutes": 60, "slot_date": "2099-01-05", "slot_time": "10:00",
            "occupied": ["10:00"], "source": "booking-form",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        try:
            r = requests.post(f"{API}/admin/bookings/{bid}/reschedule",
                              headers=admin_headers,
                              json={"date": "2099-01-05", "time": "20:00"}, timeout=15)
            assert r.status_code == 400
        finally:
            db.consultations.delete_one({"id": bid})
