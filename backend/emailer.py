"""Email + .ics calendar invite via Gmail SMTP. Graceful no-op if not configured."""
import os
import ssl
import smtplib
import logging
from datetime import datetime, timezone
from email.message import EmailMessage
from email.policy import SMTP

log = logging.getLogger(__name__)


def _ics_escape(v: str) -> str:
    return v.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def _utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_ics(booking_id: str, summary: str, start: datetime, end: datetime, client_name: str, client_email: str, organizer: str) -> bytes:
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Sudarshan Karweer//Consultation//EN",
        "CALSCALE:GREGORIAN", "METHOD:REQUEST", "BEGIN:VEVENT",
        f"UID:{booking_id}@sudarshankarweer", f"DTSTAMP:{_utc(datetime.now(timezone.utc))}",
        f"DTSTART:{_utc(start)}", f"DTEND:{_utc(end)}",
        f"SUMMARY:{_ics_escape(summary)}",
        f"DESCRIPTION:{_ics_escape('Premium 1:1 consultation with Sudarshan Karweer for ' + client_name)}",
        "LOCATION:Online (video link to follow)",
        f"ORGANIZER:mailto:{organizer}",
        f"ATTENDEE;CN={_ics_escape(client_name)}:mailto:{client_email}",
        "END:VEVENT", "END:VCALENDAR", "",
    ]
    return "\r\n".join(lines).encode("utf-8")


def send_booking_email(booking_id: str, client_name: str, client_email: str, service: str,
                       start: datetime, end: datetime) -> str:
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    admin = os.environ.get("BOOKING_ADMIN_EMAIL", user or "")
    if not user or not pwd:
        log.warning("Email skipped for booking %s: Gmail app password not configured", booking_id)
        return "skipped"

    msg = EmailMessage(policy=SMTP)
    msg["Subject"] = f"Confirmed: {service} with Sudarshan Karweer"
    msg["From"] = user
    msg["To"] = client_email
    msg["Cc"] = admin
    msg.set_content(
        f"Hello {client_name},\n\n"
        f"Your {service} is confirmed.\n"
        f"When: {start.strftime('%A, %d %b %Y at %H:%M UTC')}\n\n"
        "A calendar invite is attached. A video link will follow before the session.\n\n"
        "— Team Sudarshan Karweer\n"
    )
    msg.add_attachment(build_ics(booking_id, service, start, end, client_name, client_email, user),
                       maintype="text", subtype="calendar", filename="consultation.ics",
                       params={"method": "REQUEST", "charset": "utf-8"})
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
            s.ehlo(); s.starttls(context=ctx); s.ehlo()
            s.login(user, pwd); s.send_message(msg)
        log.info("Booking email sent for %s", booking_id)
        return "sent"
    except Exception:
        log.exception("Booking email failed for %s", booking_id)
        return "failed"


def send_digest_email(client_email: str, client_name: str, videos: list) -> str:
    """Weekly personalised top-5 videos digest."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd:
        return "skipped"
    rows = ""
    for v in videos[:5]:
        url = f"https://www.youtube.com/watch?v={v['video_id']}"
        rows += (
            f'<tr><td style="padding:10px 0;">'
            f'<a href="{url}" style="color:#0A0A0A;text-decoration:none;font-weight:600;font-size:15px;">{v.get("title","")}</a>'
            f'<div style="color:#6b7280;font-size:12px;margin-top:4px;">Source: {v.get("source","")}</div>'
            f'</td></tr>'
        )
    html = (
        f'<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;">'
        f'<div style="background:#0A0A0A;padding:20px 24px;border-radius:12px 12px 0 0;">'
        f'<span style="color:#fff;font-size:22px;font-weight:700;">S<span style="color:#C6F135;">K.</span></span>'
        f'<span style="color:#9ca3af;font-size:12px;margin-left:10px;">Your weekly Learning Hub</span></div>'
        f'<div style="border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;padding:24px;">'
        f'<p style="font-size:15px;color:#111;">Hi {client_name},</p>'
        f'<p style="font-size:14px;color:#374151;">Your 5 hand-picked videos for the week, tuned to your interests:</p>'
        f'<table style="width:100%;border-collapse:collapse;">{rows}</table>'
        f'<a href="https://www.sudarshankarweer.com/learning" style="display:inline-block;margin-top:18px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Open Learning Hub</a>'
        f'<p style="font-size:11px;color:#9ca3af;margin-top:20px;">You receive this because you have an account with Sudarshan Karweer. Manage preferences in your dashboard.</p>'
        f'</div></div>'
    )
    msg = EmailMessage()
    msg["Subject"] = "Your weekly watchlist — 5 fresh picks"
    msg["From"] = user
    msg["To"] = client_email
    msg.set_content("Your weekly personalised videos. View them at https://www.sudarshankarweer.com/learning")
    msg.add_alternative(html, subtype="html")
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
            s.ehlo(); s.starttls(context=ctx); s.ehlo()
            s.login(user, pwd); s.send_message(msg)
        return "sent"
    except Exception:
        log.exception("Digest email failed for %s", client_email)
        return "failed"
