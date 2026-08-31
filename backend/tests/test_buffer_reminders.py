import asyncio


async def main():
    import server as s
    db = s.db
    d = "2026-09-02"  # a Wednesday within default week
    await db.consultations.delete_many({"email": "buftest@example.com"})

    # Insert a 60-min booking at 11:00 (occupies 11:00, 11:30)
    await db.consultations.insert_one({
        "id": "buf-1", "email": "buftest@example.com", "name": "Buf",
        "status": "confirmed", "slot_date": d, "slot_time": "11:00", "minutes": 60,
        "occupied": ["11:00", "11:30"], "source": "booking-form"})

    # No buffer: only 11:00, 11:30 blocked
    b0 = await s._booked_slots_for([d], 0)
    assert b0[d] == {"11:00", "11:30"}, b0[d]
    print("PASS: no-buffer blocks exactly the session slots", sorted(b0[d]))

    # 30-min buffer: extends to 10:30 (before) and 12:00 (after)
    b30 = await s._booked_slots_for([d], 30)
    assert b30[d] == {"10:30", "11:00", "11:30", "12:00"}, sorted(b30[d])
    print("PASS: 30-min buffer blocks 10:30..12:00", sorted(b30[d]))

    # 60-min buffer: 10:00..12:30
    b60 = await s._booked_slots_for([d], 60)
    assert b60[d] == {"10:00", "10:30", "11:00", "11:30", "12:00", "12:30"}, sorted(b60[d])
    print("PASS: 60-min buffer blocks 10:00..12:30", sorted(b60[d]))

    # New-booking alert is inert (no SMTP)
    r = s.send_new_booking_alert_email("admin@example.com", {"name": "X", "package": "Discovery Call", "slot_date": d, "slot_time": "11:00"})
    assert r == "skipped", r
    print("PASS: new-booking alert inert -> skipped")

    # Reminder window: booking ~24h out (IST) is selected; far-out one is not
    from datetime import datetime, timezone, timedelta
    soon_ist = (datetime.now(timezone.utc).astimezone(s.IST_TZ) + timedelta(hours=24))
    far_ist = (datetime.now(timezone.utc).astimezone(s.IST_TZ) + timedelta(days=5))
    await db.consultations.delete_many({"email": {"$in": ["soon@example.com", "far@example.com"]}})
    await db.consultations.insert_one({"id": "rem-soon", "email": "soon@example.com", "name": "Soon",
        "status": "confirmed", "package": "Strategy", "slot_date": soon_ist.strftime("%Y-%m-%d"),
        "slot_time": soon_ist.strftime("%H:%M"), "minutes": 60, "source": "booking-form"})
    await db.consultations.insert_one({"id": "rem-far", "email": "far@example.com", "name": "Far",
        "status": "confirmed", "package": "Strategy", "slot_date": far_ist.strftime("%Y-%m-%d"),
        "slot_time": "11:00", "minutes": 60, "source": "booking-form"})
    await s._send_session_reminders()
    soon = await db.consultations.find_one({"id": "rem-soon"})
    far = await db.consultations.find_one({"id": "rem-far"})
    assert 24 in (soon.get("reminders_sent") or []), f"soon should be reminded: {soon.get('reminders_sent')}"
    assert 24 not in (far.get("reminders_sent") or []), "far should NOT be reminded"
    print("PASS: reminder selects ~24h-out booking only (reminders_sent=%s)" % soon.get("reminders_sent"))

    # cleanup
    await db.consultations.delete_many({"id": {"$in": ["buf-1", "rem-soon", "rem-far"]}})
    print("ALL BUFFER/ALERT/REMINDER TESTS PASSED")


asyncio.run(main())
