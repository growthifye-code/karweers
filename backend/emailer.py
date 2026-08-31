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


def build_ics(booking_id: str, summary: str, start: datetime, end: datetime, client_name: str, client_email: str, organizer: str, meeting_link: str = "") -> bytes:
    location = meeting_link if meeting_link else "Online (video link to follow)"
    lines = [
        "BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Sudarshan Karweer//Consultation//EN",
        "CALSCALE:GREGORIAN", "METHOD:REQUEST", "BEGIN:VEVENT",
        f"UID:{booking_id}@sudarshankarweer", f"DTSTAMP:{_utc(datetime.now(timezone.utc))}",
        f"DTSTART:{_utc(start)}", f"DTEND:{_utc(end)}",
        f"SUMMARY:{_ics_escape(summary)}",
        f"DESCRIPTION:{_ics_escape('Premium 1:1 consultation with Sudarshan Karweer for ' + client_name + (chr(10) + 'Join: ' + meeting_link if meeting_link else ''))}",
        f"LOCATION:{_ics_escape(location)}",
        f"ORGANIZER:mailto:{organizer}",
        f"ATTENDEE;CN={_ics_escape(client_name)}:mailto:{client_email}",
    ]
    if meeting_link:
        lines.append(f"URL:{_ics_escape(meeting_link)}")
    lines += ["END:VEVENT", "END:VCALENDAR", ""]
    return "\r\n".join(lines).encode("utf-8")


def send_booking_email(booking_id: str, client_name: str, client_email: str, service: str,
                       start: datetime, end: datetime, meeting_link: str = "", manage_url: str = "") -> str:
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    admin = os.environ.get("BOOKING_ADMIN_EMAIL", user or "")
    if not user or not pwd:
        log.warning("Email skipped for booking %s: Gmail app password not configured", booking_id)
        return "skipped"

    join_line = f"Join here: {meeting_link}\n" if meeting_link else "A video link will follow before the session.\n"
    manage_line = f"\nNeed to change it? Cancel or request a reschedule here: {manage_url}\n" if manage_url else ""
    msg = EmailMessage(policy=SMTP)
    msg["Subject"] = f"Confirmed: {service} with Sudarshan Karweer"
    msg["From"] = user
    msg["To"] = client_email
    msg["Cc"] = admin
    msg.set_content(
        f"Hello {client_name},\n\n"
        f"Your {service} is confirmed.\n"
        f"When: {start.strftime('%A, %d %b %Y at %H:%M UTC')}\n"
        f"{join_line}"
        f"{manage_line}\n"
        "A calendar invite is attached.\n\n"
        "— Team Sudarshan Karweer\n"
    )
    msg.add_attachment(build_ics(booking_id, service, start, end, client_name, client_email, user, meeting_link),
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


def send_ticket_alert_email(to_email: str, ticket: dict) -> str:
    """Alert the advisor the moment a client raises a support ticket."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    html = (
        f'<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;">'
        f'<div style="background:#0A0A0A;padding:18px 24px;border-radius:12px 12px 0 0;">'
        f'<span style="color:#fff;font-size:20px;font-weight:700;">S<span style="color:#C6F135;">K.</span></span>'
        f'<span style="color:#9ca3af;font-size:12px;margin-left:10px;">New support ticket</span></div>'
        f'<div style="border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;padding:24px;">'
        f'<p style="font-size:15px;color:#111;font-weight:600;">{ticket.get("subject","")}</p>'
        f'<p style="font-size:13px;color:#6b7280;">{ticket.get("ticket_code","")} · {ticket.get("name","")} '
        f'({ticket.get("client_code") or ticket.get("email","")}) · {ticket.get("category","")} · '
        f'priority {ticket.get("priority","")}</p>'
        f'<p style="font-size:14px;color:#374151;margin-top:14px;white-space:pre-wrap;">{ticket.get("message","")}</p>'
        f'<a href="https://www.sudarshankarweer.com/admin" style="display:inline-block;margin-top:18px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Open Service Desk</a>'
        f'</div></div>'
    )
    msg = EmailMessage()
    msg["Subject"] = f"New ticket: {ticket.get('subject','')} [{ticket.get('ticket_code','')}]"
    msg["From"] = user
    msg["To"] = to_email
    msg["Reply-To"] = ticket.get("email", user)
    msg.set_content(f"New support ticket from {ticket.get('name','')}: {ticket.get('subject','')}\n\n{ticket.get('message','')}")
    msg.add_alternative(html, subtype="html")
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
            s.ehlo(); s.starttls(context=ctx); s.ehlo()
            s.login(user, pwd); s.send_message(msg)
        return "sent"
    except Exception:
        log.exception("Ticket alert email failed")
        return "failed"


def send_report_email(to_email: str, csv_text: str) -> str:
    """Monthly lead-source + conversion analytics, with CSV attached."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    month = datetime.now(timezone.utc).strftime("%B %Y")
    html = (
        f'<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;">'
        f'<div style="background:#0A0A0A;padding:18px 24px;border-radius:12px 12px 0 0;">'
        f'<span style="color:#fff;font-size:20px;font-weight:700;">S<span style="color:#C6F135;">K.</span></span>'
        f'<span style="color:#9ca3af;font-size:12px;margin-left:10px;">Monthly analytics report</span></div>'
        f'<div style="border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;padding:24px;">'
        f'<p style="font-size:15px;color:#111;">Your lead-source &amp; conversion report for {month} is attached as a CSV.</p>'
        f'<p style="font-size:13px;color:#6b7280;">It breaks down total leads, paid consultations, conversion rate and revenue by channel.</p>'
        f'<a href="https://www.sudarshankarweer.com/admin" style="display:inline-block;margin-top:14px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Open dashboard</a>'
        f'</div></div>'
    )
    msg = EmailMessage()
    msg["Subject"] = f"Lead & revenue analytics — {month}"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Your monthly lead-source & conversion analytics for {month} is attached.")
    msg.add_alternative(html, subtype="html")
    msg.add_attachment(csv_text.encode("utf-8"), maintype="text", subtype="csv",
                       filename=f"analytics-{datetime.now(timezone.utc).strftime('%Y-%m')}.csv")
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
            s.ehlo(); s.starttls(context=ctx); s.ehlo()
            s.login(user, pwd); s.send_message(msg)
        return "sent"
    except Exception:
        log.exception("Report email failed")
        return "failed"


def send_security_alert_email(to_email: str, alert: dict) -> str:
    """Alert the advisor the moment an attack is detected and auto-mitigated."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    sev = (alert.get("severity") or "high").upper()
    html = (
        f'<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;">'
        f'<div style="background:#0A0A0A;padding:18px 24px;border-radius:12px 12px 0 0;">'
        f'<span style="color:#fff;font-size:20px;font-weight:700;">S<span style="color:#C6F135;">K.</span></span>'
        f'<span style="color:#ef4444;font-size:12px;margin-left:10px;font-weight:700;">SECURITY ALERT · {sev}</span></div>'
        f'<div style="border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;padding:24px;">'
        f'<p style="font-size:15px;color:#111;font-weight:600;">{alert.get("reason","Suspicious activity")}</p>'
        f'<p style="font-size:13px;color:#6b7280;">IP <strong>{alert.get("ip","")}</strong>'
        f'{(" · " + alert.get("email","")) if alert.get("email") else ""} · {alert.get("type","")}</p>'
        f'<p style="font-size:14px;color:#374151;margin-top:12px;">{alert.get("detail","")}</p>'
        f'<p style="font-size:13px;color:#059669;margin-top:12px;font-weight:600;">Automatic action taken: this IP has been blocked.</p>'
        f'<a href="https://www.sudarshankarweer.com/admin" style="display:inline-block;margin-top:16px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Review in dashboard</a>'
        f'</div></div>'
    )
    msg = EmailMessage()
    msg["Subject"] = f"[Security] {alert.get('reason','Attack blocked')} — {alert.get('ip','')}"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Security alert ({sev}): {alert.get('reason','')} from IP {alert.get('ip','')}. "
                    f"{alert.get('detail','')}. This IP has been automatically blocked.")
    msg.add_alternative(html, subtype="html")
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
            s.ehlo(); s.starttls(context=ctx); s.ehlo()
            s.login(user, pwd); s.send_message(msg)
        return "sent"
    except Exception:
        log.exception("Security alert email failed")
        return "failed"


def _shell(label: str, inner: str) -> str:
    return (
        f'<div style="font-family:Arial,sans-serif;max-width:560px;margin:auto;">'
        f'<div style="background:#0A0A0A;padding:18px 24px;border-radius:12px 12px 0 0;">'
        f'<span style="color:#fff;font-size:20px;font-weight:700;">S<span style="color:#C6F135;">K.</span></span>'
        f'<span style="color:#9ca3af;font-size:12px;margin-left:10px;">{label}</span></div>'
        f'<div style="border:1px solid #e5e7eb;border-top:none;border-radius:0 0 12px 12px;padding:24px;">{inner}</div></div>'
    )


def _smtp_send(msg) -> str:
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=20) as s:
            s.ehlo(); s.starttls(context=ctx); s.ehlo()
            s.login(msg["From"], os.environ.get("GMAIL_APP_PASSWORD")); s.send_message(msg)
        return "sent"
    except Exception:
        log.exception("SMTP send failed")
        return "failed"


def send_weekly_agenda_email(to_email: str, sessions: list) -> str:
    """Monday-morning digest to the advisor listing the week's confirmed sessions."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    if sessions:
        rows = ""
        for s in sessions:
            join = f'<a href="{s.get("meeting_link")}" style="color:#059669;font-weight:600;">Join</a>' if s.get("meeting_link") else '<span style="color:#9ca3af;">—</span>'
            rows += (f'<tr>'
                     f'<td style="padding:8px 6px;border-bottom:1px solid #eee;font-size:13px;color:#059669;font-weight:600;white-space:nowrap;">{s.get("slot_date","")}<br>{s.get("slot_time","")} IST</td>'
                     f'<td style="padding:8px 6px;border-bottom:1px solid #eee;font-size:13px;color:#111;">{s.get("name","")}<div style="color:#6b7280;font-size:12px;">{s.get("package","")}</div></td>'
                     f'<td style="padding:8px 6px;border-bottom:1px solid #eee;font-size:13px;text-align:right;">{join}</td>'
                     f'</tr>')
        inner = (f'<p style="font-size:15px;color:#111;font-weight:600;">Your week ahead — {len(sessions)} confirmed session(s)</p>'
                 f'<table style="width:100%;border-collapse:collapse;margin-top:10px;">{rows}</table>'
                 f'<a href="https://www.sudarshankarweer.com/admin" style="display:inline-block;margin-top:16px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Open dashboard</a>')
    else:
        inner = '<p style="font-size:15px;color:#111;font-weight:600;">Your week ahead</p><p style="font-size:14px;color:#374151;margin-top:6px;">No confirmed sessions scheduled for the coming week yet.</p>'
    msg = EmailMessage()
    msg["Subject"] = f"Week ahead: {len(sessions)} confirmed session(s)"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Your week ahead: {len(sessions)} confirmed session(s). Open your dashboard for details.")
    msg.add_alternative(_shell("Weekly agenda", inner), subtype="html")
    return _smtp_send(msg)


def send_new_booking_alert_email(to_email: str, booking: dict) -> str:
    """Alert the advisor the moment a new session booking lands (pending confirmation)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    inner = (
        f'<p style="font-size:15px;color:#111;font-weight:600;">New booking — action needed</p>'
        f'<p style="font-size:14px;color:#111;margin-top:6px;">{booking.get("package","Consultation")} · '
        f'<span style="color:#059669;font-weight:600;">{booking.get("slot_date","")} at {booking.get("slot_time","")} IST</span></p>'
        f'<p style="font-size:13px;color:#6b7280;margin-top:10px;">{booking.get("name","")} · {booking.get("email","")}'
        f'{(" · " + booking.get("phone")) if booking.get("phone") else ""}</p>'
        f'<p style="font-size:13px;color:#6b7280;">Focus: {booking.get("area","")}</p>'
        f'{("<p style=font-size:14px;color:#374151;margin-top:12px;white-space:pre-wrap;>" + booking.get("message","") + "</p>") if booking.get("message") else ""}'
        f'<p style="font-size:13px;color:#b45309;margin-top:12px;font-weight:600;">Status: pending confirmation — please confirm the slot.</p>'
        f'<a href="https://www.sudarshankarweer.com/admin" style="display:inline-block;margin-top:16px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Review &amp; confirm</a>'
    )
    msg = EmailMessage()
    msg["Subject"] = f"New booking (pending): {booking.get('package','')} — {booking.get('slot_date','')} {booking.get('slot_time','')}"
    msg["From"] = user
    msg["To"] = to_email
    if booking.get("email"):
        msg["Reply-To"] = booking["email"]
    msg.set_content(f"New booking from {booking.get('name','')} for {booking.get('package','')} on "
                    f"{booking.get('slot_date','')} at {booking.get('slot_time','')} IST. Pending confirmation.")
    msg.add_alternative(_shell("New session booking", inner), subtype="html")
    return _smtp_send(msg)


def send_session_reminder_email(to_email: str, client_name: str, package: str, slot_date: str, slot_time: str, when_label: str = "", meeting_link: str = "") -> str:
    """Remind the client before their confirmed session (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    when = when_label or "soon"
    join = (f'<a href="{meeting_link}" style="display:inline-block;margin-top:14px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Join the session</a>'
            if meeting_link else '<p style="font-size:13px;color:#6b7280;margin-top:12px;">A video link will follow shortly. If you need to reschedule, just reply to this email.</p>')
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {client_name},</p>'
        f'<p style="font-size:14px;color:#374151;">A reminder that your session with Sudarshan Karweer is {when}.</p>'
        f'<p style="font-size:15px;color:#111;margin-top:10px;font-weight:600;">{package}</p>'
        f'<p style="font-size:14px;color:#059669;font-weight:600;">{slot_date} at {slot_time} IST</p>'
        f'{join}'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
    )
    msg = EmailMessage()
    msg["Subject"] = f"Reminder: your {package} is {when} ({slot_time} IST)"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Reminder: your {package} with Sudarshan Karweer is {when} — {slot_date} at {slot_time} IST."
                    + (f" Join: {meeting_link}" if meeting_link else ""))
    msg.add_alternative(_shell("Session reminder", inner), subtype="html")
    return _smtp_send(msg)
