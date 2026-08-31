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


def send_waitlist_opening_email(to_email: str, name: str, package: str, date_str: str, book_url: str = "") -> str:
    """Tell a waitlisted client that a slot opened up on their requested day."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    cta = (f'<a href="{book_url}" style="display:inline-block;margin-top:14px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Book your slot</a>'
           if book_url else "")
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {name},</p>'
        f'<p style="font-size:14px;color:#374151;">Good news — a slot has just opened up on <strong>{date_str}</strong>'
        f'{(" for " + package) if package else ""}. These fill quickly, so book soon to secure it.</p>'
        f'{cta}'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
    )
    msg = EmailMessage()
    msg["Subject"] = f"A slot opened up on {date_str}"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"A slot opened up on {date_str}{(' for ' + package) if package else ''}. Book soon: {book_url}")
    msg.add_alternative(_shell("Waitlist — slot available", inner), subtype="html")
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



def send_consent_receipt_email(to_email: str, name: str, action: str, version: str,
                               at: str = "", admin_bcc: str = "") -> str:
    """Send the user a copy of the Terms & Privacy agreement they just accepted (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    action_label = {"register": "creating your account", "login": "signing in",
                    "google": "signing in with Google"}.get(action, "signing in")
    site = "https://www.sudarshankarweer.com"
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {name or "there"},</p>'
        f'<p style="font-size:14px;color:#374151;">Thanks for {action_label}. This is your record that you read and agreed to '
        f'our Terms &amp; Conditions and Privacy Policy.</p>'
        f'<table style="width:100%;border-collapse:collapse;margin-top:14px;font-size:13px;color:#374151;">'
        f'<tr><td style="padding:6px 0;color:#6b7280;">Agreed on</td><td style="padding:6px 0;text-align:right;font-weight:600;color:#111;">{at or "just now"}</td></tr>'
        f'<tr><td style="padding:6px 0;color:#6b7280;">Policy version</td><td style="padding:6px 0;text-align:right;font-weight:600;color:#111;">{version}</td></tr>'
        f'<tr><td style="padding:6px 0;color:#6b7280;">Method</td><td style="padding:6px 0;text-align:right;font-weight:600;color:#111;text-transform:capitalize;">{action}</td></tr>'
        f'</table>'
        f'<p style="font-size:14px;color:#374151;margin-top:16px;">Read them anytime:</p>'
        f'<p style="font-size:14px;margin-top:4px;">'
        f'<a href="{site}/terms" style="color:#059669;font-weight:600;">Terms &amp; Conditions</a> &nbsp;·&nbsp; '
        f'<a href="{site}/privacy" style="color:#059669;font-weight:600;">Privacy Policy</a></p>'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
    )
    msg = EmailMessage()
    msg["Subject"] = "Your agreement to our Terms & Privacy Policy"
    msg["From"] = user
    msg["To"] = to_email
    if admin_bcc:
        msg["Bcc"] = admin_bcc
    msg.set_content(f"Hi {name or 'there'}, this confirms you agreed to our Terms & Conditions and Privacy Policy "
                    f"(version {version}) on {at or 'just now'} via {action}. "
                    f"Read them: {site}/terms and {site}/privacy. — Team Sudarshan Karweer")
    msg.add_alternative(_shell("Consent receipt", inner), subtype="html")
    return _smtp_send(msg)


def render_signals_digest_html(name: str, items: list, site: str = "https://www.sudarshankarweer.com", unsubscribe_url: str = "") -> str:
    cards = ""
    for it in items:
        cards += (
            f'<div style="border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:12px;">'
            f'<span style="display:inline-block;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#059669;">{it.get("tag","")}</span>'
            f'<p style="font-size:15px;font-weight:700;color:#111;margin:8px 0 4px;">{it.get("title","")}</p>'
            f'<p style="font-size:13px;color:#374151;margin:0;">{it.get("take","")}</p></div>'
        )
    unsub = (f'<p style="font-size:12px;color:#9ca3af;margin-top:20px;text-align:center;">'
             f'You receive this because you subscribed to Sudarshan Karweer updates. '
             f'<a href="{unsubscribe_url}" style="color:#9ca3af;text-decoration:underline;">Unsubscribe</a> anytime.</p>'
             if unsubscribe_url else "")
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {name or "there"},</p>'
        f'<p style="font-size:14px;color:#374151;">Here are this week\'s sharpest Market Signals on the energy transition, capital and strategy.</p>'
        f'<div style="margin-top:14px;">{cards}</div>'
        f'<a href="{site}/signals" style="display:inline-block;margin-top:8px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Browse the full archive</a>'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
        f'{unsub}'
    )
    return _shell("Weekly Market Signals", inner)


def send_signals_digest_email(to_email: str, name: str, items: list, site: str = "https://www.sudarshankarweer.com", unsubscribe_url: str = "") -> str:
    """Weekly round-up of the best Market Signals to a subscriber (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email or not items:
        return "skipped"
    msg = EmailMessage()
    msg["Subject"] = "This week in Market Signals"
    msg["From"] = user
    msg["To"] = to_email
    if unsubscribe_url:
        msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.set_content("This week's Market Signals: " + " | ".join(i.get("title", "") for i in items)
                    + f"  Read more: {site}/signals"
                    + (f"  Unsubscribe: {unsubscribe_url}" if unsubscribe_url else ""))
    msg.add_alternative(render_signals_digest_html(name, items, site, unsubscribe_url), subtype="html")
    return _smtp_send(msg)


def send_test_email(to_email: str) -> str:
    """Send a simple deliverability test email (used to check SPF/DKIM/DMARC via a mail tester)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    inner = (
        '<p style="font-size:15px;color:#111;">This is a deliverability test from the Sudarshan Karweer platform.</p>'
        '<p style="font-size:14px;color:#374151;">If you can read this, outbound email is working. '
        'Run it through a tool like mail-tester.com to confirm SPF, DKIM and DMARC all pass.</p>'
        '<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
    )
    msg = EmailMessage()
    msg["Subject"] = "Deliverability test — Sudarshan Karweer"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content("Deliverability test from the Sudarshan Karweer platform. If you can read this, outbound email works.")
    msg.add_alternative(_shell("Deliverability test", inner), subtype="html")
    return _smtp_send(msg)



def _inr(v) -> str:
    try:
        return "\u20b9" + f"{float(v):,.2f}"
    except Exception:
        return "\u20b9" + str(v)


def send_payment_receipt_email(to_email: str, booking: dict) -> str:
    """Receipt to the client after a successful consultation payment (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    rows = (
        f'<tr><td style="padding:6px 0;color:#6b7280;">Session</td><td style="padding:6px 0;text-align:right;font-weight:600;color:#111;">{booking.get("package","")}</td></tr>'
        f'<tr><td style="padding:6px 0;color:#6b7280;">When</td><td style="padding:6px 0;text-align:right;font-weight:600;color:#111;">{booking.get("slot_date","")} {booking.get("slot_time","")} IST</td></tr>'
        f'<tr><td style="padding:6px 0;color:#6b7280;">Base fee</td><td style="padding:6px 0;text-align:right;color:#111;">{_inr(booking.get("amount",0))}</td></tr>'
        f'<tr><td style="padding:6px 0;color:#6b7280;">GST ({booking.get("gst_pct",18)}%)</td><td style="padding:6px 0;text-align:right;color:#111;">{_inr(booking.get("gst_amount",0))}</td></tr>'
        f'<tr><td style="padding:10px 0 0;color:#111;font-weight:700;border-top:1px solid #e5e7eb;">Total paid</td><td style="padding:10px 0 0;text-align:right;font-weight:700;color:#111;border-top:1px solid #e5e7eb;">{_inr(booking.get("amount_total",0))}</td></tr>'
        f'<tr><td style="padding:6px 0;color:#6b7280;">Payment ID</td><td style="padding:6px 0;text-align:right;color:#111;">{booking.get("razorpay_payment_id","")}</td></tr>'
    )
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {booking.get("name","there")},</p>'
        f'<p style="font-size:14px;color:#374151;">Thank you — your payment was received. Your slot is reserved and pending confirmation; '
        f'we\'ll confirm your session and send a calendar invite with the meeting link shortly.</p>'
        f'<table style="width:100%;border-collapse:collapse;margin-top:14px;font-size:13px;">{rows}</table>'
        f'<p style="font-size:12px;color:#9ca3af;margin-top:16px;">If your session cannot be accommodated, this payment is refunded in full to your original payment method.</p>'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
    )
    msg = EmailMessage()
    msg["Subject"] = "Payment received — your consultation booking"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Payment received for {booking.get('package','')} on {booking.get('slot_date','')} {booking.get('slot_time','')} IST. "
                    f"Total {booking.get('amount_total','')} INR. Payment ID {booking.get('razorpay_payment_id','')}. — Team Sudarshan Karweer")
    msg.add_alternative(_shell("Payment receipt", inner), subtype="html")
    return _smtp_send(msg)


def send_refund_email(to_email: str, booking: dict, reason: str = "") -> str:
    """Notify the client that their consultation payment has been refunded (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {booking.get("name","there")},</p>'
        f'<p style="font-size:14px;color:#374151;">Your consultation ({booking.get("package","")}, {booking.get("slot_date","")} {booking.get("slot_time","")} IST) '
        f'could not be confirmed{(" — " + reason) if reason else ""}, so we\'ve refunded <strong>{_inr(booking.get("amount_total",0))}</strong> in full '
        f'to your original payment method. It typically appears within 5–7 business days.</p>'
        f'<p style="font-size:13px;color:#374151;margin-top:12px;">Payment ID: {booking.get("razorpay_payment_id","")}<br>Refund ID: {booking.get("refund_id","")}</p>'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">We\'d be glad to help you find another slot — just reply to this email.</p>'
        f'<p style="font-size:13px;color:#374151;margin-top:12px;">— Team Sudarshan Karweer</p>'
    )
    msg = EmailMessage()
    msg["Subject"] = "Your consultation payment has been refunded"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"We refunded {booking.get('amount_total','')} INR for {booking.get('package','')} to your original payment method. "
                    f"Refund ID {booking.get('refund_id','')}. — Team Sudarshan Karweer")
    msg.add_alternative(_shell("Refund processed", inner), subtype="html")
    return _smtp_send(msg)

