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
