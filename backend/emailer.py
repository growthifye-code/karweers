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


def render_insights_newsletter_html(name: str, items: list, site: str = "https://www.sudarshankarweer.com", unsubscribe_url: str = "") -> str:
    cards = ""
    for it in items:
        img = it.get("hero_image") or ""
        img_html = (f'<img src="{img}" alt="" width="100%" style="border-radius:10px 10px 0 0;max-height:150px;object-fit:cover;display:block;" />' if img else "")
        cards += (
            f'<a href="{site}/insight/{it.get("slug","")}" style="display:block;text-decoration:none;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;margin-bottom:14px;">'
            f'{img_html}'
            f'<div style="padding:16px;">'
            f'<span style="display:inline-block;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#059669;">{it.get("category","")} · {it.get("service_title","")}</span>'
            f'<p style="font-size:16px;font-weight:700;color:#111;margin:8px 0 4px;">{it.get("title","")}</p>'
            f'<p style="font-size:13px;color:#374151;margin:0;">{it.get("dek","")}</p></div></a>'
        )
    unsub = (f'<p style="font-size:12px;color:#9ca3af;margin-top:20px;text-align:center;">'
             f'You receive this because you subscribed to Sudarshan Karweer updates. '
             f'<a href="{unsubscribe_url}" style="color:#9ca3af;text-decoration:underline;">Unsubscribe</a> anytime.</p>'
             if unsubscribe_url else "")
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {name or "there"},</p>'
        f'<p style="font-size:14px;color:#374151;">This week\'s freshest SK Insights — world-class thinking on strategy, M&amp;A, capital, energy and leadership, drawn from real deals and decades of advisory work.</p>'
        f'<div style="margin-top:14px;">{cards}</div>'
        f'<a href="{site}/insights-hub" style="display:inline-block;margin-top:8px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Explore all insights</a>'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
        f'{unsub}'
    )
    return _shell("This week in SK Insights", inner)


def send_insights_newsletter_email(to_email: str, name: str, items: list, site: str = "https://www.sudarshankarweer.com", unsubscribe_url: str = "") -> str:
    """Weekly round-up of the freshest SK Insights (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email or not items:
        return "skipped"
    msg = EmailMessage()
    msg["Subject"] = "This week in SK Insights"
    msg["From"] = user
    msg["To"] = to_email
    if unsubscribe_url:
        msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.set_content("This week's SK Insights: " + " | ".join(i.get("title", "") for i in items)
                    + f"  Read more: {site}/insights-hub"
                    + (f"  Unsubscribe: {unsubscribe_url}" if unsubscribe_url else ""))
    msg.add_alternative(render_insights_newsletter_html(name, items, site, unsubscribe_url), subtype="html")
    return _smtp_send(msg)


def render_insights_recap_html(stats: dict, site: str = "https://www.sudarshankarweer.com") -> str:
    def rows(items, metric):
        if not items:
            return '<p style="font-size:13px;color:#9ca3af;margin:4px 0;">No activity yet.</p>'
        out = ""
        for i, it in enumerate(items):
            out += (f'<div style="display:flex;justify-content:space-between;gap:10px;padding:8px 0;border-bottom:1px solid #f0f0f0;">'
                    f'<span style="font-size:13px;color:#111;">{i+1}. <a href="{site}/insight/{it.get("slug","")}" style="color:#111;text-decoration:none;">{it.get("title","")}</a></span>'
                    f'<span style="font-size:13px;font-weight:700;color:#059669;">{it.get(metric,0)}</span></div>')
        return out
    themes = ""
    for t in (stats.get("by_theme") or [])[:6]:
        themes += (f'<div style="display:flex;justify-content:space-between;padding:6px 0;">'
                   f'<span style="font-size:13px;color:#374151;">{t.get("theme","")}</span>'
                   f'<span style="font-size:13px;color:#111;">{t.get("reads",0)} reads · {t.get("shares",0)} shares</span></div>')
    themes_html = themes or '<p style="font-size:13px;color:#9ca3af;">No activity yet.</p>'
    inner = (
        f'<p style="font-size:15px;color:#111;">Good Monday, Sudarshan.</p>'
        f'<p style="font-size:14px;color:#374151;">Here\'s how your SK Insights performed last week.</p>'
        f'<div style="display:flex;gap:12px;margin:16px 0;">'
        f'<div style="flex:1;border:1px solid #e5e7eb;border-radius:12px;padding:14px;text-align:center;"><p style="font-size:24px;font-weight:800;color:#111;margin:0;">{stats.get("total_reads",0)}</p><p style="font-size:11px;color:#6b7280;margin:2px 0 0;text-transform:uppercase;letter-spacing:.05em;">Reads</p></div>'
        f'<div style="flex:1;border:1px solid #e5e7eb;border-radius:12px;padding:14px;text-align:center;"><p style="font-size:24px;font-weight:800;color:#111;margin:0;">{stats.get("total_shares",0)}</p><p style="font-size:11px;color:#6b7280;margin:2px 0 0;text-transform:uppercase;letter-spacing:.05em;">Shares</p></div>'
        f'</div>'
        f'<p style="font-size:13px;font-weight:700;color:#111;margin:16px 0 4px;">Most read</p>{rows(stats.get("top_read"), "reads")}'
        f'<p style="font-size:13px;font-weight:700;color:#111;margin:16px 0 4px;">Most shared</p>{rows(stats.get("top_shared"), "shares")}'
        f'<p style="font-size:13px;font-weight:700;color:#111;margin:16px 0 4px;">By theme</p>{themes_html}'
        f'<a href="{site}/admin" style="display:inline-block;margin-top:16px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Open the dashboard</a>'
    )
    return _shell("Your weekly SK Insights recap", inner)


def send_insights_recap_email(to_email: str, stats: dict, site: str = "https://www.sudarshankarweer.com") -> str:
    """Monday performance recap to the admin (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    msg = EmailMessage()
    msg["Subject"] = f"Weekly SK Insights recap — {stats.get('total_reads',0)} reads, {stats.get('total_shares',0)} shares"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Weekly recap: {stats.get('total_reads',0)} reads, {stats.get('total_shares',0)} shares. Open {site}/admin")
    msg.add_alternative(render_insights_recap_html(stats, site), subtype="html")
    return _smtp_send(msg)


def render_library_digest_html(name: str, books: list, site: str = "https://www.sudarshankarweer.com", unsubscribe_url: str = "") -> str:
    cards = ""
    for b in books:
        badges = []
        if b.get("has_read"):
            badges.append("Read free")
        if b.get("has_audio"):
            badges.append("Audiobook")
        badges.append("Ritual")
        chips = " · ".join(badges)
        cards += (
            f'<a href="{site}/library/{b.get("slug","")}" style="display:block;text-decoration:none;border:1px solid #e5e7eb;border-radius:12px;padding:16px;margin-bottom:12px;">'
            f'<span style="display:inline-block;font-size:11px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;color:#059669;">{b.get("theme","")}</span>'
            f'<p style="font-size:16px;font-weight:700;color:#111;margin:6px 0 2px;">{b.get("title","")}</p>'
            f'<p style="font-size:12px;color:#6b7280;margin:0 0 6px;">{b.get("author","")} · {b.get("year","")}</p>'
            f'<p style="font-size:13px;color:#374151;margin:0 0 6px;">{b.get("blurb","")}</p>'
            f'<p style="font-size:11px;color:#9ca3af;margin:0;">{chips}</p></a>'
        )
    unsub = (f'<p style="font-size:12px;color:#9ca3af;margin-top:20px;text-align:center;">'
             f'You receive this because you subscribed to Sudarshan Karweer updates. '
             f'<a href="{unsubscribe_url}" style="color:#9ca3af;text-decoration:underline;">Unsubscribe</a> anytime.</p>'
             if unsubscribe_url else "")
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {name or "there"},</p>'
        f'<p style="font-size:14px;color:#374151;">Here is this week\'s fresh shelf from the Leadership Library — read the classics, listen free, and turn each one into a daily ritual.</p>'
        f'<div style="margin-top:14px;">{cards}</div>'
        f'<a href="{site}/library" style="display:inline-block;margin-top:8px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Open the Library</a>'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
        f'{unsub}'
    )
    return _shell("This week's Leadership shelf", inner)


def send_library_digest_email(to_email: str, name: str, books: list, site: str = "https://www.sudarshankarweer.com", unsubscribe_url: str = "") -> str:
    """Weekly fresh Library shelf to a subscriber (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email or not books:
        return "skipped"
    msg = EmailMessage()
    msg["Subject"] = "This week's Leadership shelf 📚"
    msg["From"] = user
    msg["To"] = to_email
    if unsubscribe_url:
        msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.set_content("This week's Leadership shelf: " + " | ".join(b.get("title", "") for b in books)
                    + f"  Open the Library: {site}/library"
                    + (f"  Unsubscribe: {unsubscribe_url}" if unsubscribe_url else ""))
    msg.add_alternative(render_library_digest_html(name, books, site, unsubscribe_url), subtype="html")
    return _smtp_send(msg)


def send_score_beaten_email(to_email: str, name: str, game_title: str, rival: str,
                            new_score: int, your_score: int, max_score: int, game_url: str) -> str:
    """Nudge a dethroned strategist to reclaim their #1 spot (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    msg = EmailMessage()
    msg["Subject"] = f"Someone just beat your top score on \u201c{game_title}\u201d"
    msg["From"] = user
    msg["To"] = to_email
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {name or "there"},</p>'
        f'<p style="font-size:14px;color:#374151;">Your #1 spot on the <strong>{game_title}</strong> strategy simulation just got taken. '
        f'{rival or "A rival"} scored <strong>{new_score}/{max_score}</strong> — edging past your <strong>{your_score}/{max_score}</strong>.</p>'
        f'<p style="font-size:14px;color:#374151;">Think you can reclaim the top of the War Room? One better run is all it takes.</p>'
        f'<a href="{game_url}" style="display:inline-block;margin-top:8px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Reclaim your spot</a>'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
    )
    msg.set_content(f"{rival} beat your top score on {game_title} ({new_score}/{max_score} vs your {your_score}/{max_score}). Reclaim it: {game_url}")
    msg.add_alternative(_shell("You've been dethroned", inner), subtype="html")
    return _smtp_send(msg)



def render_sector_digest_html(name: str, groups: list, site: str = "https://www.sudarshankarweer.com", unsubscribe_url: str = "", prefs_url: str = "") -> str:
    blocks = ""
    for g in groups:
        rows = ""
        for it in (g.get("items") or [])[:4]:
            rows += (
                f'<a href="{it.get("link","#")}" style="display:block;text-decoration:none;padding:7px 0;border-bottom:1px solid #f0f0f0;">'
                f'<span style="font-size:11px;color:#059669;font-weight:600;">{it.get("source","")}</span>'
                f'<span style="display:block;font-size:13px;color:#111;line-height:1.35;">{it.get("title","")}</span></a>'
            )
        ins = (f'<p style="font-size:12px;color:#6b7280;font-style:italic;margin:8px 0 0;">SK Take: {g.get("insight")}</p>' if g.get("insight") else "")
        path = "sectors" if g.get("kind") == "sector" else ("capital" if g.get("kind") == "agency" else "oems")
        link = f'{site}/{path}/{g.get("slug","")}'
        rows_html = rows or "<p style='font-size:13px;color:#9ca3af;margin:6px 0;'>No major headlines this week.</p>"
        blocks += (
            f'<div style="border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;margin-bottom:12px;">'
            f'<a href="{link}" style="font-size:15px;font-weight:700;color:#111;text-decoration:none;">{g.get("label","")} &rarr;</a>'
            f'<div style="margin-top:6px;">{rows_html}</div>{ins}</div>'
        )
    prefs = (f'<a href="{prefs_url}" style="color:#059669;text-decoration:underline;">Manage your topics</a> · ' if prefs_url else "")
    unsub = (f'<p style="font-size:12px;color:#9ca3af;margin-top:20px;text-align:center;">'
             f'{prefs}You receive this because you subscribed to Sudarshan Karweer updates. '
             f'<a href="{unsubscribe_url}" style="color:#9ca3af;text-decoration:underline;">Unsubscribe</a> anytime.</p>'
             if (unsubscribe_url or prefs_url) else "")
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {name or "there"},</p>'
        f'<p style="font-size:14px;color:#374151;">Your Monday brief — the week\'s biggest moves across the sectors and capital you follow.</p>'
        f'<div style="margin-top:14px;">{blocks}</div>'
        f'<a href="{site}/explore" style="display:inline-block;margin-top:4px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Explore Sectors &amp; Capital</a>'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
        f'{unsub}'
    )
    return _shell("Weekly Sector Brief", inner)


def send_sector_digest_email(to_email: str, name: str, groups: list, site: str = "https://www.sudarshankarweer.com", unsubscribe_url: str = "", prefs_url: str = "") -> str:
    """Monday sector/agency news round-up to a subscriber (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email or not groups:
        return "skipped"
    msg = EmailMessage()
    msg["Subject"] = "Your weekly sector brief"
    msg["From"] = user
    msg["To"] = to_email
    if unsubscribe_url:
        msg["List-Unsubscribe"] = f"<{unsubscribe_url}>"
        msg["List-Unsubscribe-Post"] = "List-Unsubscribe=One-Click"
    msg.set_content("Your weekly sector brief: " + " | ".join(g.get("label", "") for g in groups) + f"  Read more: {site}/explore")
    msg.add_alternative(render_sector_digest_html(name, groups, site, unsubscribe_url, prefs_url), subtype="html")
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



def send_abandoned_nudge_email(to_email: str, booking: dict, resume_url: str) -> str:
    """Gentle nudge to complete an abandoned consultation payment (INERT until SMTP configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {booking.get("name","there")},</p>'
        f'<p style="font-size:14px;color:#374151;">You were almost there — your <strong>{booking.get("package","")}</strong> slot on '
        f'<strong>{booking.get("slot_date","")} {booking.get("slot_time","")} IST</strong> is still held for you, but payment wasn\'t completed.</p>'
        f'<p style="font-size:14px;color:#374151;">Complete your booking securely to lock it in — the total is {_inr(booking.get("amount_total",0))} (incl. GST).</p>'
        f'<a href="{resume_url}" style="display:inline-block;margin-top:10px;background:#C6F135;color:#0A0A0A;padding:12px 24px;border-radius:999px;text-decoration:none;font-weight:700;font-size:14px;">Complete my booking</a>'
        f'<p style="font-size:12px;color:#9ca3af;margin-top:16px;">If we don\'t hear from you, the slot is released so someone else can book it. No charge has been made.</p>'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
    )
    msg = EmailMessage()
    msg["Subject"] = "Your consultation slot is still held — complete your booking"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Complete your {booking.get('package','')} booking on {booking.get('slot_date','')} {booking.get('slot_time','')} IST: {resume_url}")
    msg.add_alternative(_shell("Complete your booking", inner), subtype="html")
    return _smtp_send(msg)


def render_gst_invoice_html(booking: dict, gst: dict) -> str:
    base = float(booking.get("amount", 0))
    gst_amt = float(booking.get("gst_amount", 0))
    total = float(booking.get("amount_total", 0))
    half = round(gst_amt / 2, 2)
    rows = (
        f'<tr><td style="padding:8px;border:1px solid #e5e7eb;">{booking.get("package","Consultation")} (SAC {gst.get("sac","998311")})</td>'
        f'<td style="padding:8px;border:1px solid #e5e7eb;text-align:right;">{_inr(base)}</td></tr>'
        f'<tr><td style="padding:8px;border:1px solid #e5e7eb;">CGST @ 9%</td><td style="padding:8px;border:1px solid #e5e7eb;text-align:right;">{_inr(half)}</td></tr>'
        f'<tr><td style="padding:8px;border:1px solid #e5e7eb;">SGST @ 9%</td><td style="padding:8px;border:1px solid #e5e7eb;text-align:right;">{_inr(half)}</td></tr>'
        f'<tr><td style="padding:8px;border:1px solid #e5e7eb;font-weight:700;">Total (incl. GST)</td>'
        f'<td style="padding:8px;border:1px solid #e5e7eb;text-align:right;font-weight:700;">{_inr(total)}</td></tr>'
    )
    supplier = (
        f'<p style="margin:0;font-size:15px;font-weight:700;color:#111;">{gst.get("legal_name","")}</p>'
        f'<p style="margin:2px 0;font-size:12px;color:#374151;">{gst.get("address","")}</p>'
        f'<p style="margin:2px 0;font-size:12px;color:#374151;">GSTIN: {gst.get("gstin","")}'
        + (f' · State: {gst.get("state","")} ({gst.get("state_code","")})' if gst.get("state") else "") + '</p>'
    )
    inner = (
        '<p style="font-size:18px;font-weight:800;color:#111;letter-spacing:.04em;">TAX INVOICE</p>'
        f'{supplier}'
        f'<table style="width:100%;margin-top:14px;font-size:12px;color:#374151;"><tr>'
        f'<td>Invoice No: <strong>{booking.get("invoice_no","")}</strong></td>'
        f'<td style="text-align:right;">Date: <strong>{(booking.get("invoice_at","") or "")[:10]}</strong></td></tr></table>'
        f'<p style="margin-top:12px;font-size:13px;color:#111;">Billed to: <strong>{booking.get("name","")}</strong> ({booking.get("email","")})</p>'
        f'<p style="margin:2px 0;font-size:12px;color:#6b7280;">Session: {booking.get("slot_date","")} {booking.get("slot_time","")} IST · Payment ID {booking.get("razorpay_payment_id","")}</p>'
        f'<table style="width:100%;border-collapse:collapse;margin-top:12px;font-size:13px;color:#111;">'
        f'<tr><th style="padding:8px;border:1px solid #e5e7eb;text-align:left;">Description</th>'
        f'<th style="padding:8px;border:1px solid #e5e7eb;text-align:right;">Amount</th></tr>{rows}</table>'
        f'<p style="margin-top:10px;font-size:11px;color:#9ca3af;">Place of supply defaults to the supplier state for B2C where recipient GSTIN/address is not provided. This is a computer-generated tax invoice.</p>'
        f'<p style="font-size:13px;color:#374151;margin-top:14px;">— {gst.get("legal_name","Team Sudarshan Karweer")}</p>'
    )
    return _shell("Tax Invoice", inner)


def send_gst_invoice_email(to_email: str, booking: dict, gst: dict) -> str:
    """Email a GST tax invoice alongside the payment receipt (INERT until SMTP + GSTIN configured)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email or not gst.get("gstin"):
        return "skipped"
    msg = EmailMessage()
    msg["Subject"] = f"Tax Invoice {booking.get('invoice_no','')} — Sudarshan Karweer"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Tax Invoice {booking.get('invoice_no','')} for {booking.get('package','')}. "
                    f"Total {booking.get('amount_total','')} INR incl. GST. GSTIN {gst.get('gstin','')}.")
    msg.add_alternative(render_gst_invoice_html(booking, gst), subtype="html")
    return _smtp_send(msg)


def send_admin_notify(to_email: str, subject: str, body_txt: str) -> str:
    """Plain internal alert to the advisor/team (lead-magnet, corporate inquiry, new purchase)."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    safe = (body_txt or "").replace("\n", "<br>")
    inner = (f'<p style="font-size:15px;color:#111;font-weight:600;">{subject}</p>'
             f'<p style="font-size:14px;color:#374151;line-height:1.6;">{safe}</p>')
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(body_txt or subject)
    msg.add_alternative(_shell("Internal alert", inner), subtype="html")
    return _smtp_send(msg)


def send_nurture_welcome_email(to_email: str, name: str, site: str = "https://www.sudarshankarweer.com", unsubscribe_url: str = "") -> str:
    """Welcome + first insight for a new lead-magnet / newsletter subscriber."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    unsub = (f'<p style="font-size:12px;color:#9ca3af;margin-top:18px;">Not for you? '
             f'<a href="{unsubscribe_url}" style="color:#9ca3af;">Unsubscribe</a>.</p>') if unsubscribe_url else ""
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {name},</p>'
        f'<p style="font-size:14px;color:#374151;line-height:1.6;">Welcome — you\'re now on the inside track. '
        f'Expect sharp, no-noise signals on strategy, leadership and the sectors Sudarshan works across, '
        f'straight to your inbox.</p>'
        f'<p style="font-size:14px;color:#374151;line-height:1.6;">Your first read is waiting on the site — '
        f'start with the Leadership Assessment to see where you stand today.</p>'
        f'<a href="{site}/assessment" style="display:inline-block;margin-top:14px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Start the assessment</a>'
        f'<p style="font-size:13px;color:#374151;margin-top:18px;">— Team Sudarshan Karweer</p>'
        f'{unsub}'
    )
    msg = EmailMessage()
    msg["Subject"] = "You're in — your first insight from Sudarshan"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Hi {name}, welcome. Start with the Leadership Assessment at {site}/assessment")
    msg.add_alternative(_shell("Welcome", inner), subtype="html")
    return _smtp_send(msg)


def send_purchase_email(to_email: str, name: str, kind: str, title: str, download_url: str = "", site: str = "https://www.sudarshankarweer.com") -> str:
    """Purchase confirmation + access for a digital product or cohort seat."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    if kind == "product":
        cta = (f'<a href="{download_url}" style="display:inline-block;margin-top:14px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Download now</a>'
               if download_url else "")
        line = f'Your purchase of <strong>{title}</strong> is confirmed. Your download is ready below.'
    else:
        cta = (f'<a href="{site}" style="display:inline-block;margin-top:14px;background:#C6F135;color:#0A0A0A;padding:10px 20px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">View details</a>')
        line = f'Your seat in <strong>{title}</strong> is booked. Joining details and the schedule will follow shortly.'
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {name},</p>'
        f'<p style="font-size:14px;color:#374151;line-height:1.6;">{line}</p>'
        f'{cta}'
        f'<p style="font-size:13px;color:#374151;margin-top:18px;">— Team Sudarshan Karweer</p>'
    )
    msg = EmailMessage()
    msg["Subject"] = f"Confirmed: {title}"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Hi {name}, your purchase of {title} is confirmed. {download_url}")
    msg.add_alternative(_shell("Purchase confirmed", inner), subtype="html")
    return _smtp_send(msg)


def send_commerce_abandoned_email(to_email: str, name: str, item_title: str, resume_url: str, code: str = "", label: str = "") -> str:
    """One-tap 'finish your order' nudge for an abandoned product/cohort checkout, carrying any promo code."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    promo_line = ""
    if code:
        promo_line = (f'<div style="margin-top:12px;border:1px dashed #C6F135;border-radius:12px;padding:12px 14px;background:#f7ffe0;">'
                      f'<span style="font-size:13px;color:#374151;">Your code </span>'
                      f'<span style="font-family:monospace;font-weight:700;color:#0A0A0A;">{code}</span>'
                      f'<span style="font-size:13px;color:#374151;">{(" · " + label) if label else ""} is still saved for you.</span></div>')
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {name or "there"},</p>'
        f'<p style="font-size:14px;color:#374151;line-height:1.6;">You were a tap away from <strong>{item_title}</strong>. '
        f'It\'s still waiting for you — pick up right where you left off.</p>'
        f'{promo_line}'
        f'<a href="{resume_url}" style="display:inline-block;margin-top:16px;background:#C6F135;color:#0A0A0A;padding:11px 22px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Finish my order</a>'
        f'<p style="font-size:13px;color:#374151;margin-top:18px;">— Team Sudarshan Karweer</p>'
    )
    msg = EmailMessage()
    msg["Subject"] = f"Still interested in {item_title}?"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Hi {name or 'there'}, finish your order for {item_title}: {resume_url}"
                    + (f" (code {code} saved)" if code else ""))
    msg.add_alternative(_shell("Complete your order", inner), subtype="html")
    return _smtp_send(msg)



def render_gift_email_html(recipient_name: str, buyer_name: str, item_title: str, kind: str, download_url: str = "", message: str = "", site: str = "https://www.sudarshankarweer.com", deliver_at: str = "") -> str:
    """Full HTML of the gift email — shared by the recipient email and the buyer's pre-pay preview."""
    if kind == "cohort":
        cta = f'<a href="{site}" style="display:inline-block;margin-top:14px;background:#C6F135;color:#0A0A0A;padding:11px 22px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">See the details</a>'
        line = f'<strong>{buyer_name or "Someone"}</strong> has gifted you a seat in <strong>{item_title}</strong>. Joining details and the schedule will follow shortly.'
    else:
        cta = (f'<a href="{download_url or "#"}" style="display:inline-block;margin-top:14px;background:#C6F135;color:#0A0A0A;padding:11px 22px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">Open your gift</a>')
        line = f'<strong>{buyer_name or "Someone"}</strong> has gifted you <strong>{item_title}</strong>. It\'s ready for you below.'
    note = (f'<div style="margin-top:14px;border-left:3px solid #C6F135;padding:6px 0 6px 14px;color:#374151;font-size:14px;font-style:italic;">"{message}"</div>' if message else "")
    when = (f'<p style="font-size:12px;color:#9ca3af;margin-top:14px;">Scheduled to arrive on {deliver_at[:10]}.</p>' if deliver_at else "")
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {recipient_name or "there"},</p>'
        f'<p style="font-size:14px;color:#374151;line-height:1.6;">{line}</p>'
        f'{note}{cta}'
        f'<p style="font-size:13px;color:#374151;margin-top:18px;">— Team Sudarshan Karweer</p>'
        f'{when}'
    )
    return _shell("A gift for you", inner)


def send_gift_email(to_email: str, recipient_name: str, buyer_name: str, item_title: str, kind: str, download_url: str = "", message: str = "", site: str = "https://www.sudarshankarweer.com") -> str:
    """Notify a gift recipient that someone bought them a product/cohort seat."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not to_email:
        return "skipped"
    msg = EmailMessage()
    msg["Subject"] = f"You've been gifted: {item_title}"
    msg["From"] = user
    msg["To"] = to_email
    msg.set_content(f"Hi {recipient_name or 'there'}, {buyer_name or 'someone'} gifted you {item_title}. {download_url}")
    msg.add_alternative(render_gift_email_html(recipient_name, buyer_name, item_title, kind, download_url, message, site), subtype="html")
    return _smtp_send(msg)



def send_gift_receipt_email(buyer_email: str, buyer_name: str, item_title: str, recipient_name: str, recipient_email: str, amount, message: str = "", site: str = "https://www.sudarshankarweer.com", deliver_at: str = "") -> str:
    """Forwardable receipt to the buyer confirming what they gifted and to whom."""
    user = os.environ.get("GMAIL_USER")
    pwd = os.environ.get("GMAIL_APP_PASSWORD")
    if not user or not pwd or not buyer_email:
        return "skipped"
    try:
        amt = f"\u20b9{int(float(amount)):,}"
    except Exception:
        amt = f"\u20b9{amount}"
    note = (f'<tr><td style="padding:6px 0;color:#6b7280;font-size:13px;">Your message</td>'
            f'<td style="padding:6px 0;color:#111;font-size:13px;text-align:right;">"{message}"</td></tr>' if message else "")
    delivery_line = (f'<p style="font-size:14px;color:#374151;line-height:1.6;">We\'ll deliver it to '
                     f'<strong>{recipient_name or recipient_email}</strong> on <strong>{deliver_at[:10]}</strong>. '
                     f'Here\'s your receipt, which you\'re welcome to forward.</p>'
                     if deliver_at else
                     f'<p style="font-size:14px;color:#374151;line-height:1.6;">Thank you — your gift is on its way. '
                     f'We\'ve emailed access directly to <strong>{recipient_name or recipient_email}</strong>. '
                     f'Here\'s your receipt, which you\'re welcome to forward.</p>')
    inner = (
        f'<p style="font-size:15px;color:#111;">Hi {buyer_name or "there"},</p>'
        f'{delivery_line}'
        f'<table style="width:100%;border:1px solid #e5e7eb;border-radius:12px;padding:14px 16px;margin-top:14px;border-collapse:separate;">'
        f'<tr><td style="padding:6px 0;color:#6b7280;font-size:13px;">Gift</td><td style="padding:6px 0;color:#111;font-weight:600;font-size:13px;text-align:right;">{item_title}</td></tr>'
        f'<tr><td style="padding:6px 0;color:#6b7280;font-size:13px;">Recipient</td><td style="padding:6px 0;color:#111;font-size:13px;text-align:right;">{recipient_name or ""}{(" · " + recipient_email) if recipient_email else ""}</td></tr>'
        f'{note}'
        f'<tr><td style="padding:10px 0 0;color:#6b7280;font-size:13px;border-top:1px solid #e5e7eb;">Amount paid</td>'
        f'<td style="padding:10px 0 0;color:#0A0A0A;font-weight:700;font-size:15px;text-align:right;border-top:1px solid #e5e7eb;">{amt}</td></tr>'
        f'</table>'
        f'<p style="font-size:13px;color:#374151;margin-top:16px;">— Team Sudarshan Karweer</p>'
    )
    msg = EmailMessage()
    msg["Subject"] = f"Your gift receipt · {item_title}"
    msg["From"] = user
    msg["To"] = buyer_email
    msg.set_content(f"Hi {buyer_name or 'there'}, your gift of {item_title} to {recipient_name or recipient_email} is confirmed. Amount: {amt}.")
    msg.add_alternative(_shell("Gift receipt", inner), subtype="html")
    return _smtp_send(msg)

