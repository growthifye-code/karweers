from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse, RedirectResponse, HTMLResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import asyncio
import logging
import uuid
import time
import io
import random
import hashlib
import razorpay
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from auth import hash_password, verify_password, create_access_token, decode_token, get_jwt_secret
import jwt as pyjwt
import pyotp
from seed_data import ARTICLES, SERVICES, STATS, MARKET_PULSE, TESTIMONIALS
import curator
from services_data import SERVICES as SERVICE_PAGES
from emailer import send_booking_email
from emailer import send_security_alert_email
from emailer import send_new_booking_alert_email, send_session_reminder_email, send_weekly_agenda_email, send_waitlist_opening_email
from emailer import send_consent_receipt_email
from emailer import send_signals_digest_email, render_signals_digest_html, send_test_email
from emailer import send_insights_newsletter_email
from emailer import send_insights_recap_email
from emailer import send_library_digest_email, send_score_beaten_email
from emailer import send_sector_digest_email
from emailer import send_payment_receipt_email, send_refund_email
from emailer import send_gst_invoice_email, send_abandoned_nudge_email
from emailer import send_admin_notify, send_nurture_welcome_email, send_purchase_email
from emailer import send_commerce_abandoned_email
from emailer import send_gift_email
from emailer import send_gift_receipt_email
import xml.etree.ElementTree as ET
import contextvars
from urllib.parse import quote_plus
from datetime import datetime as _dt

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')
HCAPTCHA_SECRET = os.environ.get('HCAPTCHA_SECRET', '')
HCAPTCHA_SITEKEY = os.environ.get('HCAPTCHA_SITEKEY', '')
_HCAPTCHA_TEST_SECRET = "0x0000000000000000000000000000000000000000"

# Strict admin allowlist — ONLY these emails may ever hold the admin role.
ADMIN_ALLOWLIST = {e.strip().lower() for e in os.environ.get('ADMIN_ALLOWLIST', '').split(',') if e.strip()}


def role_for(email: str) -> str:
    return "admin" if (email or "").lower() in ADMIN_ALLOWLIST else "client"


def gen_client_code() -> str:
    return "SK-" + uuid.uuid4().hex[:6].upper()


_current_host: contextvars.ContextVar = contextvars.ContextVar("_current_host", default="")
PREVIEW_HOST_MARKERS = ("preview.emergentagent.com", "preview.emergentcf.cloud", "localhost", "127.0.0.1")


def _is_preview_host(request=None) -> bool:
    host = ""
    if request is not None:
        host = (request.headers.get("x-forwarded-host") or request.headers.get("origin")
                or request.headers.get("host") or "")
    if not host:
        host = _current_host.get() or ""
    host = host.lower()
    return any(m in host for m in PREVIEW_HOST_MARKERS)


def verify_captcha(token, ip=None, request=None):
    if not token:
        raise HTTPException(status_code=400, detail="Captcha verification required")
    # Preview/dev: the real Enterprise sitekey is hostname-locked in the hCaptcha
    # dashboard, so the widget cannot complete a challenge on the ephemeral preview
    # domain. There the frontend uses the always-pass hCaptcha TEST key; accept a
    # present token. Production (real domain) always runs full server-side verify.
    if _is_preview_host(request):
        return True
    # Lenient mode: real site key set but real secret not yet configured.
    if HCAPTCHA_SECRET == _HCAPTCHA_TEST_SECRET:
        return True
    try:
        form = {"secret": HCAPTCHA_SECRET, "response": token}
        if HCAPTCHA_SITEKEY:
            form["sitekey"] = HCAPTCHA_SITEKEY
        if ip:
            form["remoteip"] = ip
        r = requests.post("https://api.hcaptcha.com/siteverify", data=form, timeout=10)
        ok = r.json().get("success", False)
    except Exception:
        raise HTTPException(status_code=503, detail="Captcha service unavailable")
    if not ok:
        raise HTTPException(status_code=403, detail="Captcha verification failed")
    return True


# Short-lived signed cookie proving a captcha was solved just before a Google OAuth redirect.
CAPTCHA_GATE_TTL = 600  # 10 minutes

# ---------------- Legal consent (T&C + Privacy) ----------------
CONSENT_POLICY_VERSION = os.environ.get("CONSENT_POLICY_VERSION", "2026-06-02")


async def record_consent(request: Request, email: str, name: str, action: str, user_id: str = ""):
    """Persist a tamper-evident record that the user agreed to T&C + Privacy at sign-in/up."""
    ts = now_iso()
    doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id or "",
        "email": (email or "").lower(),
        "name": name or "",
        "action": action,  # register | login | google
        "agreed": True,
        "terms_version": CONSENT_POLICY_VERSION,
        "privacy_version": CONSENT_POLICY_VERSION,
        "ip": _client_ip(request),
        "user_agent": (request.headers.get("user-agent", "") or "")[:400],
        "created_at": ts,
    }
    await db.consent_logs.insert_one(dict(doc))
    if user_id:
        await db.users.update_one({"id": user_id}, {"$set": {
            "consent": {"agreed": True, "version": CONSENT_POLICY_VERSION, "at": ts, "action": action}}})
    # Email the user a copy of what they agreed to (BCC admin for the compliance trail). INERT until SMTP is set.
    if doc["email"]:
        admin_bcc = os.environ.get("BOOKING_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL", "")
        try:
            asyncio.create_task(asyncio.to_thread(
                send_consent_receipt_email, doc["email"], name, action, CONSENT_POLICY_VERSION, ts, admin_bcc))
        except Exception:
            pass


def issue_captcha_gate(consent: bool = False) -> str:
    payload = {"purpose": "captcha_gate", "consent": bool(consent),
               "exp": datetime.now(timezone.utc) + timedelta(seconds=CAPTCHA_GATE_TTL)}
    return pyjwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def read_captcha_gate(token) -> Optional[dict]:
    if not token:
        return None
    try:
        data = pyjwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        if data.get("purpose") == "captcha_gate":
            return data
    except Exception:
        return None
    return None


def verify_captcha_gate(token) -> bool:
    return read_captcha_gate(token) is not None

app = FastAPI(title="Sudarshan Karweer Advisory")
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


# ---------------- Models ----------------
class RegisterIn(BaseModel):
    name: str
    email: EmailStr
    password: str
    captcha_token: Optional[str] = None
    consent: bool = False


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    captcha_token: Optional[str] = None
    consent: bool = False


class ConsultationIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = ""
    company: Optional[str] = ""
    area: str
    message: str
    captcha_token: Optional[str] = None


class ArticleIn(BaseModel):
    title: str
    category: str
    summary: str
    content: str
    sector: Optional[str] = ""
    tags: List[str] = []
    image: str = ""
    featured: bool = False


class ChatIn(BaseModel):
    session_id: str
    message: str


class GenerateIn(BaseModel):
    topic: str
    category: str


# ---------------- Auth helpers ----------------
EMERGENT_AUTH_URL = "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data"


async def _user_from_session(token: Optional[str]) -> Optional[dict]:
    if not token:
        return None
    sess = await db.user_sessions.find_one({"session_token": token})
    if not sess:
        return None
    exp = sess.get("expires_at")
    if isinstance(exp, str):
        try:
            exp = datetime.fromisoformat(exp)
        except Exception:
            exp = None
    if exp is not None:
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if exp < datetime.now(timezone.utc):
            return None
    return await db.users.find_one({"id": sess["user_id"]}, {"_id": 0, "password_hash": 0})


async def get_current_user(request: Request) -> dict:
    session_token = request.cookies.get("session_token")
    access_token = request.cookies.get("access_token")
    bearer = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        bearer = auth_header[7:]
    # 1) Google (Emergent) session tokens
    for t in (session_token, bearer):
        u = await _user_from_session(t)
        if u:
            return u
    # 2) JWT tokens (email/password auth)
    for t in (access_token, bearer):
        if not t:
            continue
        try:
            payload = decode_token(t)
        except Exception:
            continue
        u = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
        if u:
            return u
    raise HTTPException(status_code=401, detail="Not authenticated")


async def get_optional_user(request: Request) -> Optional[dict]:
    try:
        return await get_current_user(request)
    except HTTPException:
        return None


async def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


# ---------------- Auth routes ----------------
@api_router.post("/auth/register")
async def register(body: RegisterIn, request: Request):
    verify_captcha(body.captcha_token, _client_ip(request), request)
    if not body.consent:
        raise HTTPException(status_code=400, detail="You must read and agree to the Terms & Conditions and Privacy Policy to continue.")
    email = body.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    uid = str(uuid.uuid4())
    role = role_for(email)
    cc = gen_client_code()
    doc = {
        "id": uid, "email": email, "name": body.name, "client_code": cc,
        "password_hash": hash_password(body.password), "role": role,
        "created_at": now_iso(),
    }
    await db.users.insert_one(doc)
    await record_consent(request, email, body.name, "register", user_id=uid)
    token = create_access_token(uid, email, role)
    return {"token": token, "user": {"id": uid, "email": email, "name": body.name, "role": role, "client_code": cc}}


# ---------------- Login brute-force protection ----------------
LOGIN_MAX_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15


def _client_ip(request: Request) -> str:
    """Real client IP behind the ingress proxy (X-Forwarded-For), else socket peer."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    xri = request.headers.get("x-real-ip")
    if xri:
        return xri.strip()
    return request.client.host if request.client else "unknown"


def _login_identifier(request: Request, email: str) -> str:
    return f"{_client_ip(request)}:{email}"


async def check_login_lockout(identifier: str):
    """Raise 429 if this ip+email is currently locked out."""
    doc = await db.login_attempts.find_one({"identifier": identifier})
    if not doc:
        return
    locked_until = doc.get("locked_until")
    if not locked_until:
        return
    try:
        lu = datetime.fromisoformat(locked_until)
        if lu.tzinfo is None:
            lu = lu.replace(tzinfo=timezone.utc)
    except Exception:
        return
    now = datetime.now(timezone.utc)
    if lu > now:
        retry = int((lu - now).total_seconds())
        raise HTTPException(status_code=429,
                            detail=f"Too many failed attempts. Try again in {max(1, retry // 60) } minute(s).",
                            headers={"Retry-After": str(retry)})


async def register_failed_login(identifier: str, ip: str, email: str):
    """Increment failed-attempt counter; lock after threshold; escalate to IP ban on attack."""
    doc = await db.login_attempts.find_one({"identifier": identifier})
    count = (doc or {}).get("count", 0) + 1
    fail_total = (doc or {}).get("fail_total", 0) + 1
    update = {"count": count, "fail_total": fail_total, "ip": ip, "email": email, "updated_at": now_iso()}
    locked = False
    if count >= LOGIN_MAX_ATTEMPTS:
        update["locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=LOGIN_LOCKOUT_MINUTES)).isoformat()
        update["count"] = 0  # reset counter; lockout window now governs access
        locked = True
    await db.login_attempts.update_one({"identifier": identifier}, {"$set": update}, upsert=True)
    if locked:
        await raise_security_alert("medium", "account_lockout", ip,
                                   "Repeated failed logins", f"{email} locked for {LOGIN_LOCKOUT_MINUTES} min", email=email)
        await evaluate_credential_stuffing(ip)


async def evaluate_credential_stuffing(ip: str):
    """One IP failing across many accounts (or very high total fails) => attack => auto-ban."""
    docs = await db.login_attempts.find({"ip": ip}).to_list(1000)
    distinct = {d.get("email") for d in docs if d.get("email")}
    total = sum(d.get("fail_total", 0) for d in docs)
    if len(distinct) >= CRED_STUFF_DISTINCT_EMAILS or total >= CRED_STUFF_TOTAL_FAILS:
        if not await is_ip_banned(ip):
            await ban_ip(ip, "Credential stuffing",
                         f"{len(distinct)} accounts targeted · {total} failed logins")


async def clear_login_attempts(identifier: str):
    await db.login_attempts.delete_one({"identifier": identifier})


# ---------------- Site-wide security guard (auto-detect & block attacks) ----------------
import time as _time
from collections import defaultdict, deque

RATE_WINDOW_SEC = 10
RATE_MAX_REQUESTS = 100          # per IP per window across ALL /api endpoints
BAN_MINUTES = 60                 # auto-ban duration
CRED_STUFF_DISTINCT_EMAILS = 3   # 1 IP failing across N accounts => attack
CRED_STUFF_TOTAL_FAILS = 15

MALICIOUS_PATTERNS = [
    "../", "..%2f", "%2e%2e", "/etc/passwd", "/.env", "/.git", "/wp-admin", "/wp-login",
    "/phpmyadmin", "/vendor/", "/.aws", "/config.json", "<script", "onerror=", "javascript:",
    "union select", "union+select", " or 1=1", "'or'1'='1", "sleep(", "benchmark(", "%00",
    "/cgi-bin/", "/actuator", "/.ssh", "eval(", "base64_decode", "/xmlrpc.php",
]

_req_log = defaultdict(deque)    # ip -> deque[timestamps]
_banned_ips = {}                 # ip -> banned_until epoch (in-memory cache)
_banned_cidrs = {}               # cidr string -> banned_until epoch (range blocks)


async def raise_security_alert(severity: str, atype: str, ip: str, reason: str, detail: str, email: str = ""):
    alert = {"id": str(uuid.uuid4()), "type": atype, "severity": severity, "ip": ip,
             "email": email, "reason": reason, "detail": detail, "created_at": now_iso(), "seen": False}
    await db.security_alerts.insert_one(dict(alert))
    logger.warning("SECURITY[%s] %s ip=%s :: %s (%s)", severity, atype, ip, reason, detail)
    try:
        to = os.environ.get("BOOKING_ADMIN_EMAIL", "")
        asyncio.create_task(asyncio.to_thread(send_security_alert_email, to, alert))
    except Exception:
        pass


async def ban_ip(ip: str, reason: str, detail: str, minutes: int = BAN_MINUTES, severity: str = "high"):
    await _apply_block(ip, "ip", reason, detail, minutes, severity)


_audit_retention_days = 90


async def audit(request: Request, actor: str, action: str, target: str = "", meta: str = ""):
    """Tamper-evident admin action trail (auto-expires per retention policy)."""
    now = datetime.now(timezone.utc)
    await db.audit_log.insert_one({
        "id": str(uuid.uuid4()), "actor": actor or "unknown", "action": action,
        "target": target, "meta": meta, "ip": _client_ip(request), "at": now_iso(),
        "expire_at": now + timedelta(days=_audit_retention_days)})


async def _apply_block(target: str, scope: str, reason: str, detail: str,
                       minutes: int = BAN_MINUTES, severity: str = "high", alert: bool = True):
    until = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    if scope == "cidr":
        _banned_cidrs[target] = until.timestamp()
    else:
        _banned_ips[target] = until.timestamp()
    await db.blocked_ips.update_one({"ip": target}, {"$set": {
        "ip": target, "scope": scope, "reason": reason, "detail": detail,
        "banned_until": until.isoformat(), "updated_at": now_iso()}}, upsert=True)
    if alert:
        await raise_security_alert(severity, "cidr_banned" if scope == "cidr" else "ip_banned",
                                   target, reason, detail)


import ipaddress as _ipaddr


async def is_ip_banned(ip: str) -> bool:
    now = _time.time()
    exp = _banned_ips.get(ip)
    if exp is not None:
        if exp > now:
            return True
        _banned_ips.pop(ip, None)
    # Range (CIDR) blocks — stop a whole attacking network.
    try:
        addr = _ipaddr.ip_address(ip)
        for cidr, until in list(_banned_cidrs.items()):
            if until <= now:
                _banned_cidrs.pop(cidr, None)
                continue
            try:
                if addr in _ipaddr.ip_network(cidr, strict=False):
                    return True
            except Exception:
                continue
    except Exception:
        pass
    doc = await db.blocked_ips.find_one({"ip": ip})
    if not doc:
        return False
    try:
        t = datetime.fromisoformat(doc.get("banned_until"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=timezone.utc)
    except Exception:
        return False
    if t > datetime.now(timezone.utc):
        _banned_ips[ip] = t.timestamp()
        return True
    return False


async def lookup_country(ip: str):
    """Best-effort country for an offender IP, cached in Mongo. Returns (country, code)."""
    doc = await db.ip_geo.find_one({"ip": ip})
    if doc:
        return doc.get("country", "Unknown"), doc.get("cc", "")
    country, cc = "Unknown", ""
    try:
        r = await asyncio.to_thread(
            requests.get, f"http://ip-api.com/json/{ip}?fields=status,country,countryCode", timeout=4)
        j = r.json()
        if j.get("status") == "success":
            country, cc = j.get("country", "Unknown"), j.get("countryCode", "")
    except Exception:
        pass
    await db.ip_geo.update_one({"ip": ip}, {"$set": {"ip": ip, "country": country, "cc": cc}}, upsert=True)
    return country, cc


def _subnet24(ip: str) -> str:
    try:
        a = _ipaddr.ip_address(ip)
        if a.version == 4:
            return ".".join(ip.split(".")[:3]) + ".0/24"
        return str(_ipaddr.ip_network(ip + "/64", strict=False))
    except Exception:
        return ""


# ---------------- VPN / proxy guard + TOTP trusted-token bypass ----------------
VPNAPI_KEY = os.environ.get("VPNAPI_KEY", "")
IPQS_API_KEY = os.environ.get("IPQS_API_KEY", "")
VPN_TOTP_TTL_HOURS = 12


async def vpn_guard_enabled() -> bool:
    doc = await db.app_meta.find_one({"_id": "vpn_guard"})
    return bool(doc and doc.get("enabled"))


async def vpn_allowlist() -> list:
    doc = await db.app_meta.find_one({"_id": "vpn_allowlist"})
    return (doc or {}).get("ips", [])


async def detect_vpn(ip: str) -> dict:
    """Cached IP intel via vpnapi.io / IPQualityScore (fail-open on error).

    Returns vpn/proxy/tor plus threat signals (fraud_score, recent_abuse) and a
    computed `threat` flag. VPNs/proxies are NOT threats on their own — only Tor,
    high fraud score or recent abuse are. `_fresh` is True on a cache miss."""
    now = datetime.now(timezone.utc)
    hit = await db.ip_risk_cache.find_one({"_id": ip})
    if hit:
        try:
            exp = datetime.fromisoformat(hit["expireAt"])
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp > now:
                return {"vpn": hit.get("vpn", False), "proxy": hit.get("proxy", False),
                        "tor": hit.get("tor", False), "provider": hit.get("provider", "cache"),
                        "fraud_score": hit.get("fraud_score"), "recent_abuse": hit.get("recent_abuse", False),
                        "flagged": hit.get("flagged", False), "threat": hit.get("threat", False), "_fresh": False}
        except Exception:
            pass
    vpn = proxy = tor = recent_abuse = False
    fraud_score = None
    provider = "none"
    if VPNAPI_KEY:
        try:
            r = await asyncio.to_thread(requests.get, f"https://vpnapi.io/api/{ip}",
                                        params={"key": VPNAPI_KEY}, timeout=5)
            j = r.json()
            if "security" not in j:
                raise RuntimeError(j.get("message", "vpnapi error/quota"))
            s = j["security"]
            vpn, proxy, tor = bool(s.get("vpn")), bool(s.get("proxy")), bool(s.get("tor"))
            provider = "vpnapi.io"
        except Exception:
            provider = "error"
    if provider != "vpnapi.io" and IPQS_API_KEY:
        try:
            r = await asyncio.to_thread(
                requests.get, f"https://www.ipqualityscore.com/api/json/ip/{IPQS_API_KEY}/{ip}",
                params={"strictness": 0, "allow_public_access_points": "true"}, timeout=5)
            j = r.json()
            if j.get("success"):
                vpn, proxy, tor = bool(j.get("vpn")), bool(j.get("proxy")), bool(j.get("tor"))
                recent_abuse = bool(j.get("recent_abuse"))
                fraud_score = j.get("fraud_score")
                provider = "ipqualityscore"
        except Exception:
            pass
    flagged = vpn or proxy or tor
    threat = _is_threat({"tor": tor, "recent_abuse": recent_abuse, "fraud_score": fraud_score})
    ttl = timedelta(minutes=2) if provider in ("error", "none") else timedelta(hours=24)
    await db.ip_risk_cache.update_one({"_id": ip}, {"$set": {
        "_id": ip, "vpn": vpn, "proxy": proxy, "tor": tor, "provider": provider,
        "fraud_score": fraud_score, "recent_abuse": recent_abuse,
        "flagged": flagged, "threat": threat, "expireAt": (now + ttl).isoformat()}}, upsert=True)
    return {"vpn": vpn, "proxy": proxy, "tor": tor, "provider": provider, "fraud_score": fraud_score,
            "recent_abuse": recent_abuse, "flagged": flagged, "threat": threat, "_fresh": True}


def _is_threat(intel: dict) -> bool:
    """A genuine security threat — NOT a plain VPN/proxy. Tor exit nodes, IPs with
    recent abuse history, or a very high fraud score are blocked."""
    if intel.get("tor") or intel.get("recent_abuse"):
        return True
    fs = intel.get("fraud_score")
    return isinstance(fs, (int, float)) and fs >= 88


def _issue_vpn_totp_cookie() -> str:
    return pyjwt.encode({"purpose": "vpn_totp",
                         "exp": datetime.now(timezone.utc) + timedelta(hours=VPN_TOTP_TTL_HOURS)},
                        get_jwt_secret(), algorithm="HS256")


def _verify_vpn_totp_cookie(token) -> bool:
    if not token:
        return False
    try:
        return pyjwt.decode(token, get_jwt_secret(), algorithms=["HS256"]).get("purpose") == "vpn_totp"
    except Exception:
        return False


async def _totp_matches(code: str) -> bool:
    code = (code or "").strip()
    if not (code.isdigit() and len(code) == 6):
        return False
    async for t in db.trusted_totp.find({"enabled": True}):
        try:
            if pyotp.TOTP(t["secret"]).verify(code, valid_window=1):
                return True
        except Exception:
            continue
    return False


async def vpn_should_block(request: Request) -> bool:
    """VPNs/proxies are ALLOWED (only flagged for visibility). Only genuine threats
    — Tor, recent abuse, or a very high fraud score — are blocked. Allowlisted IPs
    and TOTP-verified sessions are always let through."""
    if not await vpn_guard_enabled():
        return False
    ip = _client_ip(request)
    if ip in await vpn_allowlist():
        return False
    if _verify_vpn_totp_cookie(request.cookies.get("vpn_totp")):
        return False
    intel = await detect_vpn(ip)
    # Flag any VPN/proxy/Tor detection for admin visibility, once per fresh lookup.
    if intel.get("flagged") and intel.get("_fresh"):
        labels = ",".join(k for k in ("vpn", "proxy", "tor") if intel.get(k)) or "flagged"
        await raise_security_alert(
            "high" if intel.get("threat") else "low",
            "ip_threat" if intel.get("threat") else "ip_flagged", ip, labels,
            f"provider={intel.get('provider')} fraud={intel.get('fraud_score')} recent_abuse={intel.get('recent_abuse')}")
    return bool(intel.get("threat"))


async def blocked_countries() -> set:
    doc = await db.app_meta.find_one({"_id": "blocked_countries"})
    return set((doc or {}).get("codes", []))


async def country_should_block(request: Request):
    """(blocked, country_name, country_code) — hard geo block, independent of the VPN toggle."""
    codes = await blocked_countries()
    if not codes:
        return (False, "", "")
    ip = _client_ip(request)
    if ip in await vpn_allowlist():
        return (False, "", "")
    country, cc = await lookup_country(ip)
    if cc and cc in codes:
        return (True, country, cc)
    return (False, country, cc)


@api_router.post("/auth/login")
async def login(body: LoginIn, request: Request):
    client_ip = _client_ip(request)
    verify_captcha(body.captcha_token, client_ip, request)
    if not body.consent:
        raise HTTPException(status_code=400, detail="You must read and agree to the Terms & Conditions and Privacy Policy to continue.")
    email = body.email.lower()
    identifier = _login_identifier(request, email)
    await check_login_lockout(identifier)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        await register_failed_login(identifier, client_ip, email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await clear_login_attempts(identifier)
    await record_consent(request, email, user.get("name", ""), "login", user_id=user["id"])
    # Enforce allowlist: role always reflects the allowlist, never drifts.
    role = role_for(email)
    if user.get("role") != role:
        await db.users.update_one({"id": user["id"]}, {"$set": {"role": role}})
    token = create_access_token(user["id"], email, role)
    return {"token": token, "user": {"id": user["id"], "email": email, "name": user["name"], "role": role}}


@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


class SessionIn(BaseModel):
    session_id: Optional[str] = None


class CaptchaGateIn(BaseModel):
    captcha_token: Optional[str] = None
    consent: bool = False


@api_router.post("/auth/captcha-gate")
async def captcha_gate(body: CaptchaGateIn, request: Request, response: Response):
    """Verify a solved hCaptcha + consent, then set a short-lived cookie that gates the Google OAuth redirect."""
    verify_captcha(body.captcha_token, _client_ip(request), request)
    if not body.consent:
        raise HTTPException(status_code=400, detail="You must read and agree to the Terms & Conditions and Privacy Policy to continue.")
    response.set_cookie("captcha_gate", issue_captcha_gate(consent=True), httponly=True, secure=True,
                        samesite="none", path="/", max_age=CAPTCHA_GATE_TTL)
    return {"ok": True}


@api_router.post("/auth/session")
async def create_session(body: SessionIn, request: Request, response: Response):
    # hCaptcha + consent must have been captured on the login/register page before the Google redirect.
    gate = read_captcha_gate(request.cookies.get("captcha_gate"))
    if not gate:
        raise HTTPException(status_code=403, detail="Captcha verification required")
    if not gate.get("consent"):
        raise HTTPException(status_code=400, detail="You must read and agree to the Terms & Conditions and Privacy Policy to continue.")
    session_id = body.session_id or request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Missing session id")
    try:
        r = requests.get(EMERGENT_AUTH_URL, headers={"X-Session-ID": session_id}, timeout=10)
    except Exception:
        raise HTTPException(status_code=503, detail="Auth service unavailable")
    if r.status_code != 200:
        raise HTTPException(status_code=401, detail="Invalid session")
    data = r.json()
    email = (data.get("email") or "").lower()
    if not email:
        raise HTTPException(status_code=401, detail="Invalid session data")
    existing = await db.users.find_one({"email": email})
    role = role_for(email)  # allowlist decides admin; everyone else is a client
    if existing:
        uid = existing["id"]
        cc = existing.get("client_code") or gen_client_code()
        await db.users.update_one({"id": uid}, {"$set": {
            "name": data.get("name") or existing.get("name"),
            "picture": data.get("picture", ""), "auth": "google", "role": role, "client_code": cc}})
    else:
        uid = str(uuid.uuid4())
        cc = gen_client_code()
        await db.users.insert_one({
            "id": uid, "email": email, "name": data.get("name") or email.split("@")[0],
            "picture": data.get("picture", ""), "role": role, "auth": "google",
            "client_code": cc, "created_at": now_iso()})
    session_token = data["session_token"]
    expires = datetime.now(timezone.utc) + timedelta(days=7)
    await db.user_sessions.insert_one({
        "user_id": uid, "session_token": session_token,
        "expires_at": expires.isoformat(), "created_at": now_iso()})
    response.set_cookie("session_token", session_token, httponly=True, secure=True,
                        samesite="none", path="/", max_age=7 * 24 * 3600)
    response.delete_cookie("captcha_gate", path="/")
    await record_consent(request, email, data.get("name") or "", "google", user_id=uid)
    return {"user": {"id": uid, "email": email, "name": data.get("name"), "role": role,
                     "picture": data.get("picture", "")}}


@api_router.post("/auth/logout")
async def logout_route(request: Request, response: Response):
    stoken = request.cookies.get("session_token")
    if stoken:
        await db.user_sessions.delete_one({"session_token": stoken})
    response.delete_cookie("session_token", path="/")
    return {"success": True}


# ---------------- Learning / curation + recommendations ----------------
class TrackIn(BaseModel):
    kind: str
    ref: Optional[str] = ""
    label: Optional[str] = ""


@api_router.get("/learning/topics")
async def learning_topics():
    return curator.TOPICS


@api_router.get("/learning/videos")
async def learning_videos(topic: Optional[str] = None, limit: int = 60):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: curator.library(topic, limit))
    return {"videos": data}


@api_router.get("/learning/daily")
async def learning_daily(limit: int = 10):
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: curator.daily(min(limit, 10)))
    return {"videos": data}


@api_router.post("/track")
async def track_activity(body: TrackIn, user: Optional[dict] = Depends(get_optional_user)):
    if not user:
        return {"tracked": False}
    topics = curator.derive_topics(body.kind, body.ref)
    await db.activity_events.insert_one({
        "user_id": user["id"], "kind": body.kind, "ref": body.ref or "",
        "label": body.label or "", "topics": topics, "created_at": now_iso()})
    return {"tracked": True, "topics": topics}


async def _topic_weights(user_id: str) -> dict:
    weights = {}
    # Seed from explicitly declared interests (captured at login).
    u = await db.users.find_one({"id": user_id}, {"_id": 0, "interests": 1})
    for t in (u or {}).get("interests", []) or []:
        weights[t] = weights.get(t, 0) + 3.0
    events = await db.activity_events.find({"user_id": user_id}).sort("created_at", -1).to_list(300)
    now = datetime.now(timezone.utc)
    for ev in events:
        try:
            ts = datetime.fromisoformat(ev["created_at"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            days = max((now - ts).total_seconds() / 86400.0, 0)
        except Exception:
            days = 30
        recency = 0.94 ** days  # recent activity weighs more
        for t in ev.get("topics", []):
            weights[t] = weights.get(t, 0) + recency
    return weights


# ---------------- Client interests + relevant blogs ----------------
TOPIC_SECTORS = {
    "energy": ["Renewable Energy", "Energy Storage", "Green Hydrogen"],
    "climate-finance": ["Green Financing", "Sustainability"],
    "global-macro": ["Economy"],
    "india-economy": ["Economy"],
    "leadership": ["Business Strategy"],
    "fundraising": ["Business Strategy"],
    "technology": ["Renewable Energy", "Sustainability"],
    "ai": ["Sustainability"],
    "geopolitics": ["Economy"],
}


class InterestsIn(BaseModel):
    interests: List[str] = []


@api_router.post("/me/interests")
async def set_interests(body: InterestsIn, user: dict = Depends(get_current_user)):
    valid = [t for t in body.interests if t in curator.TOPIC_IDS]
    await db.users.update_one({"id": user["id"]}, {"$set": {"interests": valid}})
    return {"interests": valid}


@api_router.get("/me/blogs")
async def my_blogs(limit: int = 6, user: dict = Depends(get_current_user)):
    weights = await _topic_weights(user["id"])
    top = [t for t, _ in sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:3]]
    sectors = []
    for t in top:
        sectors.extend(TOPIC_SECTORS.get(t, []))
    q = {"sector": {"$in": sectors}} if sectors else {}
    items = await db.articles.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)
    if len(items) < limit:  # backfill with latest
        extra = await db.articles.find({}, {"_id": 0}).sort("created_at", -1).to_list(limit)
        seen = {a["slug"] for a in items}
        for a in extra:
            if a["slug"] not in seen:
                items.append(a)
            if len(items) >= limit:
                break
    return {"articles": items[:limit], "based_on": top}


# ---------------- CRM (admin) ----------------
@api_router.get("/admin/clients")
async def admin_clients(admin: dict = Depends(require_admin)):
    users = await db.users.find({"role": "client"}, {"_id": 0, "password_hash": 0}).sort("created_at", -1).to_list(2000)
    # Aggregate counts in a handful of queries (avoids per-user N+1).
    act = {d["_id"]: d for d in await db.activity_events.aggregate(
        [{"$group": {"_id": "$user_id", "n": {"$sum": 1}, "last": {"$max": "$created_at"}}}]).to_list(10000)}
    tk = {d["_id"]: d["n"] for d in await db.support_tickets.aggregate(
        [{"$group": {"_id": "$user_id", "n": {"$sum": 1}}}]).to_list(10000)}
    bk = {d["_id"]: d["n"] for d in await db.consultations.aggregate(
        [{"$group": {"_id": "$email", "n": {"$sum": 1}}}]).to_list(10000)}
    out = []
    for u in users:
        a = act.get(u["id"], {})
        out.append({**u, "activity_count": a.get("n", 0), "last_activity": a.get("last"),
                    "booking_count": bk.get(u["email"], 0), "ticket_count": tk.get(u["id"], 0),
                    "interests_computed": (u.get("interests") or [])[:3]})
    return out


@api_router.get("/admin/clients/{cid}")
async def admin_client_detail(cid: str, admin: dict = Depends(require_admin)):
    u = await db.users.find_one({"id": cid}, {"_id": 0, "password_hash": 0})
    if not u:
        raise HTTPException(status_code=404, detail="Client not found")
    timeline = await db.activity_events.find({"user_id": cid}, {"_id": 0}).sort("created_at", -1).to_list(200)
    bookings = await db.consultations.find({"email": u["email"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    tickets = await db.support_tickets.find({"user_id": cid}, {"_id": 0}).sort("created_at", -1).to_list(100)
    weights = await _topic_weights(cid)
    interests = [{"topic": t, "score": round(s, 2)} for t, s in sorted(weights.items(), key=lambda kv: kv[1], reverse=True)]
    return {"user": u, "timeline": timeline, "bookings": bookings, "tickets": tickets, "interests": interests}


class ClientMetaIn(BaseModel):
    notes: Optional[str] = None
    tags: Optional[List[str]] = None


@api_router.patch("/admin/clients/{cid}")
async def admin_update_client(cid: str, body: ClientMetaIn, admin: dict = Depends(require_admin)):
    upd = {}
    if body.notes is not None:
        upd["notes"] = body.notes
    if body.tags is not None:
        upd["tags"] = [t.strip() for t in body.tags if t and t.strip()]
    if upd:
        res = await db.users.update_one({"id": cid}, {"$set": upd})
        if res.matched_count == 0:
            raise HTTPException(status_code=404, detail="Client not found")
    return {"success": True, **upd}


# ---------------- Chatbot lead capture (into CRM leads) ----------------
class ChatLeadIn(BaseModel):
    name: str
    phone: str
    email: Optional[str] = ""
    message: Optional[str] = ""


@api_router.post("/chat/lead")
async def chat_lead(body: ChatLeadIn):
    lead = {
        "id": str(uuid.uuid4()),
        "name": body.name.strip(),
        "email": (body.email or "").strip(),
        "phone": body.phone.strip(),
        "company": "",
        "area": "Chatbot enquiry",
        "package": "",
        "amount": 0,
        "message": body.message or "",
        "status": "new",
        "source": "ask-sk-chatbot",
        "created_at": now_iso(),
    }
    await db.consultations.insert_one(lead)
    return {"success": True, "id": lead["id"]}


# ---------------- Ticket SLA + auto-escalation ----------------
SLA_HOURS = {"high": 4, "medium": 24, "low": 72}
ESCALATE_NEXT = {"low": "medium", "medium": "high"}


def _ticket_age_hours(t: dict) -> float:
    ts = t.get("created_at") or t.get("updated_at")
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
    except Exception:
        return 0.0


async def _auto_escalate_tickets():
    open_t = await db.support_tickets.find({"status": {"$in": ["open", "in-progress"]}}).to_list(2000)
    for t in open_t:
        pr = t.get("priority", "medium")
        if pr == "high":
            continue
        if _ticket_age_hours(t) > SLA_HOURS.get(pr, 24) and pr in ESCALATE_NEXT:
            # Bump priority WITHOUT touching updated_at (keeps the SLA clock honest).
            await db.support_tickets.update_one({"id": t["id"]}, {"$set": {
                "priority": ESCALATE_NEXT[pr], "auto_escalated": True, "escalated_at": now_iso()}})


@api_router.get("/admin/login-attempts")
async def admin_login_attempts(admin: dict = Depends(require_admin)):
    """Recent failed-login activity so admins can spot brute-force attacks at a glance."""
    docs = await db.login_attempts.find({}, {"_id": 0}).sort("updated_at", -1).to_list(50)
    now = datetime.now(timezone.utc)
    out = []
    locked_now = 0
    for d in docs:
        locked = False
        lu = d.get("locked_until")
        if lu:
            try:
                t = datetime.fromisoformat(lu)
                if t.tzinfo is None:
                    t = t.replace(tzinfo=timezone.utc)
                locked = t > now
            except Exception:
                locked = False
        if locked:
            locked_now += 1
        out.append({
            "ip": d.get("ip", "unknown"),
            "email": d.get("email", ""),
            "recent_fails": d.get("count", 0),
            "total_fails": d.get("fail_total", d.get("count", 0)),
            "locked": locked,
            "locked_until": lu if locked else None,
            "updated_at": d.get("updated_at"),
        })
    return {"attempts": out, "locked_now": locked_now, "max_attempts": LOGIN_MAX_ATTEMPTS,
            "lockout_minutes": LOGIN_LOCKOUT_MINUTES}


class UnlockIn(BaseModel):
    ip: str
    email: str


@api_router.post("/admin/login-attempts/unlock")
async def admin_unlock_login(body: UnlockIn, admin: dict = Depends(require_admin)):
    """Manually clear a lockout / failed-attempt record so a genuine user can sign in again."""
    identifier = f"{body.ip}:{body.email}"
    res = await db.login_attempts.delete_one({"identifier": identifier})
    return {"cleared": res.deleted_count > 0}


@api_router.get("/admin/security")
async def admin_security(admin: dict = Depends(require_admin)):
    """Live threat overview: auto-blocked IPs + recent security alerts for real-time response."""
    now = datetime.now(timezone.utc)
    banned_docs = await db.blocked_ips.find({}, {"_id": 0}).sort("updated_at", -1).to_list(100)
    banned = []
    for d in banned_docs:
        active = False
        try:
            t = datetime.fromisoformat(d.get("banned_until"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            active = t > now
        except Exception:
            active = False
        banned.append({"ip": d.get("ip"), "reason": d.get("reason"), "detail": d.get("detail"),
                       "banned_until": d.get("banned_until"), "active": active, "updated_at": d.get("updated_at")})
    alerts = await db.security_alerts.find({}, {"_id": 0}).sort("created_at", -1).to_list(50)
    unseen = await db.security_alerts.count_documents({"seen": False})

    # 14-day trend of blocked/attack events (exclude info-level like manual unbans).
    all_alerts = await db.security_alerts.find(
        {"severity": {"$in": ["high", "medium"]}}, {"_id": 0, "created_at": 1, "severity": 1}).to_list(5000)
    days = []
    starts = []
    for i in range(13, -1, -1):
        d = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        starts.append(d)
        days.append({"day": d.strftime("%d %b"), "high": 0, "medium": 0, "total": 0})
    for a in all_alerts:
        try:
            ts = datetime.fromisoformat(a["created_at"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        for i, s in enumerate(starts):
            if s <= ts < s + timedelta(days=1):
                sev = a.get("severity", "medium")
                if sev in ("high", "medium"):
                    days[i][sev] += 1
                days[i]["total"] += 1
                break

    return {"banned": banned, "active_bans": sum(1 for b in banned if b["active"]),
            "alerts": alerts, "unseen": unseen, "trend": days,
            "offenders": await _top_offenders(), "networks": _last_networks,
            "countries": _last_countries, "blocked_countries": sorted(await blocked_countries())}


class CountryIn(BaseModel):
    code: str
    country: str = ""


@api_router.post("/admin/security/block-country")
async def admin_block_country(body: CountryIn, request: Request, admin: dict = Depends(require_admin)):
    cc = (body.code or "").upper().strip()
    if len(cc) != 2:
        raise HTTPException(status_code=400, detail="Provide a 2-letter ISO country code")
    codes = await blocked_countries()
    codes.add(cc)
    await db.app_meta.update_one({"_id": "blocked_countries"}, {"$set": {"codes": sorted(codes)}}, upsert=True)
    await raise_security_alert("info", "country_blocked", "-", f"Country blocked: {body.country or cc}", cc)
    await audit(request, admin.get("email"), "block_country", cc, body.country)
    return {"blocked_countries": sorted(codes)}


@api_router.post("/admin/security/unblock-country")
async def admin_unblock_country(body: CountryIn, request: Request, admin: dict = Depends(require_admin)):
    cc = (body.code or "").upper().strip()
    codes = await blocked_countries()
    codes.discard(cc)
    await db.app_meta.update_one({"_id": "blocked_countries"}, {"$set": {"codes": sorted(codes)}}, upsert=True)
    await audit(request, admin.get("email"), "unblock_country", cc)
    return {"blocked_countries": sorted(codes)}


@api_router.get("/admin/audit-log")
async def admin_audit_log(admin: dict = Depends(require_admin)):
    logs = await db.audit_log.find({}, {"_id": 0, "expire_at": 0}).sort("at", -1).to_list(100)
    return {"logs": logs, "retention_days": _audit_retention_days}


@api_router.get("/admin/consent-logs")
async def admin_consent_logs(admin: dict = Depends(require_admin)):
    """Every recorded T&C + Privacy agreement — for super-admin compliance review."""
    logs = await db.consent_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(2000)
    return {"logs": logs, "policy_version": CONSENT_POLICY_VERSION, "total": len(logs)}


@api_router.get("/admin/consent-logs/export")
async def admin_consent_export(admin: dict = Depends(require_admin)):
    import csv as _csv
    import io as _io
    logs = await db.consent_logs.find({}, {"_id": 0}).sort("created_at", -1).to_list(20000)
    buf = _io.StringIO()
    w = _csv.writer(buf)
    w.writerow(["Timestamp (UTC)", "Name", "Email", "Action", "Agreed", "Terms Version", "Privacy Version", "IP", "User Agent"])
    for l in logs:
        w.writerow([l.get("created_at", ""), l.get("name", ""), l.get("email", ""), l.get("action", ""),
                    "Yes" if l.get("agreed") else "No", l.get("terms_version", ""), l.get("privacy_version", ""),
                    l.get("ip", ""), l.get("user_agent", "")])
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=consent-log.csv"})


class PolicyVersionIn(BaseModel):
    version: str


@api_router.get("/admin/policy-version")
async def admin_get_policy_version(admin: dict = Depends(require_admin)):
    total = await db.users.count_documents({})
    current = await db.users.count_documents({"consent.agreed": True, "consent.version": CONSENT_POLICY_VERSION})
    pol = await db.app_meta.find_one({"_id": "policy"}) or {}
    return {"version": CONSENT_POLICY_VERSION, "users_total": total, "users_on_current": current,
            "history": list(reversed(pol.get("history", [])))[:50]}


@api_router.post("/admin/policy-version")
async def admin_set_policy_version(body: PolicyVersionIn, request: Request, admin: dict = Depends(require_admin)):
    """Bump the Terms/Privacy version — every client is prompted to re-agree on their next visit."""
    global CONSENT_POLICY_VERSION
    v = (body.version or "").strip()
    if not v:
        raise HTTPException(status_code=400, detail="Version cannot be empty.")
    entry = {"version": v, "at": now_iso(), "by": admin.get("email", "")}
    CONSENT_POLICY_VERSION = v
    await db.app_meta.update_one({"_id": "policy"},
                                 {"$set": {"version": v, "updated_at": entry["at"]},
                                  "$push": {"history": entry}}, upsert=True)
    await audit(request, admin.get("email"), "policy_version_bumped", v)
    return {"version": v}


class CardStyleIn(BaseModel):
    accent: str


@api_router.get("/admin/card-style")
async def admin_get_card_style(admin: dict = Depends(require_admin)):
    doc = await db.app_meta.find_one({"_id": "card_style"}) or {}
    return {"accent": doc.get("accent", "#C6F135")}


@api_router.post("/admin/card-style")
async def admin_set_card_style(body: CardStyleIn, request: Request, admin: dict = Depends(require_admin)):
    """Set the accent colour used on the auto-generated daily signals share cards."""
    accent = (body.accent or "").strip()
    if not accent.startswith("#") or len(accent) not in (4, 7):
        raise HTTPException(status_code=400, detail="Enter a valid hex colour, e.g. #C6F135.")
    await db.app_meta.update_one({"_id": "card_style"}, {"$set": {"accent": accent}}, upsert=True)
    _og_cache.clear()  # force cards to re-render with the new accent
    await audit(request, admin.get("email"), "card_style_updated", accent)
    return {"accent": accent}


class TestEmailIn(BaseModel):
    to: EmailStr


@api_router.post("/admin/email/test")
async def admin_send_test_email(body: TestEmailIn, admin: dict = Depends(require_admin)):
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return {"sent": False, "skipped": "email_not_configured"}
    res = await asyncio.to_thread(send_test_email, body.to)
    return {"sent": res == "sent", "result": res, "to": body.to}


@api_router.get("/admin/signals-digest/preview", response_class=HTMLResponse)
async def admin_signals_digest_preview(admin: dict = Depends(require_admin)):
    """Render the weekly digest exactly as subscribers would receive it (no send)."""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    signals = await db.signals_archive.find({"date": {"$gte": week_ago}}, {"_id": 0}).sort("date", -1).to_list(14)
    items = _collect_top_signal_items(signals, 6)
    if not items:
        return HTMLResponse('<div style="font-family:Arial;padding:40px;color:#374151;">No Market Signals in the last 7 days yet — the preview will populate as daily signals are generated.</div>')
    html = render_signals_digest_html("there", items, PUBLIC_SITE, PUBLIC_SITE + "/api/newsletter/unsubscribe?token=PREVIEW")
    return HTMLResponse(html)



@api_router.post("/admin/signals-digest/run")
async def admin_run_signals_digest(admin: dict = Depends(require_admin)):
    """Send the weekly Market Signals digest to subscribers now."""
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return {"sent": False, "skipped": "email_not_configured"}
    subs = await db.subscribers.count_documents({})
    await _send_signals_digest()
    return {"sent": True, "subscribers": subs}


@api_router.post("/admin/library-digest/run")
async def admin_run_library_digest(admin: dict = Depends(require_admin)):
    """Send the weekly Library shelf digest to subscribers now."""
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return {"sent": False, "skipped": "email_not_configured"}
    subs = await db.subscribers.count_documents({})
    await _send_library_digest()
    return {"sent": True, "subscribers": subs}


# ---------------- Client self-service: consent record + withdrawal ----------------
@api_router.get("/me/consent")
async def my_consent(user: dict = Depends(get_current_user)):
    """The signed-in user's own consent history + current status (for export)."""
    logs = await db.consent_logs.find({"email": user["email"]}, {"_id": 0}).sort("created_at", -1).to_list(500)
    c = user.get("consent") or {}
    needs_renewal = not (c.get("agreed") and c.get("version") == CONSENT_POLICY_VERSION)
    return {"consent": user.get("consent"), "history": logs, "policy_version": CONSENT_POLICY_VERSION,
            "needs_renewal": needs_renewal}


@api_router.post("/me/consent/withdraw")
async def withdraw_consent(request: Request, user: dict = Depends(get_current_user)):
    """Record a consent withdrawal (does not delete the account; tracking stops on withdrawal)."""
    ts = now_iso()
    await db.consent_logs.insert_one({
        "id": str(uuid.uuid4()), "user_id": user["id"], "email": user["email"], "name": user.get("name", ""),
        "action": "withdraw", "agreed": False, "terms_version": CONSENT_POLICY_VERSION,
        "privacy_version": CONSENT_POLICY_VERSION, "ip": _client_ip(request),
        "user_agent": (request.headers.get("user-agent", "") or "")[:400], "created_at": ts})
    await db.users.update_one({"id": user["id"]}, {"$set": {
        "consent": {"agreed": False, "version": CONSENT_POLICY_VERSION, "at": ts, "action": "withdraw"}}})
    return {"withdrawn": True, "at": ts}


@api_router.post("/me/consent/renew")
async def renew_consent(request: Request, user: dict = Depends(get_current_user)):
    """Re-agree to the current Terms & Privacy version (used by the renewal prompt / after withdrawal)."""
    ts = now_iso()
    await record_consent(request, user["email"], user.get("name", ""), "renew", user_id=user["id"])
    return {"renewed": True, "version": CONSENT_POLICY_VERSION, "at": ts}


class RetentionIn(BaseModel):
    days: int = 90


@api_router.post("/admin/audit-retention")
async def admin_audit_retention(body: RetentionIn, request: Request, admin: dict = Depends(require_admin)):
    global _audit_retention_days
    days = max(1, min(3650, int(body.days)))
    _audit_retention_days = days
    await db.app_meta.update_one({"_id": "audit_retention"}, {"$set": {"days": days}}, upsert=True)
    now = datetime.now(timezone.utc)
    async for d in db.audit_log.find({}, {"_id": 1, "at": 1}):
        try:
            base = datetime.fromisoformat(d["at"])
            if base.tzinfo is None:
                base = base.replace(tzinfo=timezone.utc)
        except Exception:
            base = now
        await db.audit_log.update_one({"_id": d["_id"]}, {"$set": {"expire_at": base + timedelta(days=days)}})
    await audit(request, admin.get("email"), "audit_retention_set", str(days))
    return {"retention_days": days}


# ---------------- Super-Admin Vault (MFA: TOTP + WebAuthn passkey) ----------------
import base64 as _base64
import secrets as _secrets
from cryptography.fernet import Fernet as _Fernet
from webauthn import (generate_registration_options, verify_registration_response,
                      generate_authentication_options, verify_authentication_response,
                      base64url_to_bytes)
from webauthn.helpers import options_to_json
from webauthn.helpers.structs import (AuthenticatorSelectionCriteria, AuthenticatorAttachment,
                                      ResidentKeyRequirement, UserVerificationRequirement,
                                      PublicKeyCredentialDescriptor)

_ENC_KEY = os.environ.get("ENCRYPTION_KEY", "")
_fernet = _Fernet(_ENC_KEY.encode()) if _ENC_KEY else None
WEBAUTHN_RP_ID = os.environ.get("WEBAUTHN_RP_ID", "")
WEBAUTHN_ORIGIN = os.environ.get("WEBAUTHN_ORIGIN", "")
WEBAUTHN_RP_NAME = os.environ.get("WEBAUTHN_RP_NAME", "Super Admin")
VAULT_TTL = 300  # unlock capability lifetime, seconds


def _enc(s: str) -> str:
    return _fernet.encrypt(s.encode()).decode()


def _dec(s: str) -> str:
    return _fernet.decrypt(s.encode()).decode()


def _b64u(b: bytes) -> str:
    return _base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _issue_vault_jwt(email: str, stage: str) -> str:
    return pyjwt.encode({"purpose": "vault", "stage": stage, "email": email,
                         "exp": datetime.now(timezone.utc) + timedelta(seconds=VAULT_TTL)},
                        get_jwt_secret(), algorithm="HS256")


def _read_vault_jwt(token, stage: str):
    if not token:
        return None
    try:
        d = pyjwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        if d.get("purpose") == "vault" and d.get("stage") == stage:
            return d.get("email")
    except Exception:
        return None
    return None


async def require_vault_unlocked(request: Request, admin: dict = Depends(require_admin)):
    if _read_vault_jwt(request.cookies.get("vault_unlock"), "unlocked") != admin.get("email"):
        raise HTTPException(status_code=403, detail="Vault locked — complete MFA to unlock.")
    return admin


class VaultCodeIn(BaseModel):
    code: str = ""


class VaultKeyIn(BaseModel):
    label: str
    value: str


class WACredIn(BaseModel):
    id: str
    rawId: str = ""
    response: dict
    type: str = "public-key"
    clientExtensionResults: dict = {}
    authenticatorAttachment: Optional[str] = None


def _vault_seconds_left(token) -> int:
    if not token:
        return 0
    try:
        d = pyjwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        if d.get("purpose") == "vault" and d.get("stage") == "unlocked":
            return max(0, int(d["exp"] - datetime.now(timezone.utc).timestamp()))
    except Exception:
        return 0
    return 0


# ---------------- Vault unlock lockout (anti-brute-force on MFA) ----------------
VAULT_MAX_FAILS = 5
VAULT_LOCK_MINUTES = 15


async def _vault_lock_state(email: str):
    """Return (locked, seconds_left, fails) for this super-admin's vault unlocking."""
    doc = await db.vault_lockouts.find_one({"email": email})
    if not doc:
        return (False, 0, 0)
    lu = doc.get("locked_until")
    if lu:
        try:
            t = datetime.fromisoformat(lu)
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            secs = int((t - datetime.now(timezone.utc)).total_seconds())
            if secs > 0:
                return (True, secs, doc.get("fails", 0))
        except Exception:
            pass
    return (False, 0, doc.get("fails", 0))


async def check_vault_lockout(email: str):
    locked, secs, _ = await _vault_lock_state(email)
    if locked:
        raise HTTPException(status_code=429,
                            detail=f"Too many failed attempts. Vault unlocking is frozen — try again in {max(1, secs // 60)} minute(s).",
                            headers={"Retry-After": str(secs)})


async def register_vault_fail(email: str, request: Request, kind: str):
    doc = await db.vault_lockouts.find_one({"email": email})
    fails = (doc or {}).get("fails", 0) + 1
    update = {"email": email, "fails": fails, "updated_at": now_iso()}
    frozen = False
    if fails >= VAULT_MAX_FAILS:
        update["locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=VAULT_LOCK_MINUTES)).isoformat()
        update["fails"] = 0
        frozen = True
    await db.vault_lockouts.update_one({"email": email}, {"$set": update}, upsert=True)
    if frozen:
        await audit(request, email, "vault_lockout_frozen", email, meta=f"{VAULT_LOCK_MINUTES}m after {VAULT_MAX_FAILS} fails")
        await raise_security_alert("high", "vault_lockout", _client_ip(request),
                                   "Vault unlocking frozen after repeated failed attempts",
                                   f"{email} frozen for {VAULT_LOCK_MINUTES} min ({kind})", email=email)


async def clear_vault_fails(email: str):
    await db.vault_lockouts.delete_one({"email": email})


@api_router.get("/admin/vault/status")
async def vault_status(request: Request, admin: dict = Depends(require_admin)):
    email = admin.get("email")
    mfa = await db.superadmin_mfa.find_one({"email": email})
    pk = await db.webauthn_credentials.count_documents({"user_id": email})
    left = _vault_seconds_left(request.cookies.get("vault_unlock")) if _read_vault_jwt(request.cookies.get("vault_unlock"), "unlocked") == email else 0
    last = await db.audit_log.find_one({"action": "vault_unlocked"}, sort=[("at", -1)], projection={"_id": 0, "actor": 1, "ip": 1, "at": 1})
    lock_frozen, lock_secs, lock_fails = await _vault_lock_state(email)
    return {"totp_enrolled": bool(mfa and mfa.get("totp_enrolled")),
            "passkey_enrolled": pk > 0,
            "unlocked": left > 0,
            "unlock_seconds_left": left,
            "last_unlock": last,
            "lock_frozen": lock_frozen,
            "lock_seconds_left": lock_secs,
            "fails": lock_fails,
            "max_fails": VAULT_MAX_FAILS,
            "ready": bool(_fernet and WEBAUTHN_RP_ID),
            "key_count": await db.vault_secrets.count_documents({})}


@api_router.post("/admin/vault/enroll/totp")
async def vault_enroll_totp(admin: dict = Depends(require_admin)):
    email = admin.get("email")
    secret = pyotp.random_base32()
    await db.superadmin_mfa.update_one({"email": email}, {"$set": {
        "email": email, "totp_secret_enc": _enc(secret), "totp_enrolled": False}}, upsert=True)
    uri = pyotp.TOTP(secret).provisioning_uri(name=email, issuer_name=WEBAUTHN_RP_NAME)
    import io as _io, qrcode as _qr
    img = _qr.make(uri)
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    return {"otpauth_uri": uri, "qr": "data:image/png;base64," + _base64.b64encode(buf.getvalue()).decode(),
            "secret": secret}


@api_router.post("/admin/vault/enroll/totp/verify")
async def vault_enroll_totp_verify(body: VaultCodeIn, admin: dict = Depends(require_admin)):
    email = admin.get("email")
    mfa = await db.superadmin_mfa.find_one({"email": email})
    if not mfa or not mfa.get("totp_secret_enc"):
        raise HTTPException(status_code=400, detail="Start enrollment first")
    if not pyotp.TOTP(_dec(mfa["totp_secret_enc"])).verify(body.code, valid_window=1):
        raise HTTPException(status_code=401, detail="Invalid code")
    await db.superadmin_mfa.update_one({"email": email}, {"$set": {"totp_enrolled": True}})
    return {"enrolled": True}


@api_router.post("/admin/vault/unlock/totp")
async def vault_unlock_totp(body: VaultCodeIn, request: Request, response: Response, admin: dict = Depends(require_admin)):
    email = admin.get("email")
    await check_vault_lockout(email)
    mfa = await db.superadmin_mfa.find_one({"email": email})
    if not mfa or not mfa.get("totp_enrolled"):
        raise HTTPException(status_code=400, detail="Enroll authenticator first")
    if not pyotp.TOTP(_dec(mfa["totp_secret_enc"])).verify(body.code, valid_window=1):
        await register_vault_fail(email, request, "wrong authenticator code")
        await audit(request, email, "vault_totp_fail")
        await raise_security_alert("high", "vault_unlock_failed", _client_ip(request),
                                   "Failed vault unlock (wrong authenticator code)", email, email=email)
        raise HTTPException(status_code=401, detail="Invalid authenticator code")
    response.set_cookie("vault_totp", _issue_vault_jwt(email, "totp"), httponly=True, secure=True,
                        samesite="none", path="/", max_age=VAULT_TTL)
    return {"stage": "totp_ok",
            "passkey_required": await db.webauthn_credentials.count_documents({"user_id": email}) > 0}


def _ceremony_valid(cer) -> bool:
    return bool(cer) and cer.get("exp", 0) >= datetime.now(timezone.utc).timestamp()


@api_router.post("/admin/vault/webauthn/register/options")
async def vault_wa_reg_options(admin: dict = Depends(require_admin)):
    if not WEBAUTHN_RP_ID:
        raise HTTPException(status_code=400, detail="WebAuthn not configured")
    email = admin.get("email")
    rows = await db.webauthn_credentials.find({"user_id": email}, {"credential_id": 1}).to_list(50)
    existing = [PublicKeyCredentialDescriptor(id=base64url_to_bytes(x["credential_id"])) for x in rows]
    options = generate_registration_options(
        rp_id=WEBAUTHN_RP_ID, rp_name=WEBAUTHN_RP_NAME, user_name=email, user_id=email.encode(),
        challenge=_secrets.token_bytes(32),
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            resident_key=ResidentKeyRequirement.PREFERRED,
            user_verification=UserVerificationRequirement.REQUIRED),
        exclude_credentials=existing)
    await db.webauthn_ceremonies.update_one({"email": email, "kind": "reg"}, {"$set": {
        "email": email, "kind": "reg", "challenge": _b64u(options.challenge),
        "exp": (datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()}}, upsert=True)
    return json.loads(options_to_json(options))


@api_router.post("/admin/vault/webauthn/register/verify")
async def vault_wa_reg_verify(payload: WACredIn, request: Request, admin: dict = Depends(require_admin)):
    email = admin.get("email")
    cer = await db.webauthn_ceremonies.find_one_and_delete({"email": email, "kind": "reg"})
    if not _ceremony_valid(cer):
        raise HTTPException(status_code=400, detail="Ceremony expired")
    try:
        v = verify_registration_response(
            credential=payload.model_dump(), expected_challenge=base64url_to_bytes(cer["challenge"]),
            expected_rp_id=WEBAUTHN_RP_ID, expected_origin=WEBAUTHN_ORIGIN, require_user_verification=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Passkey registration failed: {e}")
    await db.webauthn_credentials.update_one({"credential_id": _b64u(v.credential_id)}, {"$set": {
        "user_id": email, "credential_id": _b64u(v.credential_id),
        "public_key": _b64u(v.credential_public_key), "sign_count": v.sign_count,
        "created_at": now_iso()}}, upsert=True)
    await audit(request, email, "vault_passkey_registered")
    return {"ok": True}


@api_router.post("/admin/vault/webauthn/auth/options")
async def vault_wa_auth_options(request: Request, admin: dict = Depends(require_admin)):
    email = admin.get("email")
    if _read_vault_jwt(request.cookies.get("vault_totp"), "totp") != email:
        raise HTTPException(status_code=403, detail="Enter authenticator code first")
    rows = await db.webauthn_credentials.find({"user_id": email}).to_list(50)
    if not rows:
        raise HTTPException(status_code=400, detail="No passkey registered")
    options = generate_authentication_options(
        rp_id=WEBAUTHN_RP_ID, challenge=_secrets.token_bytes(32),
        user_verification=UserVerificationRequirement.REQUIRED,
        allow_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(r["credential_id"])) for r in rows])
    await db.webauthn_ceremonies.update_one({"email": email, "kind": "auth"}, {"$set": {
        "email": email, "kind": "auth", "challenge": _b64u(options.challenge),
        "exp": (datetime.now(timezone.utc) + timedelta(minutes=5)).timestamp()}}, upsert=True)
    return json.loads(options_to_json(options))


@api_router.post("/admin/vault/webauthn/auth/verify")
async def vault_wa_auth_verify(payload: WACredIn, request: Request, response: Response, admin: dict = Depends(require_admin)):
    email = admin.get("email")
    await check_vault_lockout(email)
    if _read_vault_jwt(request.cookies.get("vault_totp"), "totp") != email:
        raise HTTPException(status_code=403, detail="Enter authenticator code first")
    cer = await db.webauthn_ceremonies.find_one_and_delete({"email": email, "kind": "auth"})
    if not _ceremony_valid(cer):
        raise HTTPException(status_code=400, detail="Ceremony expired")
    row = await db.webauthn_credentials.find_one({"user_id": email, "credential_id": payload.id})
    if not row:
        raise HTTPException(status_code=400, detail="Unknown passkey")
    try:
        v = verify_authentication_response(
            credential=payload.model_dump(), expected_challenge=base64url_to_bytes(cer["challenge"]),
            expected_rp_id=WEBAUTHN_RP_ID, expected_origin=WEBAUTHN_ORIGIN,
            credential_public_key=base64url_to_bytes(row["public_key"]),
            credential_current_sign_count=row["sign_count"], require_user_verification=True)
    except Exception as e:
        await register_vault_fail(email, request, "passkey rejected")
        await audit(request, email, "vault_passkey_fail")
        await raise_security_alert("high", "vault_unlock_failed", _client_ip(request),
                                   "Failed vault unlock (passkey rejected)", email, email=email)
        raise HTTPException(status_code=400, detail=f"Passkey authentication failed: {e}")
    await db.webauthn_credentials.update_one({"_id": row["_id"]}, {"$set": {"sign_count": v.new_sign_count}})
    await clear_vault_fails(email)
    response.set_cookie("vault_unlock", _issue_vault_jwt(email, "unlocked"), httponly=True, secure=True,
                        samesite="none", path="/", max_age=VAULT_TTL)
    response.delete_cookie("vault_totp", path="/")
    await audit(request, email, "vault_unlocked")
    return {"vault_unlocked": True}


@api_router.post("/admin/vault/lock")
async def vault_lock(response: Response, admin: dict = Depends(require_admin)):
    response.delete_cookie("vault_unlock", path="/")
    return {"locked": True}


@api_router.get("/admin/vault/keys")
async def vault_keys(admin: dict = Depends(require_vault_unlocked)):
    docs = await db.vault_secrets.find({}, {"_id": 0}).sort("label", 1).to_list(200)
    return {"keys": [{"id": d["id"], "label": d["label"], "value": _dec(d["value_enc"]),
                      "updated_at": d.get("updated_at")} for d in docs]}


@api_router.post("/admin/vault/keys")
async def vault_add_key(body: VaultKeyIn, request: Request, admin: dict = Depends(require_vault_unlocked)):
    vid = str(uuid.uuid4())
    await db.vault_secrets.insert_one({"id": vid, "label": body.label,
                                       "value_enc": _enc(body.value), "updated_at": now_iso()})
    await audit(request, admin.get("email"), "vault_add_key", body.label)
    return {"id": vid}


@api_router.delete("/admin/vault/keys/{vid}")
async def vault_del_key(vid: str, request: Request, admin: dict = Depends(require_vault_unlocked)):
    await db.vault_secrets.delete_one({"id": vid})
    await audit(request, admin.get("email"), "vault_del_key", vid)
    return {"deleted": True}


_last_networks = []
_last_countries = []


async def _top_offenders():
    """Rank the IPs probing us most, with best-effort country + /24 network grouping."""
    global _last_networks, _last_countries
    events = await db.security_alerts.find(
        {"severity": {"$in": ["high", "medium"]}},
        {"_id": 0, "ip": 1, "reason": 1, "created_at": 1}).to_list(5000)
    by_ip = {}
    for e in events:
        ip = e.get("ip") or "unknown"
        if ip == "unknown":
            continue
        d = by_ip.setdefault(ip, {"ip": ip, "count": 0, "last": "", "reasons": set()})
        d["count"] += 1
        if (e.get("created_at") or "") > d["last"]:
            d["last"] = e.get("created_at")
        if e.get("reason"):
            d["reasons"].add(e["reason"])
    offenders = sorted(by_ip.values(), key=lambda x: x["count"], reverse=True)[:10]
    net_counts, country_counts = {}, {}
    out = []
    for o in offenders:
        country, cc = await lookup_country(o["ip"])
        subnet = _subnet24(o["ip"])
        net_counts[subnet] = net_counts.get(subnet, 0) + o["count"]
        country_counts[country] = country_counts.get(country, 0) + o["count"]
        out.append({
            "ip": o["ip"], "count": o["count"], "last": o["last"],
            "reasons": sorted(o["reasons"]), "country": country, "cc": cc, "subnet": subnet,
            "banned": await is_ip_banned(o["ip"]),
        })
    _last_networks = sorted(
        [{"subnet": s, "count": c, "banned": s in _banned_cidrs} for s, c in net_counts.items() if s],
        key=lambda x: x["count"], reverse=True)[:6]
    _last_countries = sorted(
        [{"country": c, "count": n} for c, n in country_counts.items()],
        key=lambda x: x["count"], reverse=True)[:6]
    return out


class BanIn(BaseModel):
    ip: str


@api_router.post("/admin/security/ban")
async def admin_security_ban(body: BanIn, request: Request, admin: dict = Depends(require_admin)):
    """Immediately block a single offending IP."""
    await _apply_block(body.ip, "ip", "Blocked by admin", "Manual block", severity="high", alert=False)
    await raise_security_alert("high", "ip_banned", body.ip, "Blocked by admin", "Manual block")
    await audit(request, admin.get("email"), "ban_ip", body.ip)
    return {"banned": True}


class CidrIn(BaseModel):
    subnet: str


@api_router.post("/admin/security/ban-range")
async def admin_security_ban_range(body: CidrIn, request: Request, admin: dict = Depends(require_admin)):
    """Block a whole /24 (or CIDR) range where an attack emerges from."""
    try:
        _ipaddr.ip_network(body.subnet, strict=False)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid IP range / CIDR")
    await _apply_block(body.subnet, "cidr", "Range blocked by admin",
                       f"Network {body.subnet}", severity="high", alert=False)
    await raise_security_alert("high", "cidr_banned", body.subnet, "Range blocked by admin", f"Network {body.subnet}")
    await audit(request, admin.get("email"), "ban_range", body.subnet)
    return {"banned": True}





@api_router.post("/admin/security/seen")
async def admin_security_seen(admin: dict = Depends(require_admin)):
    await db.security_alerts.update_many({"seen": False}, {"$set": {"seen": True}})
    return {"ok": True}


class UnbanIn(BaseModel):
    ip: str


@api_router.post("/admin/security/unban")
async def admin_security_unban(body: UnbanIn, request: Request, admin: dict = Depends(require_admin)):
    """Lift an IP or range ban (false positive) and clear related failed-login records."""
    _banned_ips.pop(body.ip, None)
    _banned_cidrs.pop(body.ip, None)
    await db.blocked_ips.delete_one({"ip": body.ip})
    await db.login_attempts.delete_many({"ip": body.ip})
    await raise_security_alert("info", "ip_unbanned", body.ip, "Ban lifted by admin", "Manual override")
    await audit(request, admin.get("email"), "unban", body.ip)
    return {"unbanned": True}


class VpnVerifyIn(BaseModel):
    code: str = ""


@api_router.get("/vpn/status")
async def vpn_status(request: Request):
    cblk, country, _cc = await country_should_block(request)
    if cblk:
        return {"blocked": True, "enabled": True, "reason": "country", "country": country}
    if not await vpn_guard_enabled():
        return {"blocked": False, "enabled": False}
    ip = _client_ip(request)
    if ip in await vpn_allowlist():
        return {"blocked": False, "enabled": True, "reason": "allowlist"}
    if _verify_vpn_totp_cookie(request.cookies.get("vpn_totp")):
        return {"blocked": False, "enabled": True, "reason": "verified"}
    d = await detect_vpn(ip)
    return {"blocked": d["flagged"], "enabled": True, "ip": ip, "detection": d}


@api_router.post("/vpn/verify")
async def vpn_verify(body: VpnVerifyIn, response: Response):
    if not await _totp_matches(body.code):
        raise HTTPException(status_code=401, detail="Invalid or expired access code.")
    response.set_cookie("vpn_totp", _issue_vpn_totp_cookie(), httponly=True, secure=True,
                        samesite="none", path="/", max_age=VPN_TOTP_TTL_HOURS * 3600)
    return {"verified": True}


class VpnToggleIn(BaseModel):
    enabled: bool = False


class VpnAllowlistIn(BaseModel):
    ips: List[str] = []


class VpnTokenIn(BaseModel):
    label: str = ""


@api_router.get("/admin/vpn-guard")
async def admin_vpn_guard_get(admin: dict = Depends(require_admin)):
    tokens = await db.trusted_totp.find({}, {"_id": 0, "id": 1, "label": 1, "enabled": 1, "created_at": 1}).to_list(100)
    return {"enabled": await vpn_guard_enabled(), "allowlist": await vpn_allowlist(),
            "tokens": tokens, "provider_configured": bool(VPNAPI_KEY or IPQS_API_KEY)}


@api_router.post("/admin/vpn-guard/toggle")
async def admin_vpn_guard_toggle(body: VpnToggleIn, request: Request, admin: dict = Depends(require_admin)):
    await db.app_meta.update_one({"_id": "vpn_guard"}, {"$set": {"enabled": bool(body.enabled)}}, upsert=True)
    await audit(request, admin.get("email"), "vpn_guard_toggle", str(bool(body.enabled)))
    return {"enabled": bool(body.enabled)}


@api_router.post("/admin/vpn-guard/allowlist")
async def admin_vpn_guard_allowlist(body: VpnAllowlistIn, admin: dict = Depends(require_admin)):
    ips = [i.strip() for i in body.ips if i.strip()]
    await db.app_meta.update_one({"_id": "vpn_allowlist"}, {"$set": {"ips": ips}}, upsert=True)
    return {"ips": ips}


@api_router.post("/admin/vpn-guard/token")
async def admin_vpn_guard_token(body: VpnTokenIn, admin: dict = Depends(require_admin)):
    secret = pyotp.random_base32()
    tid = str(uuid.uuid4())
    label = body.label or "Trusted token"
    await db.trusted_totp.insert_one({"id": tid, "label": label, "secret": secret,
                                      "enabled": True, "created_at": now_iso()})
    uri = pyotp.TOTP(secret).provisioning_uri(name=label, issuer_name="Sudarshan Karweer")
    import io as _io, base64 as _b64, qrcode as _qr
    img = _qr.make(uri)
    buf = _io.BytesIO()
    img.save(buf, format="PNG")
    qr = "data:image/png;base64," + _b64.b64encode(buf.getvalue()).decode()
    return {"id": tid, "label": label, "otpauth_uri": uri, "qr": qr, "secret": secret}


@api_router.delete("/admin/vpn-guard/token/{tid}")
async def admin_vpn_guard_token_del(tid: str, admin: dict = Depends(require_admin)):
    await db.trusted_totp.delete_one({"id": tid})
    return {"deleted": True}


@api_router.get("/admin/lead-analytics")
async def admin_lead_analytics(period: str = "8w", admin: dict = Depends(require_admin)):
    """Lead volume by source over a selectable period, plus per-source conversion."""
    leads = await db.consultations.find({}, {"_id": 0, "source": 1, "created_at": 1, "status": 1, "amount": 1}).to_list(10000)
    now = datetime.now(timezone.utc)
    SOURCES = ["booking-form", "ask-sk-chatbot", "consultation-checkout", "whatsapp", "other"]
    PAID_STATUSES = {"paid", "won", "scheduled"}

    # Build time buckets by period.
    buckets, labels = [], []
    if period == "12m":
        granularity = "monthly"
        first = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        starts = []
        y, m = first.year, first.month
        for _ in range(12):
            starts.append(datetime(y, m, 1, tzinfo=timezone.utc))
            m -= 1
            if m == 0:
                m = 12; y -= 1
        starts.reverse()
        for i, s in enumerate(starts):
            end = starts[i + 1] if i + 1 < len(starts) else (now + timedelta(days=1))
            buckets.append((s, end)); labels.append(s.strftime("%b %y"))
    else:
        n = 13 if period == "3m" else 8
        granularity = "weekly"
        for i in range(n - 1, -1, -1):
            s = (now - timedelta(days=now.weekday() + 7 * i)).replace(hour=0, minute=0, second=0, microsecond=0)
            buckets.append((s, s + timedelta(days=7))); labels.append(s.strftime("%d %b"))

    rows = [{"week": labels[i], **{s: 0 for s in SOURCES}} for i in range(len(buckets))]
    rev_rows = [{"week": labels[i], **{s: 0 for s in SOURCES}} for i in range(len(buckets))]
    conversion = {s: {"total": 0, "paid": 0, "revenue": 0} for s in SOURCES}
    for l in leads:
        src = l.get("source") or "other"
        if src not in SOURCES:
            src = "other"
        conversion[src]["total"] += 1
        try:
            amt = int(l.get("amount") or 0)
        except Exception:
            amt = 0
        is_paid = l.get("status") in PAID_STATUSES
        if is_paid:
            conversion[src]["paid"] += 1
            conversion[src]["revenue"] += amt
        try:
            ts = datetime.fromisoformat(l["created_at"])
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            continue
        for i, (bs, be) in enumerate(buckets):
            if bs <= ts < be:
                rows[i][src] += 1
                if is_paid:
                    rev_rows[i][src] += amt
                break
    for s in SOURCES:
        t = conversion[s]["total"]
        conversion[s]["rate"] = round(100 * conversion[s]["paid"] / t) if t else 0
    totals = {s: sum(r[s] for r in rows) for s in SOURCES}
    ranked = sorted(
        [{"source": s, **conversion[s]} for s in SOURCES if conversion[s]["total"] > 0],
        key=lambda x: (x["revenue"], x["paid"]), reverse=True)

    # Revenue by consultation package + current-month revenue vs goal.
    packages, month_rev = {}, 0
    month_prefix = now.strftime("%Y-%m")
    for l in leads:
        if l.get("status") not in PAID_STATUSES:
            continue
        try:
            amt = int(l.get("amount") or 0)
        except Exception:
            amt = 0
        pkg = l.get("package") or "Custom / Direct"
        packages[pkg] = packages.get(pkg, 0) + amt
        if (l.get("created_at") or "")[:7] == month_prefix:
            month_rev += amt
    packages_ranked = sorted(
        [{"package": p, "revenue": v} for p, v in packages.items() if v > 0],
        key=lambda x: x["revenue"], reverse=True)
    goal_doc = await db.app_meta.find_one({"_id": "revenue_goal"})
    goal = (goal_doc or {}).get("target", 0)

    return {"weeks": rows, "revenue": rev_rows, "sources": SOURCES, "totals": totals,
            "granularity": granularity, "period": period, "conversion": conversion, "ranked": ranked,
            "packages": packages_ranked, "month_revenue": month_rev, "revenue_goal": goal,
            "month_label": now.strftime("%B %Y")}


class RevenueGoalIn(BaseModel):
    target: int = 0


@api_router.post("/admin/revenue-goal")
async def set_revenue_goal(body: RevenueGoalIn, admin: dict = Depends(require_admin)):
    await db.app_meta.update_one({"_id": "revenue_goal"}, {"$set": {"target": max(0, body.target)}}, upsert=True)
    return {"target": max(0, body.target)}


@api_router.get("/admin/lead-analytics/export")
async def admin_lead_analytics_export(admin: dict = Depends(require_admin)):
    csv = await _analytics_csv()
    return Response(content=csv, media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=lead-source-analytics.csv"})


async def _analytics_csv() -> str:
    leads = await db.consultations.find({}, {"_id": 0, "source": 1, "status": 1, "amount": 1}).to_list(10000)
    SOURCES = ["booking-form", "ask-sk-chatbot", "consultation-checkout", "whatsapp", "other"]
    LABELS = {"booking-form": "Booking Form", "ask-sk-chatbot": "Ask SK Bot",
              "consultation-checkout": "Checkout", "whatsapp": "WhatsApp", "other": "Other"}
    PAID_STATUSES = {"paid", "won", "scheduled"}
    agg = {s: {"total": 0, "paid": 0, "revenue": 0} for s in SOURCES}
    for l in leads:
        src = l.get("source") or "other"
        if src not in SOURCES:
            src = "other"
        agg[src]["total"] += 1
        if l.get("status") in PAID_STATUSES:
            agg[src]["paid"] += 1
            try:
                agg[src]["revenue"] += int(l.get("amount") or 0)
            except Exception:
                pass
    lines = ["Source,Total Leads,Paid,Conversion %,Revenue"]
    for s in sorted(SOURCES, key=lambda x: (agg[x]["revenue"], agg[x]["paid"]), reverse=True):
        a = agg[s]
        if a["total"] == 0:
            continue
        rate = round(100 * a["paid"] / a["total"]) if a["total"] else 0
        lines.append(f'{LABELS[s]},{a["total"]},{a["paid"]},{rate},{a["revenue"]}')
    return "\r\n".join(lines) + "\r\n"


async def _send_monthly_report():
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return {"sent": False, "skipped": "email_not_configured"}
    from emailer import send_report_email
    csv = await _analytics_csv()
    to = os.environ.get("BOOKING_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
    loop = asyncio.get_event_loop()
    res = await loop.run_in_executor(None, lambda: send_report_email(to, csv))
    await db.app_meta.update_one({"_id": "report"}, {"$set": {"last_run": now_iso()}}, upsert=True)
    return {"sent": res == "sent", "to": to}


@api_router.post("/admin/report/run")
async def admin_run_report(admin: dict = Depends(require_admin)):
    return await _send_monthly_report()


# ---------------- Service Desk (tickets) ----------------
class TicketIn(BaseModel):
    subject: str
    message: str
    category: Optional[str] = "General"
    priority: Optional[str] = "medium"


class TicketReplyIn(BaseModel):
    message: str


class TicketUpdateIn(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None


@api_router.post("/tickets")
async def create_ticket(body: TicketIn, user: dict = Depends(get_current_user)):
    tid = str(uuid.uuid4())
    doc = {"id": tid, "ticket_code": "TK-" + uuid.uuid4().hex[:6].upper(), "user_id": user["id"],
           "client_code": user.get("client_code", ""), "name": user.get("name"), "email": user["email"],
           "subject": body.subject, "message": body.message, "category": body.category,
           "priority": body.priority, "status": "open", "replies": [],
           "created_at": now_iso(), "updated_at": now_iso()}
    await db.support_tickets.insert_one(doc)
    doc.pop("_id", None)
    try:
        from emailer import send_ticket_alert_email
        admin_to = os.environ.get("BOOKING_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
        asyncio.get_event_loop().run_in_executor(None, lambda: send_ticket_alert_email(admin_to, doc))
    except Exception:
        logger.exception("ticket alert scheduling failed")
    return doc


@api_router.get("/tickets")
async def my_tickets(user: dict = Depends(get_current_user)):
    return await db.support_tickets.find({"user_id": user["id"]}, {"_id": 0}).sort("updated_at", -1).to_list(200)


@api_router.post("/tickets/{tid}/reply")
async def reply_ticket(tid: str, body: TicketReplyIn, user: dict = Depends(get_current_user)):
    t = await db.support_tickets.find_one({"id": tid})
    if not t or (t["user_id"] != user["id"] and user.get("role") != "admin"):
        raise HTTPException(status_code=404, detail="Ticket not found")
    is_admin = user.get("role") == "admin"
    reply = {"by": user.get("name") or user["email"], "role": "admin" if is_admin else "client",
             "message": body.message, "at": now_iso()}
    new_status = "in-progress" if is_admin else "open"
    await db.support_tickets.update_one({"id": tid}, {"$push": {"replies": reply},
                                                      "$set": {"updated_at": now_iso(), "status": new_status}})
    return {"success": True, "reply": reply}


@api_router.get("/admin/tickets")
async def admin_tickets(status: Optional[str] = None, admin: dict = Depends(require_admin)):
    await _auto_escalate_tickets()
    q = {"status": status} if status else {}
    return await db.support_tickets.find(q, {"_id": 0}).sort("updated_at", -1).to_list(500)


@api_router.patch("/admin/tickets/{tid}")
async def admin_update_ticket(tid: str, body: TicketUpdateIn, admin: dict = Depends(require_admin)):
    upd = {"updated_at": now_iso()}
    if body.status:
        upd["status"] = body.status
    if body.priority:
        upd["priority"] = body.priority
    res = await db.support_tickets.update_one({"id": tid}, {"$set": upd})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return {"success": True}


# ---------------- GDPR data rights ----------------
@api_router.get("/me/data")
async def export_my_data(user: dict = Depends(get_current_user)):
    acts = await db.activity_events.find({"user_id": user["id"]}, {"_id": 0}).to_list(3000)
    bookings = await db.consultations.find({"email": user["email"]}, {"_id": 0}).to_list(500)
    tickets = await db.support_tickets.find({"user_id": user["id"]}, {"_id": 0}).to_list(500)
    return {"profile": user, "activity": acts, "bookings": bookings, "tickets": tickets, "exported_at": now_iso()}


@api_router.delete("/me")
async def delete_my_account(response: Response, user: dict = Depends(get_current_user)):
    if user.get("role") == "admin":
        raise HTTPException(status_code=400, detail="Admin accounts cannot be self-deleted")
    uid, email = user["id"], user["email"]
    await db.activity_events.delete_many({"user_id": uid})
    await db.support_tickets.delete_many({"user_id": uid})
    await db.user_sessions.delete_many({"user_id": uid})
    await db.consultations.delete_many({"email": email})
    await db.subscribers.delete_many({"email": email})
    await db.users.delete_one({"id": uid})
    response.delete_cookie("session_token", path="/")
    return {"deleted": True}


# ---------------- Weekly digest ----------------
async def _send_weekly_digest():
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return {"sent": 0, "skipped": "email_not_configured"}
    from emailer import send_digest_email
    clients = await db.users.find({"role": "client"}, {"_id": 0, "password_hash": 0}).to_list(5000)
    loop = asyncio.get_event_loop()
    sent = 0
    for c in clients:
        weights = await _topic_weights(c["id"])
        vids = await loop.run_in_executor(None, lambda w=weights: curator.recommended(w, 5))
        if not vids:
            continue
        res = await loop.run_in_executor(None, lambda cc=c, vv=vids: send_digest_email(cc["email"], cc.get("name", "there"), vv))
        if res == "sent":
            sent += 1
    await db.app_meta.update_one({"_id": "digest"}, {"$set": {"last_run": now_iso()}}, upsert=True)
    return {"sent": sent, "total": len(clients)}


@api_router.post("/admin/digest/run")
async def admin_run_digest(admin: dict = Depends(require_admin)):
    return await _send_weekly_digest()


def _collect_top_signal_items(signals: list, limit: int = 6) -> list:
    """Flatten recent daily feeds into a de-duplicated set of the best items."""
    seen, items = set(), []
    for s in signals:
        for f in s.get("feed", []):
            key = (f.get("title") or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            items.append({"title": f.get("title", ""), "take": f.get("take", ""), "tag": f.get("tag", "")})
    return items[:limit]


async def _send_signals_digest():
    """Email newsletter subscribers a weekly round-up of the best Market Signals."""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).date().isoformat()
    signals = await db.signals_archive.find(
        {"date": {"$gte": week_ago}}, {"_id": 0}).sort("date", -1).to_list(14)
    items = _collect_top_signal_items(signals, 6)
    if not items:
        return
    subs = await db.subscribers.find({}, {"_id": 0, "email": 1, "name": 1}).to_list(5000)
    loop = asyncio.get_event_loop()
    for c in subs:
        await loop.run_in_executor(None, lambda cc=c: send_signals_digest_email(
            cc["email"], cc.get("name", "there"), items, unsubscribe_url=_unsub_url(cc["email"])))
    await db.app_meta.update_one({"_id": "signals_digest"}, {"$set": {"last_run": now_iso()}}, upsert=True)


async def _send_library_digest():
    """Email subscribers the fresh weekly Library shelf (today's rotation)."""
    books = [_book_public(b) for b in _daily_shelf()]
    if not books:
        return
    subs = await db.subscribers.find({}, {"_id": 0, "email": 1, "name": 1}).to_list(5000)
    loop = asyncio.get_event_loop()
    for c in subs:
        await loop.run_in_executor(None, lambda cc=c: send_library_digest_email(
            cc["email"], cc.get("name", "there"), books, PUBLIC_SITE, _unsub_url(cc["email"])))
    await db.app_meta.update_one({"_id": "library_digest"}, {"$set": {"last_run": now_iso()}}, upsert=True)


async def _digest_scheduler():
    while True:
        try:
            await _auto_escalate_tickets()  # hourly SLA escalation pass
            await _refresh_all_news_if_due()  # 4-hourly news scrape for sectors/agencies/OEMs
            await _process_pending_payments()  # nudge abandoned checkouts, release stale holds
            await _refresh_home_content()   # daily AI homepage copy (self-guards on 24h staleness)
            # Dynamic Insights: blogs refresh on a 7-day cadence; prior editions go to the archive.
            imeta = await db.app_meta.find_one({"_id": "insights_refresh"}) or {}
            _today = datetime.now(timezone.utc).date().isoformat()
            if EMERGENT_LLM_KEY and imeta.get("last_run", "")[:10] != _today:
                have = await db.service_blogs.count_documents({})
                if have:
                    # ~12/day so all ~80 blogs cycle through a fresh edition about weekly.
                    n = await _refresh_stale_insights(max_items=12, older_than_hours=168)
                    if n:
                        await db.app_meta.update_one({"_id": "insights_refresh"},
                                                     {"$set": {"last_run": now_iso(), "last_count": n}}, upsert=True)
            now = datetime.now(timezone.utc)
            # Every Saturday, publish (roll forward) availability to the coming week.
            if now.weekday() == 5:  # Saturday
                ameta = await db.app_meta.find_one({"_id": "availability"}) or {}
                today = now.date()
                if ameta.get("last_published_on") != today.isoformat():
                    next_monday = today + timedelta(days=(7 - today.weekday()) % 7 or 7)
                    await db.app_meta.update_one({"_id": "availability"}, {"$set": {
                        "published_week_start": next_monday.isoformat(),
                        "last_published_on": today.isoformat()}}, upsert=True)
            if os.environ.get("GMAIL_APP_PASSWORD"):
                await _send_session_reminders()
                ist_now = datetime.now(IST_TZ)
                if ist_now.weekday() == 0 and ist_now.hour == 8:
                    ameta = await db.app_meta.find_one({"_id": "availability"}) or {}
                    if ameta.get("last_weekly_agenda") != ist_now.date().isoformat():
                        await _send_weekly_agenda()
                        await db.app_meta.update_one({"_id": "availability"},
                                                     {"$set": {"last_weekly_agenda": ist_now.date().isoformat()}}, upsert=True)
                    sdg = await db.app_meta.find_one({"_id": "sector_digest"})
                    if (sdg or {}).get("last_run", "")[:10] != ist_now.date().isoformat():
                        await _send_sector_digest()
                        await db.app_meta.update_one({"_id": "sector_digest"},
                                                     {"$set": {"last_run": now_iso()}}, upsert=True)
                # Weekly Market Signals digest to subscribers — Friday ~09:00 IST.
                if ist_now.weekday() == 4 and ist_now.hour == 9:
                    sd = await db.app_meta.find_one({"_id": "signals_digest"})
                    if (sd or {}).get("last_run", "")[:10] != ist_now.date().isoformat():
                        await _send_signals_digest()
                # Weekly SK Insights newsletter to subscribers — Wednesday ~09:00 IST.
                if ist_now.weekday() == 2 and ist_now.hour == 9:
                    inl = await db.app_meta.find_one({"_id": "insights_newsletter"})
                    if (inl or {}).get("last_run", "")[:10] != ist_now.date().isoformat():
                        await _send_insights_newsletter()
                # Rotate / auto-feature the winner — Monday ~06:00 IST.
                if ist_now.weekday() == 0 and ist_now.hour == 6:
                    fm = await db.app_meta.find_one({"_id": "featured_insight"})
                    if (fm or {}).get("rotated_at", "")[:10] != ist_now.date().isoformat():
                        await _auto_feature_winner(_prev_iso_week())
                # Weekly performance recap to the admin — Monday ~07:00 IST (respects cadence).
                if ist_now.weekday() == 0 and ist_now.hour == 7:
                    rc = await db.app_meta.find_one({"_id": "insights_recap"})
                    if (rc or {}).get("last_run", "")[:10] != ist_now.date().isoformat() and _recap_due((rc or {}).get("cadence", "weekly"), ist_now):
                        await _send_weekly_recap(_prev_iso_week())
                # Weekly Library shelf digest to subscribers — Monday ~09:00 IST.
                if ist_now.weekday() == 0 and ist_now.hour == 9:
                    ld = await db.app_meta.find_one({"_id": "library_digest"})
                    if (ld or {}).get("last_run", "")[:10] != ist_now.date().isoformat():
                        await _send_library_digest()
            if now.weekday() == 0 and os.environ.get("GMAIL_APP_PASSWORD"):  # Monday
                meta = await db.app_meta.find_one({"_id": "digest"})
                last = (meta or {}).get("last_run", "")
                if not last or last[:10] != now.strftime("%Y-%m-%d"):
                    await _send_weekly_digest()
            if now.day == 1 and os.environ.get("GMAIL_APP_PASSWORD"):  # 1st of month
                rmeta = await db.app_meta.find_one({"_id": "report"})
                rlast = (rmeta or {}).get("last_run", "")
                if not rlast or rlast[:7] != now.strftime("%Y-%m"):
                    await _send_monthly_report()
        except Exception:
            logger.exception("scheduler error")
        await asyncio.sleep(3600)


@api_router.get("/learning/recommended")
async def learning_recommended(limit: int = 12, user: Optional[dict] = Depends(get_optional_user)):
    weights = await _topic_weights(user["id"]) if user else {}
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: curator.recommended(weights, limit))
    top = sorted(weights.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return {"videos": data, "interests": [t for t, _ in top], "personalised": bool(weights)}


# ---------------- Content routes ----------------
@api_router.get("/articles")
async def list_articles(category: Optional[str] = None, sector: Optional[str] = None, limit: int = 100):
    q = {}
    if category:
        q["category"] = category
    if sector:
        q["sector"] = sector
    items = await db.articles.find(q, {"_id": 0}).sort("created_at", -1).to_list(limit)
    return items


@api_router.get("/articles/{slug}")
async def get_article(slug: str):
    item = await db.articles.find_one({"slug": slug}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Article not found")
    return item


@api_router.post("/articles")
async def create_article(body: ArticleIn, admin: dict = Depends(require_admin)):
    slug = body.title.lower().strip().replace(" ", "-")
    slug = "".join(c for c in slug if c.isalnum() or c == "-")[:80] + "-" + str(uuid.uuid4())[:6]
    doc = body.model_dump()
    doc.update({"id": str(uuid.uuid4()), "slug": slug, "author": "Sudarshan Karweer", "created_at": now_iso()})
    await db.articles.insert_one(doc)
    doc.pop("_id", None)
    return doc


@api_router.delete("/articles/{slug}")
async def delete_article(slug: str, admin: dict = Depends(require_admin)):
    res = await db.articles.delete_one({"slug": slug})
    if res.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Article not found")
    return {"deleted": True}


@api_router.get("/meta")
async def meta():
    return {"services": SERVICES, "stats": STATS, "market_pulse": MARKET_PULSE, "testimonials": TESTIMONIALS}


# ---------------- Consultation routes ----------------
@api_router.post("/consultations")
async def create_consultation(body: ConsultationIn, request: Request):
    verify_captcha(body.captcha_token, _client_ip(request), request)
    doc = body.model_dump()
    doc.pop("captcha_token", None)
    doc.update({"id": str(uuid.uuid4()), "status": "new", "source": "booking-form", "created_at": now_iso()})
    await db.consultations.insert_one(doc)
    return {"success": True, "message": "Your consultation request has been received. Sudarshan's team will reach out shortly."}


@api_router.get("/consultations")
async def list_consultations(admin: dict = Depends(require_admin)):
    items = await db.consultations.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    return items


@api_router.patch("/consultations/{cid}")
async def update_consultation(cid: str, status: str, admin: dict = Depends(require_admin)):
    await db.consultations.update_one({"id": cid}, {"$set": {"status": status}})
    return {"success": True}


@api_router.get("/admin/stats")
async def admin_stats(admin: dict = Depends(require_admin)):
    return {
        "articles": await db.articles.count_documents({}),
        "consultations": await db.consultations.count_documents({}),
        "new_leads": await db.consultations.count_documents({"status": "new"}),
        "clients": await db.users.count_documents({"role": "client"}),
    }


# ---------------- AI engine ----------------
AI_SYSTEM = (
    "You are 'Ask SK', the advisory assistant on Sudarshan Karweer's platform. "
    "Sudarshan Karweer is a renowned business coach and strategic advisor with 23+ years of experience and "
    "60+ projects across corporates and CXOs. His expertise spans renewable energy, energy storage (BESS), "
    "green hydrogen, green & climate financing, fundraising, strategy, new business development, scaling businesses, "
    "and government asset monetisation (e.g., MSRTC bus depot monetisation). "
    "Answer questions on macro/micro economics, energy transition, sustainability, climate change and company analysis "
    "in RE/Storage/Hydrogen. Be sharp, insightful and concise (under 180 words). When relevant, encourage booking a "
    "premium 1:1 consultation with Sudarshan for deeper, decision-grade advice."
)


def new_chat(session_id: str) -> LlmChat:
    return LlmChat(api_key=EMERGENT_LLM_KEY, session_id=session_id, system_message=AI_SYSTEM).with_model(
        "anthropic", "claude-sonnet-4-6"
    )


@api_router.post("/ai/chat")
async def ai_chat(body: ChatIn):
    async def gen():
        try:
            chat = new_chat(body.session_id)
            async for ev in chat.stream_message(UserMessage(text=body.message)):
                if isinstance(ev, TextDelta):
                    yield f"data: {json.dumps({'delta': ev.content})}\n\n"
                elif isinstance(ev, StreamDone):
                    break
            yield f"data: {json.dumps({'done': True})}\n\n"
        except Exception as e:
            logger.exception("AI chat error")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@api_router.post("/ai/generate")
async def ai_generate(body: GenerateIn, admin: dict = Depends(require_admin)):
    prompt = (
        f"Write a professional {body.category} article for Sudarshan Karweer's advisory platform on the topic: "
        f"'{body.topic}'. Return STRICT JSON with keys: title, summary (max 40 words), content (3-4 paragraphs, "
        f"use \\n\\n between paragraphs), tags (array of 3 short strings). No markdown, only JSON."
    )
    chat = new_chat("gen-" + str(uuid.uuid4())).with_model("anthropic", "claude-sonnet-4-6")
    text = ""
    async for ev in chat.stream_message(UserMessage(text=prompt)):
        if isinstance(ev, TextDelta):
            text += ev.content
        elif isinstance(ev, StreamDone):
            break
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        data = json.loads(text)
    except Exception:
        data = {"title": body.topic, "summary": text[:200], "content": text, "tags": [body.category]}
    return data


# ---------------- Dynamic AI homepage content engine ----------------
HOME_REFRESH_HOURS = 24
_home_lock = asyncio.Lock()

# Hard factual guardrails — the model must NOT invent anything beyond these.
HOME_FACTS = (
    "Sudarshan Karweer is a business coach and strategic advisor, and a former EY (Big 4) management consultant. "
    "23+ years of experience, 60+ projects with leading corporates in India and globally, and $2B+ of debt syndication "
    "across Maharashtra government authorities. He advises founders and CXOs on strategy, supply chain & cost optimisation, "
    "business & digital transformation, financial management, scaling, fundraising, new business development, and "
    "government asset monetisation (e.g. MSRTC bus depot monetisation). Focus sectors: renewable energy, energy storage (BESS), "
    "green hydrogen, green & climate financing, plus M&A, aviation, metals & mining, cement, steel, telecom, agriculture and start-up funding."
)

HOME_FALLBACK = {
    "hero_headline": "Turning complexity into your *competitive advantage*.",
    "hero_subtext": ("I'm Sudarshan Karweer — a business coach and strategic advisor, and a former EY (Big 4) management "
                     "consultant. Across 60+ projects I help founders and CXOs win at strategy, transformation, financial "
                     "management, fundraising and scaling — including renewable energy, BESS, green hydrogen and climate finance."),
    "insights": [
        "Great strategy is subtraction — decide what you won't do before you chase what you will.",
        "Bankability starts long before the term sheet — de-risk the model, then court capital.",
        "Scaling breaks on systems, not ambition — build the operating rhythm first.",
    ],
    "feed": [],
}


async def _generate_home_content() -> dict:
    prompt = (
        "You write the daily homepage copy for Sudarshan Karweer's advisory platform. "
        "ONLY use these verified facts — never invent credentials, awards, client names, prices, or specific current market numbers:\n"
        f"{HOME_FACTS}\n\n"
        "Produce fresh, timely, factual thought-leadership at an OVERALL business-leadership level — strategy, "
        "transformation, financial management, fundraising, new business development and scaling — with renewable energy, "
        "storage (BESS), green hydrogen and climate finance treated as focus SECTORS among others. Do NOT make the headline "
        "or subtext exclusively about the energy transition; keep the positioning broad and sector-agnostic. "
        "Return STRICT JSON only (no markdown, no code fences) with keys:\n"
        "  hero_headline: string, 8-12 words, punchy and confident, first-person brand voice, positioned at an overall "
        "business-leadership level (NOT limited to energy). Wrap exactly ONE key word or short phrase in *asterisks* for emphasis.\n"
        "  hero_subtext: string, 35-55 words, first person as Sudarshan, grounded in the verified facts, framing the breadth "
        "of his advisory (strategy, transformation, financial management, fundraising, scaling) with energy/climate as example sectors.\n"
        "  insights: array of exactly 3 strings, each a sharp 14-22 word advisory take (no fabricated statistics).\n"
        "  feed: array of exactly 5 objects, each {title: 6-10 words, take: 30-45 word factual commentary, tag: one of "
        "['Strategy','Leadership','Scaling','Fundraising','Climate Finance','Energy Transition','Storage','Green Hydrogen','Macro']}. "
        "Keep every 'take' general and evergreen-factual — do NOT present invented figures as live data.\n"
        "Output JSON only."
    )
    chat = new_chat("home-" + str(uuid.uuid4())).with_model("anthropic", "claude-sonnet-4-6")
    text = ""
    async for ev in chat.stream_message(UserMessage(text=prompt)):
        if isinstance(ev, TextDelta):
            text += ev.content
        elif isinstance(ev, StreamDone):
            break
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)
    # Validate / coerce shape.
    out = {
        "hero_headline": str(data.get("hero_headline") or HOME_FALLBACK["hero_headline"]).strip(),
        "hero_subtext": str(data.get("hero_subtext") or HOME_FALLBACK["hero_subtext"]).strip(),
        "insights": [str(x).strip() for x in (data.get("insights") or []) if str(x).strip()][:3],
        "feed": [],
    }
    for f in (data.get("feed") or []):
        if not isinstance(f, dict):
            continue
        out["feed"].append({
            "title": str(f.get("title") or "").strip(),
            "take": str(f.get("take") or "").strip(),
            "tag": str(f.get("tag") or "Strategy").strip(),
        })
    out["feed"] = [f for f in out["feed"] if f["title"] and f["take"]][:5]
    if not out["insights"]:
        out["insights"] = HOME_FALLBACK["insights"]
    return out


def _home_is_stale(doc: Optional[dict]) -> bool:
    if not doc or not doc.get("generated_at"):
        return True
    try:
        gen = datetime.fromisoformat(doc["generated_at"])
        if gen.tzinfo is None:
            gen = gen.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - gen) >= timedelta(hours=HOME_REFRESH_HOURS)
    except Exception:
        return True


async def _refresh_home_content(force: bool = False) -> Optional[dict]:
    doc = await db.app_meta.find_one({"_id": "home_content"})
    if not force and not _home_is_stale(doc):
        return doc
    async with _home_lock:
        doc = await db.app_meta.find_one({"_id": "home_content"})
        if not force and not _home_is_stale(doc):
            return doc
        try:
            data = await _generate_home_content()
        except Exception:
            logger.exception("home content generation failed")
            return doc  # keep last-known-good (may be None → frontend uses fallback)
        data["_id"] = "home_content"
        data["generated_at"] = now_iso()
        await db.app_meta.replace_one({"_id": "home_content"}, data, upsert=True)
        # Archive a dated snapshot so visitors can browse past daily reads (one per calendar day).
        day = datetime.now(timezone.utc).date().isoformat()
        await db.signals_archive.update_one({"date": day}, {"$set": {
            "date": day,
            "hero_headline": data.get("hero_headline", ""),
            "hero_subtext": data.get("hero_subtext", ""),
            "insights": data.get("insights", []),
            "feed": data.get("feed", []),
            "generated_at": data["generated_at"],
        }}, upsert=True)
        logger.info("home content regenerated")
        return data


@api_router.get("/home/content")
async def home_content():
    doc = await db.app_meta.find_one({"_id": "home_content"}, {"_id": 0})
    if _home_is_stale(doc):
        asyncio.create_task(_refresh_home_content())  # refresh in background; serve current instantly
    return doc or {}


@api_router.get("/signals/archive")
async def signals_archive(limit: int = 30):
    """Past daily 'Market Signals' reads, newest first, so visitors can browse history."""
    items = await db.signals_archive.find({}, {"_id": 0}).sort("date", -1).to_list(min(limit, 90))
    return {"signals": items}


@api_router.get("/signals/archive/{day}")
async def signals_archive_day(day: str):
    item = await db.signals_archive.find_one({"date": day}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="No signals for that date")
    return item


_og_cache: dict = {}


def _hex_to_rgb(h: str, default=(198, 241, 53)):
    try:
        h = (h or "").lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))
    except Exception:
        return default


def _render_signal_card(date: str, eyebrow_date: str, headline: str, accent=(198, 241, 53)) -> bytes:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    W, H = 1200, 630
    fonts_dir = Path(__file__).parent / "assets" / "fonts"
    f_bold = lambda s: ImageFont.truetype(str(fonts_dir / "VeraBd.ttf"), s)
    f_reg = lambda s: ImageFont.truetype(str(fonts_dir / "Vera.ttf"), s)
    img = Image.new("RGB", (W, H), (5, 5, 5))
    # Accent glow, top-right (dimmed accent so it reads on black).
    glow = Image.new("RGB", (W, H), (5, 5, 5))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 380, -220, W + 160, 320], fill=tuple(int(c * 0.6) for c in accent))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.blend(img, glow, 0.5)
    d = ImageDraw.Draw(img)
    PAD = 70
    d.text((PAD, 60), "SK", font=f_bold(40), fill=(255, 255, 255))
    sk_w = d.textlength("SK", font=f_bold(40))
    d.text((PAD + sk_w, 60), ".", font=f_bold(40), fill=accent)
    d.text((PAD, 150), "MARKET SIGNALS", font=f_bold(26), fill=accent)
    text = (headline or "Today's read on the energy transition & capital.").strip()
    hf = f_bold(58)
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=hf) <= W - 2 * PAD:
            cur = trial
        else:
            lines.append(cur); cur = w
        if len(lines) >= 4:
            break
    if cur and len(lines) < 5:
        lines.append(cur)
    lines = lines[:5]
    y = 235
    for ln in lines:
        d.text((PAD, y), ln, font=hf, fill=(245, 245, 245))
        y += 74
    d.text((PAD, H - 90), eyebrow_date or date, font=f_reg(24), fill=(160, 160, 160))
    tag = "sudarshankarweer.com/signals"
    tw = d.textlength(tag, font=f_reg(22))
    d.text((W - PAD - tw, H - 88), tag, font=f_reg(22), fill=accent)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


async def _card_accent() -> tuple:
    doc = await db.app_meta.find_one({"_id": "card_style"})
    return _hex_to_rgb((doc or {}).get("accent", "#C6F135"))


@api_router.get("/signals/og/{day}.png")
async def signals_og_image(day: str):
    """Auto-generated per-day social share card featuring that day's top headline."""
    item = await db.signals_archive.find_one({"date": day}, {"_id": 0})
    top = ""
    if item:
        feed = item.get("feed") or []
        top = (feed[0].get("title") if feed else "") or item.get("hero_headline", "")
    top = (top or "").replace("*", "")
    try:
        nice = datetime.fromisoformat((item or {}).get("generated_at", day)).strftime("%B %-d, %Y")
    except Exception:
        nice = day
    accent = await _card_accent()
    cache_key = f"{day}:{hash(top)}:{accent}"
    if cache_key not in _og_cache:
        _og_cache[cache_key] = await asyncio.to_thread(_render_signal_card, day, nice, top, accent)
    return Response(content=_og_cache[cache_key], media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})


_score_card_cache: dict = {}


def _render_score_card(title: str, framework: str, score: int, max_score: int,
                       band_title: str, name: str, accent=(198, 241, 53)) -> bytes:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
    W, H = 1200, 630
    fonts_dir = Path(__file__).parent / "assets" / "fonts"
    f_bold = lambda s: ImageFont.truetype(str(fonts_dir / "VeraBd.ttf"), s)
    f_reg = lambda s: ImageFont.truetype(str(fonts_dir / "Vera.ttf"), s)
    img = Image.new("RGB", (W, H), (5, 5, 5))
    glow = Image.new("RGB", (W, H), (5, 5, 5))
    gd = ImageDraw.Draw(glow)
    gd.ellipse([W - 420, -240, W + 180, 340], fill=tuple(int(c * 0.6) for c in accent))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    img = Image.blend(img, glow, 0.5)
    d = ImageDraw.Draw(img)
    PAD = 70
    d.text((PAD, 56), "SK", font=f_bold(40), fill=(255, 255, 255))
    sk_w = d.textlength("SK", font=f_bold(40))
    d.text((PAD + sk_w, 56), ".", font=f_bold(40), fill=accent)
    d.text((PAD, 142), "STRATEGY SIMULATION", font=f_bold(24), fill=accent)
    # Game title (wrap up to 2 lines).
    hf = f_bold(56)
    words, lines, cur = (title or "").split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=hf) <= W - 2 * PAD:
            cur = trial
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    y = 196
    for ln in lines[:2]:
        d.text((PAD, y), ln, font=hf, fill=(245, 245, 245))
        y += 66
    d.text((PAD, y + 8), framework or "", font=f_reg(26), fill=(160, 160, 160))
    # Big score.
    score_str = f"{score}"
    sf = f_bold(150)
    d.text((PAD, H - 250), score_str, font=sf, fill=accent)
    sw = d.textlength(score_str, font=sf)
    d.text((PAD + sw + 14, H - 150), f"/ {max_score}", font=f_bold(48), fill=(200, 200, 200))
    d.text((PAD, H - 96), (band_title or "").upper(), font=f_bold(30), fill=(245, 245, 245))
    who = (name or "").strip()
    if who:
        d.text((PAD, H - 56), f"{who}'s result", font=f_reg(24), fill=(160, 160, 160))
    tag = "sudarshankarweer.com/games"
    tw = d.textlength(tag, font=f_reg(22))
    d.text((W - PAD - tw, H - 56), tag, font=f_reg(22), fill=accent)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _safe_name(n: str) -> str:
    n = "".join(c for c in (n or "") if c.isalnum() or c in " -'.").strip()
    return (n.split(" ")[0] if n else "")[:24]


@api_router.get("/games/{slug}/score-card.png")
async def game_score_card(slug: str, score: int = 0, name: str = ""):
    g = GAMES_BY_SLUG.get(slug)
    if not g:
        raise HTTPException(status_code=404, detail="Unknown game")
    max_score = sum(max(o["score"] for o in r["options"]) for r in g["rounds"])
    score = max(0, min(int(score or 0), max_score))
    band = _game_debrief(g, score)
    who = _safe_name(name)
    accent = await _card_accent()
    key = f"{slug}:{score}:{who}:{accent}"
    if key not in _score_card_cache:
        if len(_score_card_cache) > 500:
            _score_card_cache.clear()
        _score_card_cache[key] = await asyncio.to_thread(
            _render_score_card, g["title"], g["framework"], score, max_score, band["title"], who, accent)
    return Response(content=_score_card_cache[key], media_type="image/png",
                    headers={"Cache-Control": "public, max-age=3600"})


@api_router.get("/games/leaderboard/global")
async def global_leaderboard(user: Optional[dict] = Depends(get_optional_user)):
    """Standalone War-Room board: best-per-(user,game) rolled up per strategist."""
    rows = await db.game_scores.aggregate([
        {"$sort": {"score": -1, "created_at": 1}},
        {"$group": {"_id": {"u": "$user_id", "g": "$game_slug"},
                    "name": {"$first": "$name"}, "best": {"$max": "$score"}}},
    ]).to_list(5000)
    by_user, champs = {}, {}
    for r in rows:
        uid = r["_id"]["u"]
        gslug = r["_id"]["g"]
        u = by_user.setdefault(uid, {"user_id": uid, "name": _first_name(r.get("name")), "total": 0, "games_played": 0})
        u["total"] += r["best"]
        u["games_played"] += 1
        c = champs.get(gslug)
        if not c or r["best"] > c["score"]:
            champs[gslug] = {"name": _first_name(r.get("name")), "score": r["best"]}
    ranked = sorted(by_user.values(), key=lambda x: (x["total"], x["games_played"]), reverse=True)[:20]
    for i, u in enumerate(ranked):
        u["rank"] = i + 1
        u.pop("user_id", None)
    total_possible = sum(sum(max(o["score"] for o in r["options"]) for r in g["rounds"]) for g in GAMES)
    champions = [{"slug": g["slug"], "title": g["title"], "tag": g["tag"],
                 "max_score": sum(max(o["score"] for o in r["options"]) for r in g["rounds"]),
                 **(champs.get(g["slug"]) or {"name": None, "score": None})} for g in GAMES]
    out = {"top": ranked, "total_possible": total_possible, "games": len(GAMES), "champions": champions}
    if user:
        me = by_user.get(user["id"])
        if me:
            all_ranked = sorted(by_user.values(), key=lambda x: (x["total"], x["games_played"]), reverse=True)
            my_rank = next((i + 1 for i, u in enumerate(all_ranked) if u["user_id"] == user["id"]), None)
            out["me"] = {"name": me["name"], "total": me["total"], "games_played": me["games_played"], "rank": my_rank}
    return out


# ---------------- Sector deep-dive pages (tech, OEMs, competition, videos, SK insights, news) ----------------
SECTORS = {
    "storage": {"name": "Energy Storage (BESS)", "tag": "Storage", "video_topic": "energy",
                "query": "battery energy storage BESS India", "blurb": "Grid-scale & behind-the-meter battery storage — the backbone of a firm, renewable grid."},
    "green-hydrogen": {"name": "Green Hydrogen", "tag": "Green Hydrogen", "video_topic": "energy",
                       "query": "green hydrogen electrolyser India", "blurb": "Electrolysis-based hydrogen for hard-to-abate industry and long-duration energy."},
    "climate-finance": {"name": "Climate & Green Finance", "tag": "Climate Finance", "video_topic": "climate-finance",
                        "query": "climate finance green bonds India renewable", "blurb": "Blended capital, green bonds and the money that makes the transition bankable."},
    "renewable-energy": {"name": "Renewable Energy", "tag": "Energy Transition", "video_topic": "energy",
                         "query": "renewable energy solar wind India transition", "blurb": "Solar, wind and the build-out reshaping how power is generated."},
    "energy-transition": {"name": "Energy Transition", "tag": "Energy Transition", "video_topic": "energy",
                          "query": "energy transition India decarbonisation", "blurb": "The macro shift from fossil fuels to clean, electrified energy systems."},
    "strategy": {"name": "Strategy & Scaling", "tag": "Strategy", "video_topic": "fundraising",
                 "query": "business strategy scaling fundraising India", "blurb": "How founders and CXOs build bankable, enduring businesses."},
    "macro": {"name": "Macro & Markets", "tag": "Macro", "video_topic": "global-macro",
              "query": "India economy macro markets energy", "blurb": "The macro and market forces shaping capital and the transition."},
    "asset-monetisation": {"name": "Government Asset Monetisation", "tag": "Asset Monetisation", "video_topic": "india-economy",
              "query": "government asset monetisation India infrastructure InvIT NMP", "blurb": "Unlocking value from public infrastructure — depots, land, roads and utilities."},
    "business-coaching": {"name": "Business Coaching & Scaling", "tag": "Coaching", "video_topic": "leadership",
              "query": "business coaching leadership scaling founders CXO India", "blurb": "Sharpening founders and CXOs to build enduring, bankable businesses."},
}
TAG_TO_SECTOR = {v["tag"]: k for k, v in SECTORS.items()}

CREDIBLE_SOURCES = {
    "economic times": ("The Economic Times", "economictimes.indiatimes.com"),
    "times of india": ("Times of India", "timesofindia.indiatimes.com"),
    "business standard": ("Business Standard", "business-standard.com"),
    "mint": ("Mint", "livemint.com"),
    "livemint": ("Mint", "livemint.com"),
    "hindu businessline": ("Hindu BusinessLine", "thehindubusinessline.com"),
    "businessline": ("Hindu BusinessLine", "thehindubusinessline.com"),
    "cnbc": ("CNBC", "cnbc.com"),
    "reuters": ("Reuters", "reuters.com"),
    "ani": ("ANI", "aninews.in"),
    "press information bureau": ("PIB", "pib.gov.in"),
    "pib": ("PIB", "pib.gov.in"),
}


def _logo_url(dom: str) -> str:
    return f"/api/logo?domain={dom}"


def _match_source(name: str):
    n = (name or "").lower()
    for key, val in CREDIBLE_SOURCES.items():
        if key in n:
            return {"name": val[0], "logo": _logo_url(val[1]), "favicon": _logo_url(val[1])}
    return None


def _source_domain(el) -> str:
    if el is not None:
        url = el.get("url") or ""
        if url:
            from urllib.parse import urlparse
            return urlparse(url).netloc.replace("www.", "")
    return ""


def _fetch_sector_news(query: str) -> list:
    import xml.etree.ElementTree as ET
    from urllib.parse import quote
    url = f"https://news.google.com/rss/search?q={quote(query)}&hl=en-IN&gl=IN&ceid=IN:en"
    try:
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        root = ET.fromstring(r.content)
    except Exception:
        logger.warning("news fetch failed for %s", query)
        return []
    credible, others = [], []
    for item in root.iter("item"):
        src_el = item.find("source")
        source = (src_el.text if src_el is not None else "") or ""
        title = (item.findtext("title") or "").rsplit(" - ", 1)[0]
        link = item.findtext("link") or ""
        pub = item.findtext("pubDate") or ""
        m = _match_source(source)
        if m:
            credible.append({"title": title, "link": link, "published": pub, "source": m["name"],
                             "logo": m["logo"], "favicon": m["favicon"], "credible": True})
        else:
            dom = _source_domain(src_el)
            if not dom:
                continue
            others.append({"title": title, "link": link, "published": pub, "source": source or dom,
                           "logo": _logo_url(dom), "favicon": _logo_url(dom), "credible": False})
    out = credible[:10]
    if len(out) < 8:
        out += others[: 8 - len(out)]
    return out[:12]


async def _claude_json(prompt: str) -> Optional[dict]:
    try:
        chat = new_chat("sector-" + str(uuid.uuid4())).with_model("anthropic", "claude-sonnet-4-6")
        text = ""
        async for ev in chat.stream_message(UserMessage(text=prompt)):
            if isinstance(ev, TextDelta):
                text += ev.content
            elif isinstance(ev, StreamDone):
                break
        text = text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text)
    except Exception:
        logger.exception("claude json gen failed")
        return None


async def _ensure_sector_deepdive(slug: str, force: bool = False) -> dict:
    s = SECTORS[slug]
    doc = await db.sector_content.find_one({"_id": slug})
    if doc and not force:
        gen = doc.get("generated_at", "")
        try:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(gen)) < timedelta(days=7):
                return doc
        except Exception:
            pass
    prompt = (
        f"You are briefing on the '{s['name']}' segment for a premium advisory site. Return STRICT JSON only, factual and evergreen "
        f"(no fabricated live prices or dated figures presented as current). Keys:\n"
        "overview: 45-70 word plain-English summary;\n"
        "technology: 45-70 words on how the core technology/method works and where it stands in maturity;\n"
        "key_oems: array of 5 objects {name, note(6-12 words)} — real, well-known manufacturers/players/firms in this segment;\n"
        "competition: array of 4 objects {name, note} — key competitive dynamics or leading companies;\n"
        "competing_tech: 40-60 words on rival/adjacent technologies or approaches;\n"
        "leader: 30-50 words on which technology/player is currently leading the pack and why;\n"
        "market_valuation: 35-55 words on market size/growth in qualitative terms (avoid stating a precise current figure as fact);\n"
        "financing: 45-70 words on how companies/projects in this segment are typically financed (debt, equity, blended capital, green bonds, viability-gap/grants, InvITs) with India context;\n"
        "tech_automation: 45-70 words on how technology, automation and machine intelligence are improving efficiency, cost and decision-making in this segment — name specific automation/efficiency levers;\n"
        "efficiency: array of 3-4 short strings — the highest-impact automation & efficiency-improvement areas here;\n"
        "use_cases: array of 3 objects {name, note(10-18 words)} — real, live examples/use cases that illustrate impact.\n"
        "Output JSON only."
    )
    data = await _claude_json(prompt)
    if not data:
        return doc or {"_id": slug, "overview": s["blurb"]}
    data["_id"] = slug
    data["generated_at"] = now_iso()
    await db.sector_content.replace_one({"_id": slug}, data, upsert=True)
    return data


async def _generate_sk_insight(slug: str):
    s = SECTORS[slug]
    prompt = (
        f"Write ONE sharp 'SK Insight' (Sudarshan Karweer's voice — ex-EY Big 4 advisor, $2B+ debt syndication, "
        f"renewables/storage/hydrogen/climate-finance) about the {s['name']} sector: a timely, factual, opinionated take a founder/CXO can act on. "
        f"60-90 words. Return STRICT JSON: {{\"insight\": string, \"title\": 6-10 words}}. JSON only."
    )
    data = await _claude_json(prompt)
    if not data or not data.get("insight"):
        return
    await db.sector_insights.insert_one({
        "id": str(uuid.uuid4()), "slug": slug, "title": data.get("title", "SK Insight"),
        "insight": data["insight"], "date": datetime.now(timezone.utc).date().isoformat(), "created_at": now_iso()})


async def _refresh_sector_news():
    for slug, s in SECTORS.items():
        items = await asyncio.to_thread(_fetch_sector_news, s["query"])
        if items:
            await db.sector_news.replace_one({"_id": slug},
                {"_id": slug, "items": items, "updated_at": now_iso()}, upsert=True)


@api_router.get("/sectors")
async def list_sectors():
    return [{"slug": k, "name": v["name"], "tag": v["tag"], "blurb": v["blurb"]} for k, v in SECTORS.items()]


@api_router.get("/sectors/{slug}")
async def get_sector(slug: str):
    if slug not in SECTORS:
        raise HTTPException(status_code=404, detail="Unknown sector")
    s = SECTORS[slug]
    deep = await _ensure_sector_deepdive(slug)
    deep.pop("_id", None)
    if isinstance(deep.get("key_oems"), list):
        deep["key_oems"] = _enrich_cards(deep["key_oems"])
    if isinstance(deep.get("competition"), list):
        deep["competition"] = _enrich_cards(deep["competition"])
    news = await db.sector_news.find_one({"_id": slug}, {"_id": 0})
    if not news:
        asyncio.create_task(_refresh_sector_news())
    insights = await db.sector_insights.find({"slug": slug}, {"_id": 0}).sort("created_at", -1).to_list(8)
    try:
        videos = curator.library(s["video_topic"], 12)
    except Exception:
        videos = []
    return {"slug": slug, "name": s["name"], "tag": s["tag"], "blurb": s["blurb"], "video_topic": s["video_topic"],
            "deepdive": deep, "news": (news or {}).get("items", []), "news_updated": (news or {}).get("updated_at", ""),
            "insights": insights, "videos": videos}


# ---------------- Climate-Finance Agencies & OEM / Competitor deep-dive pages ----------------
AGENCIES = {
    # Multilateral Development Banks
    "world-bank": {"name": "World Bank (IBRD)", "tag": "MDB", "group": "Multilateral Development Banks", "domain": "worldbank.org",
                   "query": "World Bank India climate finance renewable", "blurb": "The largest development lender — concessional capital and policy muscle for climate & infrastructure."},
    "ifc": {"name": "IFC (World Bank Group)", "tag": "MDB", "group": "Multilateral Development Banks", "domain": "ifc.org",
            "query": "IFC India green bonds private sector climate", "blurb": "The private-sector arm of the World Bank — equity, debt and green bonds for business."},
    "adb": {"name": "Asian Development Bank", "tag": "MDB", "group": "Multilateral Development Banks", "domain": "adb.org",
            "query": "Asian Development Bank India energy climate finance", "blurb": "Asia-Pacific's development bank — a cornerstone lender for India's energy transition."},
    "aiib": {"name": "AIIB", "tag": "MDB", "group": "Multilateral Development Banks", "domain": "aiib.org",
             "query": "AIIB India infrastructure renewable energy loan", "blurb": "The Asian Infrastructure Investment Bank — infrastructure and clean-energy capital across Asia."},
    "ndb": {"name": "New Development Bank (BRICS)", "tag": "MDB", "group": "Multilateral Development Banks", "domain": "ndb.int",
            "query": "New Development Bank BRICS India infrastructure loan", "blurb": "The BRICS bank — sustainable infrastructure funding for member economies including India."},
    "imf": {"name": "IMF", "tag": "MDB", "group": "Multilateral Development Banks", "domain": "imf.org",
            "query": "IMF India climate macroeconomic resilience", "blurb": "The macro anchor — surveillance, resilience finance and climate-macro guidance."},
    # Global Climate Funds
    "gcf": {"name": "Green Climate Fund", "tag": "Climate Fund", "group": "Global Climate Funds", "domain": "greenclimate.fund",
            "query": "Green Climate Fund India project accredited", "blurb": "The world's largest dedicated climate fund — mitigation and adaptation grants & concessional loans."},
    "gef": {"name": "Global Environment Facility", "tag": "Climate Fund", "group": "Global Climate Funds", "domain": "thegef.org",
            "query": "Global Environment Facility India grant climate", "blurb": "Grants for biodiversity, climate and land — often the catalytic first cheque."},
    "cif": {"name": "Climate Investment Funds", "tag": "Climate Fund", "group": "Global Climate Funds", "domain": "cif.org",
            "query": "Climate Investment Funds India clean technology", "blurb": "Concessional capital channelled via MDBs to de-risk clean-tech and coal-transition."},
    # Bilateral & DFI Partners
    "kfw": {"name": "KfW (Germany)", "tag": "DFI", "group": "Bilateral & DFI Partners", "domain": "kfw.de",
            "query": "KfW India solar renewable green energy loan", "blurb": "Germany's development bank — a major concessional lender to India's solar & green corridors."},
    "jica": {"name": "JICA (Japan)", "tag": "DFI", "group": "Bilateral & DFI Partners", "domain": "jica.go.jp",
             "query": "JICA India infrastructure metro clean energy loan", "blurb": "Japan's agency — long-tenor, low-cost yen loans for India's infrastructure & energy."},
    "afd": {"name": "AFD (France)", "tag": "DFI", "group": "Bilateral & DFI Partners", "domain": "afd.fr",
            "query": "AFD Agence Francaise India climate energy", "blurb": "France's development agency — climate-focused sovereign and sub-sovereign lending."},
    "dfc": {"name": "US DFC", "tag": "DFI", "group": "Bilateral & DFI Partners", "domain": "dfc.gov",
            "query": "US DFC India renewable energy investment", "blurb": "America's development finance institution — equity, debt and guarantees for clean energy."},
    "giz": {"name": "GIZ (Germany)", "tag": "DFI", "group": "Bilateral & DFI Partners", "domain": "giz.de",
            "query": "GIZ India energy climate technical cooperation", "blurb": "Germany's technical-cooperation agency — capacity, policy and pilot programmes."},
    "fmo": {"name": "FMO (Netherlands)", "tag": "DFI", "group": "Bilateral & DFI Partners", "domain": "fmo.nl",
            "query": "FMO India renewable energy investment fund", "blurb": "The Dutch entrepreneurial development bank — private-sector clean-energy investment."},
    "bii": {"name": "British International Investment", "tag": "DFI", "group": "Bilateral & DFI Partners", "domain": "bii.co.uk",
            "query": "British International Investment India climate renewable", "blurb": "The UK's DFI — patient equity and debt for India's climate and infrastructure."},
    # India Funds & Agencies
    "niif": {"name": "NIIF", "tag": "India Fund", "group": "India Funds & Agencies", "domain": "niifindia.in",
             "query": "NIIF National Investment Infrastructure Fund India", "blurb": "India's sovereign-anchored infrastructure fund platform — equity for scale."},
    "ireda": {"name": "IREDA", "tag": "India Fund", "group": "India Funds & Agencies", "domain": "ireda.in",
              "query": "IREDA renewable energy financing India loan", "blurb": "India's dedicated green-energy NBFC — the go-to lender for RE projects."},
    "sidbi": {"name": "SIDBI", "tag": "India Fund", "group": "India Funds & Agencies", "domain": "sidbi.in",
              "query": "SIDBI MSME green finance India", "blurb": "India's MSME development bank — green lines and enterprise finance."},
    "nabard": {"name": "NABARD", "tag": "India Fund", "group": "India Funds & Agencies", "domain": "nabard.org",
               "query": "NABARD rural climate adaptation fund India", "blurb": "India's rural development bank — climate adaptation and agri-green finance."},
    "pfc": {"name": "Power Finance Corporation", "tag": "India Fund", "group": "India Funds & Agencies", "domain": "pfcindia.com",
            "query": "Power Finance Corporation PFC India renewable loan", "blurb": "India's power-sector financier — scaling into large renewable portfolios."},
    "rec": {"name": "REC Limited", "tag": "India Fund", "group": "India Funds & Agencies", "domain": "recindia.nic.in",
            "query": "REC Limited India power renewable financing", "blurb": "A leading power-infrastructure NBFC — growing green and transmission finance."},
}

OEMS = {
    # Battery & storage
    "catl": {"name": "CATL", "tag": "Battery / Storage", "domain": "catl.com", "video_topic": "energy",
             "query": "CATL battery storage cells India", "blurb": "The world's largest battery-cell maker — LFP and grid-scale storage leader."},
    "byd": {"name": "BYD", "tag": "Battery / Storage", "domain": "byd.com", "video_topic": "energy",
            "query": "BYD battery storage India electric", "blurb": "Vertically-integrated batteries, storage and EVs at massive scale."},
    "tesla-energy": {"name": "Tesla Energy", "tag": "Battery / Storage", "domain": "tesla.com", "video_topic": "energy",
                     "query": "Tesla Megapack Powerwall energy storage", "blurb": "Megapack & Powerwall — software-defined grid and home storage."},
    "fluence": {"name": "Fluence", "tag": "Battery / Storage", "domain": "fluenceenergy.com", "video_topic": "energy",
                "query": "Fluence energy storage India grid", "blurb": "Grid-scale storage systems and AI-driven optimisation software."},
    "exide": {"name": "Exide Industries", "tag": "Battery / Storage", "domain": "exideindustries.com", "video_topic": "energy",
              "query": "Exide Industries lithium battery India gigafactory", "blurb": "India's storage incumbent — building lithium-ion gigafactory capacity."},
    "amara-raja": {"name": "Amara Raja", "tag": "Battery / Storage", "domain": "amararaja.com", "video_topic": "energy",
                   "query": "Amara Raja battery gigafactory India lithium", "blurb": "Indian battery major moving from lead-acid into lithium giga-scale."},
    # Solar
    "waaree": {"name": "Waaree Energies", "tag": "Solar", "domain": "waaree.com", "video_topic": "energy",
               "query": "Waaree Energies solar module India manufacturing", "blurb": "India's largest solar-module manufacturer by capacity."},
    "vikram-solar": {"name": "Vikram Solar", "tag": "Solar", "domain": "vikramsolar.com", "video_topic": "energy",
                     "query": "Vikram Solar module manufacturing India", "blurb": "Leading Indian module maker with global project footprint."},
    "adani-green": {"name": "Adani Green Energy", "tag": "Solar / Developer", "domain": "adanigreenenergy.com", "video_topic": "energy",
                    "query": "Adani Green Energy renewable India capacity", "blurb": "One of the world's largest solar-plus-wind developers."},
    "first-solar": {"name": "First Solar", "tag": "Solar", "domain": "firstsolar.com", "video_topic": "energy",
                    "query": "First Solar thin film India Tamil Nadu factory", "blurb": "Thin-film specialist with a large India manufacturing base."},
    "longi": {"name": "LONGi", "tag": "Solar", "domain": "longi.com", "video_topic": "energy",
              "query": "LONGi solar wafer module efficiency", "blurb": "Global wafer & module leader pushing cell-efficiency records."},
    # Wind
    "suzlon": {"name": "Suzlon", "tag": "Wind", "domain": "suzlon.com", "video_topic": "energy",
               "query": "Suzlon wind turbine India order book", "blurb": "India's flagship wind-turbine maker with a large installed fleet."},
    "inox-wind": {"name": "Inox Wind", "tag": "Wind", "domain": "inoxwind.com", "video_topic": "energy",
                  "query": "Inox Wind turbine India manufacturing", "blurb": "Indian turbine maker scaling larger-rotor platforms."},
    "vestas": {"name": "Vestas", "tag": "Wind", "domain": "vestas.com", "video_topic": "energy",
               "query": "Vestas wind turbine India order", "blurb": "The global wind leader — turbines, service and digital optimisation."},
    "siemens-gamesa": {"name": "Siemens Gamesa", "tag": "Wind", "domain": "siemensgamesa.com", "video_topic": "energy",
                       "query": "Siemens Gamesa wind India offshore", "blurb": "Onshore & offshore turbines with a strong India manufacturing line."},
    # Hydrogen & developers
    "ohmium": {"name": "Ohmium", "tag": "Green Hydrogen", "domain": "ohmium.com", "video_topic": "energy",
               "query": "Ohmium green hydrogen electrolyser India", "blurb": "PEM-electrolyser maker manufacturing in India for global markets."},
    "reliance-newenergy": {"name": "Reliance New Energy", "tag": "Green Hydrogen", "domain": "ril.com", "video_topic": "energy",
                           "query": "Reliance green hydrogen giga factory Jamnagar", "blurb": "Building an integrated solar-to-hydrogen giga-complex at Jamnagar."},
    "tata-power": {"name": "Tata Power", "tag": "Developer", "domain": "tatapower.com", "video_topic": "energy",
                   "query": "Tata Power renewable solar India capacity", "blurb": "Integrated utility scaling solar, rooftop, storage and manufacturing."},
    "renew": {"name": "ReNew", "tag": "Developer", "domain": "renew.com", "video_topic": "energy",
              "query": "ReNew Power renewable India capacity", "blurb": "One of India's largest independent renewable-power producers."},
}

ENTITY_MAPS = {"agency": AGENCIES, "oem": OEMS}


def _entity_map(kind: str) -> dict:
    return ENTITY_MAPS[kind]


def _agency_prompt(ent: dict) -> str:
    return (
        f"You are briefing on '{ent['name']}' — a climate/development-finance institution — for a premium advisory site "
        f"focused on India & Asia. Return STRICT JSON only, factual and evergreen (do NOT name specific current office-holders; "
        f"describe roles generally). Keys:\n"
        "overview: 45-70 word plain-English summary of what it is and its role in climate/development finance;\n"
        "mandate: 40-60 words on its mission and climate/energy focus;\n"
        "india_presence: 45-70 words on its India & Asia presence — where it is based, how it operates in India, and its focus here;\n"
        "key_people: array of 3-4 objects {role, note(8-16 words)} — describe leadership ROLES generally (e.g. 'Country Director, India'), NOT names;\n"
        "focus_areas: array of 5 short strings — its main sectors/themes;\n"
        "notable_programs: array of 3 objects {name, note(10-18 words)} — real flagship funds/programmes relevant to India/Asia;\n"
        "financing_instruments: array of 4 short strings — the instruments it deploys (e.g. concessional loans, green bonds, guarantees, equity);\n"
        "how_to_engage: 35-55 words on how a founder/CXO or developer can access or partner with it.\n"
        "Output JSON only."
    )


def _oem_prompt(ent: dict) -> str:
    return (
        f"You are briefing on '{ent['name']}' — a manufacturer/company in clean energy — for a premium advisory site. "
        f"Return STRICT JSON only, factual and evergreen (no fabricated dated figures presented as current). Keys:\n"
        "overview: 45-70 word plain-English summary of the company and what it makes;\n"
        "technology: 45-70 words on its core products and technology edge;\n"
        "manufacturing_capacity: 40-60 words on its manufacturing footprint and total scale in qualitative terms;\n"
        "plants: array of 3-6 objects {location, capacity(short, e.g. '5 GW modules' or 'qualitative'), note(8-16 words)} — key manufacturing plants/facilities (India emphasised where relevant);\n"
        "sales_offices: array of 3-6 objects {location, note(6-14 words)} — key sales/market offices or regions (India & global);\n"
        "sales_presence: 35-55 words on its India & global sales/market presence;\n"
        "recent_focus: array of 3 objects {title, note(10-18 words)} — recent expansion/launch themes (evergreen framing);\n"
        "competition: array of 4 objects {name, note(6-12 words)} — its key competitors;\n"
        "tech_automation: 45-70 words on how automation, machine intelligence and digital tech drive efficiency and cost in its operations;\n"
        "market_position: 30-50 words on where it stands versus peers.\n"
        "Output JSON only."
    )


async def _ensure_entity_profile(kind: str, slug: str, force: bool = False) -> dict:
    ent = _entity_map(kind)[slug]
    key = f"{kind}:{slug}"
    doc = await db.entity_content.find_one({"_id": key})
    if doc and not force:
        try:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(doc.get("generated_at", ""))) < timedelta(days=7):
                return doc
        except Exception:
            pass
    prompt = _agency_prompt(ent) if kind == "agency" else _oem_prompt(ent)
    data = await _claude_json(prompt)
    if not data:
        return doc or {"_id": key, "overview": ent["blurb"]}
    data["_id"] = key
    data["generated_at"] = now_iso()
    await db.entity_content.replace_one({"_id": key}, data, upsert=True)
    return data


async def _generate_entity_insight(kind: str, slug: str):
    ent = _entity_map(kind)[slug]
    today = datetime.now(timezone.utc).date().isoformat()
    if await db.entity_insights.find_one({"kind": kind, "slug": slug, "date": today}):
        return
    label = "climate/development-finance institution" if kind == "agency" else "clean-energy manufacturer"
    prompt = (
        f"Write ONE sharp 'SK Insight' (Sudarshan Karweer's voice — ex-EY Big 4 advisor, $2B+ debt syndication, "
        f"renewables/storage/hydrogen/climate-finance) about {ent['name']} ({label}) with an India/Asia lens: a timely, factual, "
        f"opinionated take a founder/CXO can act on. 60-90 words. Return STRICT JSON: {{\"insight\": string, \"title\": 6-10 words}}. JSON only."
    )
    data = await _claude_json(prompt)
    if not data or not data.get("insight"):
        return
    await db.entity_insights.insert_one({
        "id": str(uuid.uuid4()), "kind": kind, "slug": slug, "title": data.get("title", "SK Insight"),
        "insight": data["insight"], "date": today, "created_at": now_iso()})


async def _refresh_entity_news(kind: str):
    for slug, ent in _entity_map(kind).items():
        items = await asyncio.to_thread(_fetch_sector_news, ent["query"])
        if items:
            await db.entity_news.replace_one({"_id": f"{kind}:{slug}"},
                {"_id": f"{kind}:{slug}", "items": items, "updated_at": now_iso()}, upsert=True)


async def _entity_detail(kind: str, slug: str) -> dict:
    ent = _entity_map(kind)[slug]
    key = f"{kind}:{slug}"
    profile = await _ensure_entity_profile(kind, slug)
    profile = {k: v for k, v in profile.items() if k not in ("_id", "generated_at")}
    for _cf in ("competition", "key_oems"):
        if isinstance(profile.get(_cf), list):
            profile[_cf] = _enrich_cards(profile[_cf])
    news = await db.entity_news.find_one({"_id": key}, {"_id": 0})
    if not news:
        asyncio.create_task(_refresh_entity_news(kind))
    asyncio.create_task(_generate_entity_insight(kind, slug))
    insights = await db.entity_insights.find({"kind": kind, "slug": slug}, {"_id": 0}).sort("created_at", -1).to_list(8)
    try:
        videos = curator.library(ent.get("video_topic", "climate-finance"), 8)
    except Exception:
        videos = []
    return {"slug": slug, "name": ent["name"], "tag": ent["tag"], "group": ent.get("group", ""),
            "blurb": ent["blurb"], "logo": _logo_url(ent['domain']), "kind": kind,
            "video_topic": ent.get("video_topic", "climate-finance" if kind == "agency" else "energy"),
            "profile": profile, "news": (news or {}).get("items", []), "news_updated": (news or {}).get("updated_at", ""),
            "insights": insights, "videos": videos}


# Filter metadata for the Climate Fund Directory (instruments / ticket band / India access).
AGENCY_META = {
    "world-bank": {"instruments": ["Concessional debt", "Guarantees", "Technical assistance"], "ticket": "Large", "access": "Sovereign / PSU"},
    "ifc": {"instruments": ["Equity", "Commercial debt", "Green bonds", "Blended finance"], "ticket": "Mid", "access": "Direct (private sector)"},
    "adb": {"instruments": ["Concessional debt", "Equity", "Guarantees", "Technical assistance"], "ticket": "Large", "access": "Direct (sovereign & private)"},
    "aiib": {"instruments": ["Commercial debt", "Equity"], "ticket": "Large", "access": "Direct (sovereign & private)"},
    "ndb": {"instruments": ["Commercial debt"], "ticket": "Large", "access": "Sovereign / PSU"},
    "imf": {"instruments": ["Concessional debt", "Technical assistance"], "ticket": "Large", "access": "Sovereign / PSU"},
    "gcf": {"instruments": ["Grants", "Concessional debt", "Equity", "Guarantees", "Blended finance"], "ticket": "Mid", "access": "Via MDB / accredited entity"},
    "gef": {"instruments": ["Grants", "Blended finance"], "ticket": "Small", "access": "Via MDB / accredited entity"},
    "cif": {"instruments": ["Concessional debt", "Grants", "Blended finance"], "ticket": "Large", "access": "Via MDB / accredited entity"},
    "kfw": {"instruments": ["Concessional debt", "Grants", "Technical assistance"], "ticket": "Mid", "access": "Sovereign / PSU"},
    "jica": {"instruments": ["Concessional debt", "Technical assistance"], "ticket": "Large", "access": "Sovereign / PSU"},
    "afd": {"instruments": ["Concessional debt", "Grants", "Technical assistance"], "ticket": "Mid", "access": "Direct (sovereign & private)"},
    "dfc": {"instruments": ["Equity", "Commercial debt", "Guarantees"], "ticket": "Mid", "access": "Direct (private sector)"},
    "giz": {"instruments": ["Grants", "Technical assistance"], "ticket": "Small", "access": "Technical assistance"},
    "fmo": {"instruments": ["Equity", "Commercial debt", "Blended finance"], "ticket": "Small", "access": "Direct (private sector)"},
    "bii": {"instruments": ["Equity", "Commercial debt"], "ticket": "Mid", "access": "Direct (private sector)"},
    "niif": {"instruments": ["Equity"], "ticket": "Large", "access": "India-domiciled"},
    "ireda": {"instruments": ["Commercial debt", "Concessional debt"], "ticket": "Mid", "access": "Direct (developers)"},
    "sidbi": {"instruments": ["Commercial debt", "Blended finance"], "ticket": "Small", "access": "Direct (MSMEs)"},
    "nabard": {"instruments": ["Concessional debt", "Grants"], "ticket": "Small", "access": "Rural / agri"},
    "pfc": {"instruments": ["Commercial debt"], "ticket": "Large", "access": "Direct (power sector)"},
    "rec": {"instruments": ["Commercial debt"], "ticket": "Large", "access": "Direct (power sector)"},
}
AGENCY_TICKET_LABEL = {"Small": "Small (<$25M)", "Mid": "Mid ($25M–$250M)", "Large": "Large ($250M+)"}


@api_router.get("/agencies")
async def list_agencies():
    groups = {}
    for k, v in AGENCIES.items():
        meta = AGENCY_META.get(k, {})
        groups.setdefault(v["group"], []).append({"slug": k, "name": v["name"], "tag": v["tag"], "blurb": v["blurb"],
            "logo": _logo_url(v['domain']),
            "instruments": meta.get("instruments", []), "ticket": meta.get("ticket", ""),
            "ticket_label": AGENCY_TICKET_LABEL.get(meta.get("ticket", ""), ""), "access": meta.get("access", "")})
    order = ["Multilateral Development Banks", "Global Climate Funds", "Bilateral & DFI Partners", "India Funds & Agencies"]
    return [{"group": g, "items": groups[g]} for g in order if g in groups]


@api_router.get("/agencies/{slug}")
async def get_agency(slug: str):
    if slug not in AGENCIES:
        raise HTTPException(status_code=404, detail="Unknown agency")
    return await _entity_detail("agency", slug)


@api_router.get("/oems")
async def list_oems():
    groups = {}
    for k, v in OEMS.items():
        groups.setdefault(v["tag"], []).append({"slug": k, "name": v["name"], "tag": v["tag"], "blurb": v["blurb"],
            "logo": _logo_url(v['domain'])})
    return [{"group": g, "items": items} for g, items in groups.items()]


@api_router.get("/oems/{slug}")
async def get_oem(slug: str):
    if slug not in OEMS:
        raise HTTPException(status_code=404, detail="Unknown OEM")
    return await _entity_detail("oem", slug)


# ---- Company logos (India + global players) & clickable "box" topic detail ----
COMPANY_DOMAINS = {
    "tesla": "tesla.com", "byd": "byd.com", "catl": "catl.com", "exide": "exideindustries.com",
    "amara raja": "amararaja.com", "fluence": "fluenceenergy.com", "lg energy": "lgensol.com",
    "lg chem": "lgchem.com", "panasonic": "panasonic.com", "samsung sdi": "samsungsdi.com",
    "northvolt": "northvolt.com", "waaree": "waaree.com", "vikram solar": "vikramsolar.com",
    "adani green": "adanigreenenergy.com", "adani solar": "adanisolar.com", "adani": "adani.com",
    "first solar": "firstsolar.com", "longi": "longi.com", "jinko": "jinkosolar.com",
    "trina": "trinasolar.com", "ja solar": "jasolar.com", "canadian solar": "canadiansolar.com",
    "renew": "renew.com", "tata power": "tatapower.com", "tata": "tata.com", "reliance": "ril.com",
    "jsw": "jsw.in", "suzlon": "suzlon.com", "inox": "inoxwind.com", "vestas": "vestas.com",
    "siemens gamesa": "siemensgamesa.com", "siemens": "siemens.com", "ge vernova": "gevernova.com",
    "general electric": "ge.com", "goldwind": "goldwind.com", "envision": "envision-group.com",
    "nordex": "nordex-online.com", "ohmium": "ohmium.com", "ntpc": "ntpc.co.in", "sjvn": "sjvn.nic.in",
    "nhpc": "nhpcindia.com", "power grid": "powergrid.in", "greenko": "greenkogroup.com",
    "avaada": "avaada.com", "acme": "acme.in", "azure power": "azurepower.com",
    "hero future": "herofutureenergies.com", "sembcorp": "sembcorp.com", "engie": "engie.com",
    "edf": "edf.fr", "orsted": "orsted.com", "iberdrola": "iberdrola.com", "brookfield": "brookfield.com",
    "sungrow": "sungrowpower.com", "huawei": "huawei.com", "sma": "sma.de", "hitachi": "hitachienergy.com",
    "abb": "abb.com", "schneider": "se.com", "bhel": "bhel.com", "l&t": "larsentoubro.com",
    "larsen": "larsentoubro.com", "gail": "gail.co.in", "ongc": "ongcindia.com", "indian oil": "iocl.com",
    "bp ": "bp.com", "shell": "shell.com", "totalenergies": "totalenergies.com", "acwa": "acwapower.com",
    "masdar": "masdar.ae", "premier energies": "premierenergies.com", "rec group": "recgroup.com",
    "world bank": "worldbank.org", "ifc": "ifc.org", "adb": "adb.org", "aiib": "aiib.org",
    "green climate": "greenclimate.fund", "kfw": "kfw.de", "jica": "jica.go.jp",
}


def _company_logo(name: str):
    if not name:
        return None
    n = " " + name.lower() + " "
    for k, dom in COMPANY_DOMAINS.items():
        if k in n:
            return {"logo": _logo_url(dom), "favicon": _logo_url(dom)}
    import re
    token = re.sub(r"[^a-z0-9]", "", name.lower().split("(")[0].split(",")[0].split("-")[0].split(" ")[0])
    if len(token) >= 4:
        return {"logo": _logo_url(f"{token}.com"), "favicon": _logo_url(f"{token}.com")}
    return None


def _enrich_cards(items):
    if not isinstance(items, list):
        return items
    out = []
    for it in items:
        if isinstance(it, dict) and it.get("name") and not it.get("logo"):
            lg = _company_logo(it["name"])
            if lg:
                it = {**it, **lg}
        out.append(it)
    return out


async def _ensure_topic_profile(name: str, context: str) -> dict:
    import hashlib
    key = hashlib.sha256(f"{name}|{context}".lower().encode()).hexdigest()
    doc = await db.topic_content.find_one({"_id": key})
    if doc:
        try:
            if (datetime.now(timezone.utc) - datetime.fromisoformat(doc.get("generated_at", ""))) < timedelta(days=7):
                return doc
        except Exception:
            pass
    ctx = f" in the context of {context}" if context else ""
    prompt = (
        f"Brief on '{name}'{ctx} for a premium India/Asia advisory site. STRICT JSON only, factual and "
        f"evergreen (no fabricated dated figures presented as current). Keys:\n"
        "overview: 55-85 word plain-English summary;\n"
        "details: array of 4-6 objects {point(3-6 words), note(12-22 words)} spanning technology, financing, "
        "market position, India relevance, and automation/efficiency;\n"
        "sk_take: 60-90 words in Sudarshan Karweer's opinionated advisory voice (ex-EY Big 4, $2B+ debt "
        "syndication) that a founder/CXO can act on.\n"
        "Output JSON only."
    )
    data = await _claude_json(prompt)
    if not data:
        return doc or {"_id": key, "overview": ""}
    data["_id"] = key
    data["generated_at"] = now_iso()
    await db.topic_content.replace_one({"_id": key}, data, upsert=True)
    return data


@api_router.get("/topic")
async def get_topic(name: str, context: str = "", topic: str = "energy"):
    prof = await _ensure_topic_profile(name, context)
    prof = {k: v for k, v in prof.items() if k not in ("_id", "generated_at")}
    q = f"{name} {context}".strip()
    news = await asyncio.to_thread(_fetch_sector_news, q)
    blogs = await asyncio.to_thread(_fetch_sector_news, f"{q} analysis OR opinion OR outlook OR blog")
    try:
        videos = curator.library(topic, 6)
    except Exception:
        videos = []
    lg = _company_logo(name) or {}
    return {"name": name, "context": context, **prof,
            "logo": lg.get("logo"), "favicon": lg.get("favicon"),
            "news": news, "blogs": blogs, "videos": videos}


# ---------------- Leadership Library (read / listen / watch / get it) ----------------
# Catalogue lives in library_data.py (40 curated titles). Public-domain titles get an
# in-site page-flip reader (Project Gutenberg) + free audiobook (LibriVox via archive.org).
# Copyrighted titles get key lessons + an Amazon link. Every title carries SK's
# perspective, key learnings and a "make it a ritual" practice. Videos are pulled
# specifically for each book; the Watch tab is hidden when none are found.
from library_data import BOOKS, BOOKS_BY_SLUG

_BOOK_TEXT_CACHE: dict = {}
LIBRARY_SHELF_SIZE = 12


def _daily_shelf(n: int = LIBRARY_SHELF_SIZE) -> list:
    """Deterministic per-day rotation of the full catalogue — a fresh shelf daily."""
    today = date.today().isoformat()
    seed = int(hashlib.sha256(today.encode()).hexdigest(), 16)
    rnd = random.Random(seed)
    idx = list(range(len(BOOKS)))
    rnd.shuffle(idx)
    return [BOOKS[i] for i in idx[:n]]


def _book_public(b: dict) -> dict:
    return {"slug": b["slug"], "title": b["title"], "author": b["author"], "year": b["year"],
            "theme": b["theme"], "blurb": b["blurb"], "why_sk": b["why_sk"], "lessons": b["lessons"],
            "ritual": b.get("ritual", ""), "ritual_pro": b.get("ritual_pro", []),
            "ritual_personal": b.get("ritual_personal", []),
            "public_domain": b["public_domain"], "has_read": bool(b.get("gutenberg")),
            "has_audio": bool(b.get("audio")), "audio_embed": (f"https://archive.org/embed/{b['audio']}" if b.get("audio") else ""),
            "amazon": f"https://www.amazon.com/s?k={quote_plus(b['title'] + ' ' + b['author'])}",
            "source": b["source"], "credit": b["credit"]}


@api_router.get("/books")
async def list_books(scope: str = "shelf"):
    src = BOOKS if scope == "all" else _daily_shelf()
    return [_book_public(b) for b in src]


@api_router.get("/books/{slug}")
async def get_book(slug: str):
    b = BOOKS_BY_SLUG.get(slug)
    if not b:
        raise HTTPException(status_code=404, detail="Unknown book")
    data = _book_public(b)
    try:
        data["videos"] = await asyncio.to_thread(curator.book_videos, f"{b['title']} {b['author']}", 6)
    except Exception:
        data["videos"] = []
    return data

@api_router.get("/books/{slug}/text")
async def get_book_text(slug: str):
    b = BOOKS_BY_SLUG.get(slug)
    if not b or not b.get("gutenberg"):
        raise HTTPException(status_code=404, detail="No free text for this title")
    gid = b["gutenberg"]
    if gid in _BOOK_TEXT_CACHE:
        return Response(content=_BOOK_TEXT_CACHE[gid], media_type="text/plain; charset=utf-8")
    text = ""
    for url in (f"https://www.gutenberg.org/cache/epub/{gid}/pg{gid}.txt", f"https://www.gutenberg.org/files/{gid}/{gid}-0.txt"):
        try:
            r = await asyncio.to_thread(lambda u=url: requests.get(u, timeout=15, headers={"User-Agent": "Mozilla/5.0"}))
            if r.status_code == 200 and len(r.text) > 500:
                text = r.text
                break
        except Exception:
            continue
    if not text:
        raise HTTPException(status_code=503, detail="Text temporarily unavailable")
    # Trim Project Gutenberg header/footer boilerplate.
    up = text
    s = up.find("*** START OF")
    if s != -1:
        s = up.find("\n", s)
        up = up[s + 1:]
    e = up.find("*** END OF")
    if e != -1:
        up = up[:e]
    up = up.strip()
    _BOOK_TEXT_CACHE[gid] = up
    return Response(content=up, media_type="text/plain; charset=utf-8")


# ---------------- CXO Strategy Simulations (war-room decision games) ----------------
from games_data import GAMES, GAMES_BY_SLUG, game_card, game_play, debrief as _game_debrief


class GameScoreIn(BaseModel):
    answers: dict  # {round_id(str): option_id}


@api_router.get("/games")
async def list_games():
    return [game_card(g) for g in GAMES]


@api_router.get("/games/{slug}")
async def get_game(slug: str):
    g = GAMES_BY_SLUG.get(slug)
    if not g:
        raise HTTPException(status_code=404, detail="Unknown game")
    return game_play(g)


@api_router.post("/games/{slug}/score")
async def score_game(slug: str, body: GameScoreIn, user: Optional[dict] = Depends(get_optional_user)):
    g = GAMES_BY_SLUG.get(slug)
    if not g:
        raise HTTPException(status_code=404, detail="Unknown game")
    total = 0
    breakdown = []
    for r in g["rounds"]:
        chosen = (body.answers or {}).get(str(r["id"]))
        opt = next((o for o in r["options"] if o["id"] == chosen), None)
        sc = opt["score"] if opt else 0
        total += sc
        breakdown.append({"round": r["id"], "chosen": chosen, "score": sc,
                          "feedback": opt["feedback"] if opt else "",
                          "best": max(o["score"] for o in r["options"])})
    result = {**_game_debrief(g, total), "breakdown": breakdown}
    result["saved"] = False
    if user:
        prev_top = await db.game_scores.find({"game_slug": slug}).sort("score", -1).limit(1).to_list(1)
        prev_holder = prev_top[0] if prev_top else None
        prev_max = prev_holder["score"] if prev_holder else -1
        my_prev = await db.game_scores.find({"user_id": user["id"], "game_slug": slug}).sort("score", -1).limit(1).to_list(1)
        result["personal_best_before"] = my_prev[0]["score"] if my_prev else None
        await db.game_scores.insert_one({
            "id": str(uuid.uuid4()), "game_slug": slug, "game_title": g["title"],
            "user_id": user["id"], "name": user.get("name", "Anonymous"),
            "email": user.get("email", ""), "score": total,
            "max_score": result["max_score"], "band": result["band"], "created_at": now_iso()})
        result["saved"] = True
        # Dethrone nudge: if this run beats the previous #1 held by someone else, notify them.
        if (total > prev_max and prev_holder and prev_holder.get("user_id") != user["id"]
                and prev_holder.get("email") and os.environ.get("GMAIL_APP_PASSWORD")):
            loop = asyncio.get_event_loop()
            game_url = f"{PUBLIC_SITE}/games/{slug}"
            loop.run_in_executor(None, lambda: send_score_beaten_email(
                prev_holder["email"], _first_name(prev_holder.get("name")), g["title"],
                _first_name(user.get("name")), total, prev_max, result["max_score"], game_url))
    return result


def _first_name(n: str) -> str:
    return (n or "Anonymous").strip().split(" ")[0] or "Anonymous"


@api_router.get("/games/{slug}/leaderboard")
async def game_leaderboard(slug: str, user: Optional[dict] = Depends(get_optional_user)):
    g = GAMES_BY_SLUG.get(slug)
    if not g:
        raise HTTPException(status_code=404, detail="Unknown game")
    # Best score per user (public top board).
    pipeline = [
        {"$match": {"game_slug": slug}},
        {"$sort": {"score": -1, "created_at": 1}},
        {"$group": {"_id": "$user_id", "name": {"$first": "$name"},
                    "score": {"$max": "$score"}, "max_score": {"$first": "$max_score"},
                    "created_at": {"$first": "$created_at"}}},
        {"$sort": {"score": -1, "created_at": 1}},
        {"$limit": 10},
    ]
    rows = await db.game_scores.aggregate(pipeline).to_list(10)
    top = [{"rank": i + 1, "name": _first_name(r.get("name")), "score": r["score"],
            "max_score": r.get("max_score", 15), "date": (r.get("created_at") or "")[:10]}
           for i, r in enumerate(rows)]
    out = {"top": top, "max_score": sum(max(o["score"] for o in rr["options"]) for rr in g["rounds"])}
    if user:
        mine = await db.game_scores.find({"user_id": user["id"], "game_slug": slug},
                                         {"_id": 0}).sort("created_at", -1).to_list(50)
        out["my_runs"] = [{"score": m["score"], "max_score": m.get("max_score", 15),
                           "band": m.get("band", ""), "date": (m.get("created_at") or "")[:10]} for m in mine]
        out["my_best"] = max((m["score"] for m in mine), default=None)
        out["plays"] = len(mine)
    return out


@api_router.get("/me/simulations")
async def my_simulations(user: dict = Depends(get_current_user)):
    rows = await db.game_scores.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    by_game = {}
    for m in rows:
        g = by_game.setdefault(m["game_slug"], {"game_slug": m["game_slug"], "game_title": m.get("game_title", m["game_slug"]),
                                                "best": 0, "max_score": m.get("max_score", 15), "plays": 0, "last_played": ""})
        g["plays"] += 1
        g["best"] = max(g["best"], m["score"])
        if (m.get("created_at") or "") > g["last_played"]:
            g["last_played"] = (m.get("created_at") or "")[:10]
    return {"games": sorted(by_game.values(), key=lambda x: x["last_played"], reverse=True), "total_runs": len(rows)}



# ---------------- Leadership Assessment: Mini-IPIP Big Five -> quadrant -> SK Blueprint ----------------
# Mini-IPIP (Donnellan, Oswald, Baird & Lucas, 2006) — public domain (ipip.ori.org).
IPIP_ITEMS = [
    {"id": "e1", "trait": "E", "keyed": 1, "text": "I am the life of the party."},
    {"id": "a1", "trait": "A", "keyed": 1, "text": "I sympathize with others' feelings."},
    {"id": "c1", "trait": "C", "keyed": 1, "text": "I get chores done right away."},
    {"id": "n1", "trait": "N", "keyed": 1, "text": "I have frequent mood swings."},
    {"id": "o1", "trait": "O", "keyed": 1, "text": "I have a vivid imagination."},
    {"id": "e2", "trait": "E", "keyed": -1, "text": "I don't talk a lot."},
    {"id": "a2", "trait": "A", "keyed": -1, "text": "I am not interested in other people's problems."},
    {"id": "c2", "trait": "C", "keyed": -1, "text": "I often forget to put things back in their proper place."},
    {"id": "n2", "trait": "N", "keyed": -1, "text": "I am relaxed most of the time."},
    {"id": "o2", "trait": "O", "keyed": -1, "text": "I am not interested in abstract ideas."},
    {"id": "e3", "trait": "E", "keyed": 1, "text": "I talk to a lot of different people at events."},
    {"id": "a3", "trait": "A", "keyed": 1, "text": "I feel others' emotions."},
    {"id": "c3", "trait": "C", "keyed": 1, "text": "I like order."},
    {"id": "n3", "trait": "N", "keyed": 1, "text": "I get upset easily."},
    {"id": "o3", "trait": "O", "keyed": -1, "text": "I have difficulty understanding abstract ideas."},
    {"id": "e4", "trait": "E", "keyed": -1, "text": "I keep in the background."},
    {"id": "a4", "trait": "A", "keyed": -1, "text": "I am not really interested in others."},
    {"id": "c4", "trait": "C", "keyed": -1, "text": "I make a mess of things."},
    {"id": "n4", "trait": "N", "keyed": -1, "text": "I seldom feel blue."},
    {"id": "o4", "trait": "O", "keyed": -1, "text": "I do not have a good imagination."},
]
TRAIT_NAMES = {"E": "Extraversion", "A": "Agreeableness", "C": "Conscientiousness", "N": "Neuroticism", "O": "Openness"}
QUADRANTS = {
    "visionary": {"name": "Visionary Commander", "tagline": "High drive, high people — you set bold direction and take people with you."},
    "driver": {"name": "Driving Commander", "tagline": "High drive, lower warmth — you execute relentlessly and demand results."},
    "coach": {"name": "Empowering Coach", "tagline": "High people, lower task-grip — you grow people and build trust."},
    "steward": {"name": "Steady Steward", "tagline": "Measured and reliable — you bring calm, order and consistency."},
}


class AssessmentIn(BaseModel):
    answers: dict


@api_router.get("/assessment/questions")
async def assessment_questions():
    return {"items": [{"id": i["id"], "text": i["text"]} for i in IPIP_ITEMS],
            "scale": ["Strongly disagree", "Disagree", "Neutral", "Agree", "Strongly agree"],
            "credit": "Questionnaire: Mini-IPIP (Donnellan et al., 2006), International Personality Item Pool — public domain."}


@api_router.post("/assessment/score")
async def assessment_score(body: AssessmentIn):
    raw = {"E": 0, "A": 0, "C": 0, "N": 0, "O": 0}
    for item in IPIP_ITEMS:
        v = body.answers.get(item["id"])
        if not isinstance(v, int) or v < 1 or v > 5:
            raise HTTPException(status_code=400, detail=f"Missing/invalid answer for {item['id']}")
        raw[item["trait"]] += v if item["keyed"] == 1 else (6 - v)
    pct = {t: round((raw[t] - 4) / 16 * 100) for t in raw}  # 4 items each: 4..20 -> 0..100
    emotional_stability = 100 - pct["N"]
    task = round(pct["C"] * 0.6 + pct["E"] * 0.4)
    people = round(pct["A"] * 0.6 + emotional_stability * 0.4)
    key = ("visionary" if task >= 50 and people >= 50 else "driver" if task >= 50 else "coach" if people >= 50 else "steward")
    quad = QUADRANTS[key]
    scores = {
        "Extraversion": pct["E"], "Agreeableness": pct["A"], "Conscientiousness": pct["C"],
        "Openness": pct["O"], "Emotional stability": emotional_stability,
    }
    prompt = (
        f"You are Sudarshan Karweer (ex-EY Big 4 advisor, $2B+ debt syndication, executive coach) writing a private "
        f"'Leadership Blueprint' for a senior leader based on a validated Big Five profile. Speak in first person as SK, warm but "
        f"direct, from experience — NEVER mention AI, algorithms or that this is automated. Profile (0-100): "
        f"Extraversion {pct['E']}, Agreeableness {pct['A']}, Conscientiousness {pct['C']}, Openness {pct['O']}, "
        f"Emotional stability {emotional_stability}. Leadership quadrant: {quad['name']} ({quad['tagline']}). "
        f"Return STRICT JSON only. Keys: "
        f"narrative: 90-130 words on what this style means in a leadership seat and where it shines; "
        f"strengths: array of 4 short strings; "
        f"blind_spots: array of 4 objects {{spot(4-8 words), why(12-20 words)}}; "
        f"roadmap: array of 4 objects {{horizon('30 days'|'90 days'|'6 months'|'12 months'), milestone(4-8 words), action(12-22 words)}}. "
        f"JSON only."
    )
    blueprint = await _claude_json(prompt) or {}
    return {"scores": scores, "quadrant": {"key": key, **quad}, "axes": {"task": task, "people": people},
            "blueprint": blueprint,
            "credit": "Big Five profile via Mini-IPIP (Donnellan et al., 2006), public domain. Blueprint reflects Sudarshan Karweer's coaching perspective."}


NEWS_REFRESH_HOURS = 4


_LOGO_CACHE: dict = {}
_LOGO_PLACEHOLDER = _base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)


@api_router.get("/logo")
async def get_logo(domain: str):
    dom = (domain or "").strip().lower().replace("https://", "").replace("http://", "").strip("/")
    if not dom:
        return Response(content=_LOGO_PLACEHOLDER, media_type="image/png")
    if dom in _LOGO_CACHE:
        b, ct = _LOGO_CACHE[dom]
        return Response(content=b, media_type=ct, headers={"Cache-Control": "public, max-age=604800"})
    sources = [
        f"https://logo.clearbit.com/{dom}?size=64",
        f"https://www.google.com/s2/favicons?domain={dom}&sz=64",
        f"https://icons.duckduckgo.com/ip3/{dom}.ico",
    ]
    for url in sources:
        try:
            r = await asyncio.to_thread(lambda u=url: requests.get(u, timeout=8, headers={"User-Agent": "Mozilla/5.0"}))
            if r.status_code == 200 and r.content and len(r.content) > 120:
                ct = r.headers.get("content-type", "image/png")
                if "image" not in ct:
                    ct = "image/png"
                _LOGO_CACHE[dom] = (r.content, ct)
                return Response(content=r.content, media_type=ct, headers={"Cache-Control": "public, max-age=604800"})
        except Exception:
            continue
    _LOGO_CACHE[dom] = (_LOGO_PLACEHOLDER, "image/png")
    return Response(content=_LOGO_PLACEHOLDER, media_type="image/png", headers={"Cache-Control": "public, max-age=86400"})


async def _refresh_all_news_if_due():
    meta = await db.app_meta.find_one({"_id": "news_refresh"}) or {}
    try:
        due = (datetime.now(timezone.utc) - datetime.fromisoformat(meta.get("last", ""))) >= timedelta(hours=NEWS_REFRESH_HOURS)
    except Exception:
        due = True
    if not due:
        return
    try:
        await _refresh_sector_news()
        await _refresh_entity_news("agency")
        await _refresh_entity_news("oem")
        await db.app_meta.update_one({"_id": "news_refresh"}, {"$set": {"last": now_iso()}}, upsert=True)
    except Exception:
        logger.exception("news refresh failed")


async def _warm_entities():
    """One-time background warm of sector/agency/OEM profiles so pages load instantly.
    Cached in Mongo for 7 days, so this is cheap and idempotent across restarts."""
    await asyncio.sleep(5)
    try:
        sem = asyncio.Semaphore(3)

        async def _one(coro):
            async with sem:
                try:
                    await coro
                except Exception:
                    pass

        tasks = []
        for slug in SECTORS:
            tasks.append(_one(_ensure_sector_deepdive(slug)))
        for slug in AGENCIES:
            tasks.append(_one(_ensure_entity_profile("agency", slug)))
        for slug in OEMS:
            tasks.append(_one(_ensure_entity_profile("oem", slug)))
        await asyncio.gather(*tasks)
        logger.info("entity profile warm complete")
    except Exception:
        logger.exception("entity warm failed")


@api_router.post("/admin/home/regenerate")
async def admin_home_regenerate(request: Request, admin: dict = Depends(require_admin)):
    data = await _refresh_home_content(force=True)
    if not data:
        raise HTTPException(status_code=502, detail="Content generation failed — please try again in a moment.")
    await audit(request, admin.get("email"), "home_content_regenerated")
    data = dict(data)
    data.pop("_id", None)
    return data


@api_router.get("/")
async def root():
    return {"message": "Sudarshan Karweer Advisory API"}


# ---------------- Live Market Data (Yahoo Finance) ----------------
YF_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
MARKET_SYMBOLS = [
    ("Albemarle · Lithium", "ALB"),
    ("Global X Lithium ETF", "LIT"),
    ("Invesco Solar ETF", "TAN"),
    ("First Solar", "FSLR"),
    ("Enphase Energy", "ENPH"),
    ("Tesla · Energy", "TSLA"),
    ("Copper Futures", "HG=F"),
    ("Crude Oil · WTI", "CL=F"),
]
_market_cache = {"ts": 0, "data": []}


def _fetch_symbol(name, sym):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
        r = requests.get(url, params={"range": "1d", "interval": "1d"}, headers={"User-Agent": YF_UA}, timeout=6)
        m = r.json()["chart"]["result"][0]["meta"]
        price = m.get("regularMarketPrice")
        prev = m.get("chartPreviousClose") or m.get("previousClose") or price
        change = ((price - prev) / prev * 100) if prev else 0
        cur = m.get("currency", "USD")
        sign = "$" if cur == "USD" else ""
        return {"name": name, "value": f"{sign}{price:,.2f}", "change": f"{change:+.2f}%", "up": change >= 0}
    except Exception:
        return None


def _fetch_all_market():
    with ThreadPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(lambda p: _fetch_symbol(*p), MARKET_SYMBOLS))
    return [r for r in res if r]


@api_router.get("/market/live")
async def market_live():
    now = time.time()
    if now - _market_cache["ts"] < 120 and _market_cache["data"]:
        return {"data": _market_cache["data"], "updated": _market_cache["ts"], "cached": True}
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, _fetch_all_market)
    if data:
        _market_cache["ts"] = now
        _market_cache["data"] = data
    return {"data": data or _market_cache["data"], "updated": _market_cache["ts"], "cached": False}


# ---------------- Newsletter ----------------
class NewsletterIn(BaseModel):
    email: EmailStr
    captcha_token: Optional[str] = None
    themes: List[str] = []


@api_router.post("/newsletter")
async def subscribe(body: NewsletterIn, request: Request):
    verify_captcha(body.captcha_token, _client_ip(request), request)
    email = body.email.lower()
    themes = [t for t in body.themes if t in INSIGHT_THEMES][:8]
    existing = await db.subscribers.find_one({"email": email})
    if existing:
        if themes:
            await db.subscribers.update_one({"email": email}, {"$set": {"interests_themes": themes}})
        return {"success": True, "message": "You're already subscribed — thank you!"}
    await db.subscribers.insert_one({"id": str(uuid.uuid4()), "email": email,
                                     "interests_themes": themes, "created_at": now_iso()})
    return {"success": True, "message": "Subscribed! You'll receive Sudarshan's latest insights."}


@api_router.get("/newsletter")
async def list_subscribers(admin: dict = Depends(require_admin)):
    return await db.subscribers.find({}, {"_id": 0}).sort("created_at", -1).to_list(2000)


PUBLIC_SITE = "https://www.sudarshankarweer.com"


def _unsub_token(email: str) -> str:
    return pyjwt.encode({"purpose": "unsubscribe", "email": (email or "").lower()},
                        get_jwt_secret(), algorithm="HS256")


def _resub_token(email: str) -> str:
    return pyjwt.encode({"purpose": "resubscribe", "email": (email or "").lower()},
                        get_jwt_secret(), algorithm="HS256")


def _unsub_url(email: str) -> str:
    return f"{PUBLIC_SITE}/api/newsletter/unsubscribe?token={_unsub_token(email)}"


# ---- Weekly Sector Digest: subscriber interests + compile + send ----
def _prefs_token(email: str) -> str:
    return pyjwt.encode({"purpose": "prefs", "email": (email or "").lower()}, get_jwt_secret(), algorithm="HS256")


def _prefs_url(email: str) -> str:
    return f"{PUBLIC_SITE}/preferences?token={_prefs_token(email)}"


DEFAULT_DIGEST_SECTORS = ["renewable-energy", "storage", "green-hydrogen", "climate-finance"]
DEFAULT_DIGEST_AGENCIES = ["world-bank", "adb", "gcf"]


class PrefsIn(BaseModel):
    token: str
    sectors: List[str] = []
    agencies: List[str] = []
    themes: List[str] = []


class FollowIn(BaseModel):
    email: EmailStr
    kind: str
    slug: str


@api_router.get("/newsletter/preferences")
async def get_preferences(token: str = ""):
    email = _decode_email(token, "prefs")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired link")
    sub = await db.subscribers.find_one({"email": email}, {"_id": 0})
    return {"email": email, "subscribed": bool(sub),
            "selected_sectors": (sub or {}).get("interests_sectors", []),
            "selected_agencies": (sub or {}).get("interests_agencies", []),
            "selected_themes": (sub or {}).get("interests_themes", []),
            "all_themes": INSIGHT_THEMES,
            "all_sectors": [{"slug": k, "name": v["name"]} for k, v in SECTORS.items()],
            "all_agencies": [{"slug": k, "name": v["name"], "group": v["group"]} for k, v in AGENCIES.items()]}


@api_router.post("/newsletter/preferences")
async def set_preferences(body: PrefsIn):
    email = _decode_email(body.token, "prefs")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired link")
    sec = [s for s in body.sectors if s in SECTORS][:20]
    ag = [a for a in body.agencies if a in AGENCIES][:30]
    th = [t for t in body.themes if t in INSIGHT_THEMES][:8]
    await db.subscribers.update_one({"email": email},
        {"$set": {"interests_sectors": sec, "interests_agencies": ag, "interests_themes": th},
         "$setOnInsert": {"id": str(uuid.uuid4()), "email": email, "created_at": now_iso()}}, upsert=True)
    return {"success": True, "message": "Your topics are saved."}


@api_router.post("/newsletter/follow")
async def follow_topic(body: FollowIn):
    email = body.email.lower()
    if body.kind == "sector" and body.slug not in SECTORS:
        raise HTTPException(status_code=400, detail="Unknown sector")
    if body.kind == "agency" and body.slug not in AGENCIES:
        raise HTTPException(status_code=400, detail="Unknown agency")
    field = "interests_sectors" if body.kind == "sector" else "interests_agencies"
    await db.subscribers.update_one({"email": email},
        {"$addToSet": {field: body.slug},
         "$setOnInsert": {"id": str(uuid.uuid4()), "email": email, "created_at": now_iso()}}, upsert=True)
    return {"success": True, "message": "Done — you'll get this in your Monday brief.", "prefs_url": _prefs_url(email)}


async def _compile_sector_digest_groups(sub: dict) -> list:
    sec = sub.get("interests_sectors") or []
    ag = sub.get("interests_agencies") or []
    if not sec and not ag:
        sec, ag = DEFAULT_DIGEST_SECTORS, DEFAULT_DIGEST_AGENCIES
    groups = []
    for slug in sec:
        if slug not in SECTORS:
            continue
        nd = await db.sector_news.find_one({"_id": slug}, {"_id": 0})
        ins = await db.sector_insights.find_one({"slug": slug}, {"_id": 0}, sort=[("created_at", -1)])
        groups.append({"label": SECTORS[slug]["name"], "slug": slug, "kind": "sector",
                       "items": (nd or {}).get("items", [])[:4], "insight": (ins or {}).get("insight", "")})
    for slug in ag:
        if slug not in AGENCIES:
            continue
        nd = await db.entity_news.find_one({"_id": f"agency:{slug}"}, {"_id": 0})
        ins = await db.entity_insights.find_one({"kind": "agency", "slug": slug}, {"_id": 0}, sort=[("created_at", -1)])
        groups.append({"label": AGENCIES[slug]["name"], "slug": slug, "kind": "agency",
                       "items": (nd or {}).get("items", [])[:4], "insight": (ins or {}).get("insight", "")})
    return groups


async def _send_sector_digest():
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return {"sent": False, "reason": "smtp_not_configured"}
    subs = await db.subscribers.find({}, {"_id": 0}).to_list(5000)
    sent = 0
    for sub in subs:
        groups = [g for g in await _compile_sector_digest_groups(sub) if g.get("items")]
        if not groups:
            continue
        r = await asyncio.to_thread(send_sector_digest_email, sub["email"], sub.get("name", "there"),
                                    groups, PUBLIC_SITE, _unsub_url(sub["email"]), _prefs_url(sub["email"]))
        if r == "sent":
            sent += 1
    return {"sent": True, "emails": sent, "subscribers": len(subs)}


@api_router.post("/admin/sector-digest/send")
async def admin_send_sector_digest(admin: dict = Depends(require_admin)):
    return await _send_sector_digest()


@api_router.get("/admin/sector-digest/preview", response_class=HTMLResponse)
async def admin_sector_digest_preview(admin: dict = Depends(require_admin)):
    demo = {"interests_sectors": DEFAULT_DIGEST_SECTORS, "interests_agencies": DEFAULT_DIGEST_AGENCIES}
    groups = [g for g in await _compile_sector_digest_groups(demo) if g.get("items")]
    from emailer import render_sector_digest_html
    return HTMLResponse(render_sector_digest_html("there", groups, PUBLIC_SITE, PUBLIC_SITE + "/api/newsletter/unsubscribe?token=PREVIEW", PUBLIC_SITE + "/preferences?token=PREVIEW"))


def _decode_email(token: str, purpose: str) -> str:
    try:
        data = pyjwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        if data.get("purpose") == purpose:
            return data.get("email", "")
    except Exception:
        pass
    return ""


def _mail_page(heading: str, body_html: str, cta_label: str = "Back to site", cta_href: str = PUBLIC_SITE) -> str:
    return (
        '<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
        f'<title>{heading}</title></head>'
        '<body style="margin:0;background:#050505;color:#fff;font-family:Arial,sans-serif;display:flex;min-height:100vh;align-items:center;justify-content:center;">'
        '<div style="max-width:480px;padding:40px;text-align:center;">'
        '<div style="font-size:26px;font-weight:800;">S<span style="color:#C6F135;">K.</span></div>'
        f'<h1 style="font-size:22px;margin-top:24px;">{heading}</h1>{body_html}'
        f'<a href="{cta_href}" style="display:inline-block;margin-top:20px;background:#C6F135;color:#0A0A0A;padding:10px 22px;border-radius:999px;text-decoration:none;font-weight:600;font-size:14px;">{cta_label}</a>'
        '</div></body></html>'
    )


@api_router.get("/newsletter/unsubscribe")
async def newsletter_unsubscribe(token: str = ""):
    """One-click unsubscribe from the email footer link (no login needed)."""
    email = _decode_email(token, "unsubscribe")
    if email:
        await db.subscribers.delete_many({"email": email})
        resub = f"{PUBLIC_SITE}/api/newsletter/resubscribe?token={_resub_token(email)}"
        body = (f'<p style="color:#9ca3af;font-size:14px;">{email} will no longer receive the weekly Market Signals digest.</p>'
                f'<p style="color:#9ca3af;font-size:13px;">Changed your mind?</p>')
        return HTMLResponse(content=_mail_page("You're unsubscribed", body, "Resubscribe with one click", resub))
    return HTMLResponse(content=_mail_page("Link expired",
        '<p style="color:#9ca3af;font-size:14px;">This unsubscribe link is invalid or has already been used.</p>'))


@api_router.get("/newsletter/resubscribe")
async def newsletter_resubscribe(token: str = ""):
    """One-click opt back in from the unsubscribe confirmation page."""
    email = _decode_email(token, "resubscribe")
    if email:
        if not await db.subscribers.find_one({"email": email}):
            await db.subscribers.insert_one({"id": str(uuid.uuid4()), "email": email, "created_at": now_iso()})
        body = f'<p style="color:#9ca3af;font-size:14px;">Welcome back — {email} will receive the weekly Market Signals digest again.</p>'
        return HTMLResponse(content=_mail_page("You're resubscribed", body))
    return HTMLResponse(content=_mail_page("Link expired",
        '<p style="color:#9ca3af;font-size:14px;">This link is invalid or has expired.</p>'))


# ---------------- Consultation packages, availability & booking ----------------
# GST-inclusive prices in INR (the total the client is charged). Base + GST are derived from this.
GST_PCT = 18
PACKAGES = {
    "discovery": {"name": "Discovery Call", "total": 12000.0, "minutes": 30, "duration": "30 minutes",
                  "features": ["Focused problem framing", "Direct next-step guidance", "Ideal first touchpoint"]},
    "strategy": {"name": "1:1 Strategy Session", "total": 50000.0, "minutes": 60, "duration": "60 minutes",
                 "features": ["Deep strategy & fundraising review", "Actionable roadmap", "Follow-up notes"]},
    "deepdive": {"name": "Deep-Dive Advisory", "total": 120000.0, "minutes": 90, "duration": "90 minutes",
                 "features": ["Full business / deal deep-dive", "Bankability & scaling plan", "Priority follow-up access"]},
}


def _pkg_amounts(pkg: dict) -> dict:
    total = float(pkg["total"])
    base = round(total / (1 + GST_PCT / 100), 2)
    gst = round(total - base, 2)
    return {"base": base, "gst_pct": GST_PCT, "gst_amount": gst, "total": round(total, 2),
            "amount_paise": int(round(total * 100)), "currency": "INR"}


def _razorpay_client():
    kid = os.environ.get("RAZORPAY_KEY_ID")
    ks = os.environ.get("RAZORPAY_KEY_SECRET")
    if not kid or not ks:
        return None
    return razorpay.Client(auth=(kid, ks))

# Booking window: Mon–Fri, 09:30–19:00, 30-minute start slots.
WORK_START_MIN = 9 * 60 + 30
WORK_END_MIN = 19 * 60
SLOT_MIN = 30
WORK_DAYS = {0, 1, 2, 3, 4}
ACTIVE_BOOKING_STATUSES = ["pending_payment", "pending_confirmation", "confirmed"]


def _slot_times():
    out, t = [], WORK_START_MIN
    while t + SLOT_MIN <= WORK_END_MIN:
        out.append(f"{t // 60:02d}:{t % 60:02d}")
        t += SLOT_MIN
    return out


def _occupied_slots(start_hhmm: str, minutes: int):
    h, m = map(int, start_hhmm.split(":"))
    s = h * 60 + m
    return [b for b in _slot_times()
            if s <= (int(b[:2]) * 60 + int(b[3:])) < s + minutes]


def _monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


async def _get_availability_meta():
    meta = await db.app_meta.find_one({"_id": "availability"}) or {}
    if not meta.get("published_week_start"):
        meta["published_week_start"] = _monday_of(datetime.now(timezone.utc).date()).isoformat()
    meta.setdefault("blocked", {})
    meta.setdefault("buffer_minutes", 0)
    meta.setdefault("reminder_leads", [24])
    meta.setdefault("cancel_cutoff_hours", 24)
    return meta


async def _booked_slots_for(dates: list, buffer_min: int = 0):
    out = {d: set() for d in dates}
    cur = db.consultations.find(
        {"slot_date": {"$in": dates}, "status": {"$in": ACTIVE_BOOKING_STATUSES}},
        {"_id": 0, "slot_date": 1, "occupied": 1, "slot_time": 1, "minutes": 1})
    async for b in cur:
        d = b.get("slot_date")
        if buffer_min > 0 and b.get("slot_time") and b.get("minutes"):
            s = int(b["slot_time"][:2]) * 60 + int(b["slot_time"][3:])
            lo, hi = s - buffer_min, s + b["minutes"] + buffer_min
            blocked = [t for t in _slot_times()
                       if not ((int(t[:2]) * 60 + int(t[3:])) + SLOT_MIN <= lo or (int(t[:2]) * 60 + int(t[3:])) >= hi)]
        else:
            blocked = b.get("occupied") or ([b["slot_time"]] if b.get("slot_time") else [])
        out.setdefault(d, set()).update(blocked)
    return out


def _week_days(week_start: date):
    return [week_start + timedelta(days=i) for i in range(7)
            if (week_start + timedelta(days=i)).weekday() in WORK_DAYS]


@api_router.get("/consultation/packages")
async def get_packages():
    return [{"id": k, **v, **_pkg_amounts(v)} for k, v in PACKAGES.items()]


@api_router.get("/payments/config")
async def payments_config():
    return {"key_id": os.environ.get("RAZORPAY_KEY_ID", ""), "enabled": _razorpay_client() is not None, "currency": "INR"}


@api_router.get("/consultation/availability")
async def public_availability():
    meta = await _get_availability_meta()
    ws = date.fromisoformat(meta["published_week_start"])
    blocked = meta.get("blocked", {})
    buffer_min = int(meta.get("buffer_minutes", 0) or 0)
    days = _week_days(ws)
    date_strs = [d.isoformat() for d in days]
    booked = await _booked_slots_for(date_strs, buffer_min)
    now = datetime.now(timezone.utc)
    all_slots = _slot_times()
    out_days = []
    for d in days:
        ds = d.isoformat()
        avail = []
        for t in all_slots:
            if t in (blocked.get(ds) or []):
                continue
            if t in booked.get(ds, set()):
                continue
            h, m = map(int, t.split(":"))
            if datetime(d.year, d.month, d.day, h, m, tzinfo=timezone.utc) <= now:
                continue
            avail.append(t)
        if avail:
            out_days.append({"date": ds, "weekday": d.strftime("%A"),
                             "label": d.strftime("%a, %d %b"), "slots": avail})
    out_dates = {x["date"] for x in out_days}
    today = now.date()
    full_days = [{"date": d.isoformat(), "label": d.strftime("%a, %d %b")}
                 for d in days if d.isoformat() not in out_dates and d > today]
    return {"week_start": ws.isoformat(), "days": out_days, "full_days": full_days,
            "cancel_cutoff_hours": int(meta.get("cancel_cutoff_hours", 24) or 0),
            "hours": "09:30\u201319:00", "days_label": "Mon\u2013Fri"}


class BookIn(BaseModel):
    package_id: str
    name: str
    email: EmailStr
    phone: Optional[str] = ""
    area: Optional[str] = ""
    message: Optional[str] = ""
    date: str
    time: str
    captcha_token: Optional[str] = None


@api_router.post("/consultation/book")
async def book_consultation(body: BookIn, request: Request, background_tasks: BackgroundTasks):
    verify_captcha(body.captcha_token, _client_ip(request), request)
    pkg = PACKAGES.get(body.package_id)
    if not pkg:
        raise HTTPException(status_code=400, detail="Invalid package")
    client = _razorpay_client()
    if not client:
        raise HTTPException(status_code=503, detail="Payments are not configured yet. Please try again shortly.")
    try:
        d = date.fromisoformat(body.date)
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date")
    if d.weekday() not in WORK_DAYS or body.time not in _slot_times():
        raise HTTPException(status_code=400, detail="Slot is outside available hours.")
    meta = await _get_availability_meta()
    ws = date.fromisoformat(meta["published_week_start"])
    if not (ws <= d < ws + timedelta(days=7)):
        raise HTTPException(status_code=400, detail="Please pick a slot within the published week.")
    now = datetime.now(timezone.utc)
    h, m = map(int, body.time.split(":"))
    if datetime(d.year, d.month, d.day, h, m, tzinfo=timezone.utc) <= now:
        raise HTTPException(status_code=400, detail="That time has passed.")
    occupied = _occupied_slots(body.time, pkg["minutes"])
    blocked = set(meta.get("blocked", {}).get(body.date, []))
    buffer_min = int(meta.get("buffer_minutes", 0) or 0)
    booked = await _booked_slots_for([body.date], buffer_min)
    if blocked & set(occupied) or booked.get(body.date, set()) & set(occupied):
        raise HTTPException(status_code=409, detail="Sorry, that slot was just taken. Please choose another.")
    amt = _pkg_amounts(pkg)
    bid = str(uuid.uuid4())
    try:
        order = await asyncio.to_thread(client.order.create, {
            "amount": amt["amount_paise"], "currency": "INR", "payment_capture": 1,
            "receipt": bid[:40], "notes": {"package": pkg["name"], "email": body.email.lower()}})
    except Exception:
        logger.exception("razorpay order create failed")
        raise HTTPException(status_code=502, detail="Could not start the payment. Please try again.")
    doc = {
        "id": bid, "name": body.name, "email": body.email.lower(),
        "phone": body.phone or "", "company": "", "area": body.area or pkg["name"],
        "message": body.message or "", "status": "pending_payment",
        "package": pkg["name"], "package_id": body.package_id,
        "amount": amt["base"], "gst_pct": GST_PCT, "gst_amount": amt["gst_amount"], "amount_total": amt["total"],
        "currency": "INR", "paid": False,
        "razorpay_order_id": order["id"], "amount_paise": amt["amount_paise"],
        "minutes": pkg["minutes"], "slot_date": body.date, "slot_time": body.time,
        "occupied": occupied, "source": "booking-form", "created_at": now_iso(),
    }
    await db.consultations.insert_one(doc)
    return {"success": True, "status": "pending_payment", "booking_id": bid,
            "order_id": order["id"], "amount": amt["amount_paise"], "currency": "INR",
            "key_id": os.environ.get("RAZORPAY_KEY_ID", ""),
            "package": pkg["name"], "breakdown": {"base": amt["base"], "gst_pct": GST_PCT,
                                                  "gst_amount": amt["gst_amount"], "total": amt["total"]},
            "prefill": {"name": body.name, "email": body.email.lower(), "contact": body.phone or ""}}


class PaymentVerifyIn(BaseModel):
    booking_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@api_router.post("/payments/verify")
async def verify_payment(body: PaymentVerifyIn, request: Request, background_tasks: BackgroundTasks):
    client = _razorpay_client()
    if not client:
        raise HTTPException(status_code=503, detail="Payments are not configured.")
    b = await db.consultations.find_one({"id": body.booking_id})
    if not b or b.get("razorpay_order_id") != body.razorpay_order_id:
        raise HTTPException(status_code=404, detail="Booking not found for this payment.")
    if b.get("paid"):
        return {"success": True, "status": b.get("status", "pending_confirmation")}
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": body.razorpay_order_id,
            "razorpay_payment_id": body.razorpay_payment_id,
            "razorpay_signature": body.razorpay_signature})
    except Exception:
        raise HTTPException(status_code=400, detail="Payment could not be verified.")
    await _mark_booking_paid(b, body.razorpay_payment_id)
    return {"success": True, "status": "pending_confirmation",
            "message": "Payment received! Your slot is reserved and pending confirmation — we'll confirm your session shortly."}


@api_router.post("/payments/abandon/{bid}")
async def abandon_payment(bid: str):
    """Client left checkout without paying. Keep the slot held and timestamp it for the nudge; the scheduler releases it if still unpaid after 24h."""
    await db.consultations.update_one(
        {"id": bid, "status": "pending_payment", "paid": {"$ne": True}},
        {"$set": {"abandoned_at": now_iso()}})
    return {"success": True}


@api_router.get("/payments/resume/{bid}")
async def resume_payment(bid: str):
    """Reopen checkout for an unpaid booking (used by the abandoned-cart nudge link)."""
    b = await db.consultations.find_one({"id": bid}, {"_id": 0})
    if not b or b.get("paid") or b.get("status") != "pending_payment":
        raise HTTPException(status_code=404, detail="This booking is no longer awaiting payment.")
    return {"booking_id": bid, "order_id": b.get("razorpay_order_id"), "amount": b.get("amount_paise"),
            "currency": "INR", "key_id": os.environ.get("RAZORPAY_KEY_ID", ""), "package": b.get("package"),
            "slot_date": b.get("slot_date"), "slot_time": b.get("slot_time"),
            "breakdown": {"base": b.get("amount"), "gst_pct": b.get("gst_pct", GST_PCT),
                          "gst_amount": b.get("gst_amount"), "total": b.get("amount_total")},
            "prefill": {"name": b.get("name"), "email": b.get("email"), "contact": b.get("phone", "")}}


# ---------------- GST tax invoice config + numbering ----------------
def _gst_config() -> dict:
    gstin = os.environ.get("GST_GSTIN", "").strip()
    return {
        "enabled": bool(gstin), "gstin": gstin,
        "legal_name": os.environ.get("GST_LEGAL_NAME", "").strip(),
        "address": os.environ.get("GST_ADDRESS", "").strip(),
        "state": os.environ.get("GST_STATE", "").strip(),
        "state_code": os.environ.get("GST_STATE_CODE", "").strip(),
        "sac": os.environ.get("GST_SAC", "998311").strip() or "998311",
        "prefix": os.environ.get("GST_INVOICE_PREFIX", "").strip(),
    }


async def _next_invoice_no() -> str:
    doc = await db.app_meta.find_one_and_update(
        {"_id": "invoice_seq"}, {"$inc": {"n": 1}}, upsert=True, return_document=True)
    n = (doc or {}).get("n", 1)
    return f"{_gst_config()['prefix']}{n:05d}"


async def _mark_booking_paid(b: dict, payment_id: str) -> bool:
    """Idempotently mark a booking paid, generate its invoice, and fire receipt/invoice/alert emails."""
    if not b or b.get("paid"):
        return False
    gst = _gst_config()
    upd = {"status": "pending_confirmation", "paid": True, "razorpay_payment_id": payment_id, "paid_at": now_iso()}
    if gst["enabled"]:
        upd["invoice_no"] = await _next_invoice_no()
        upd["invoice_at"] = now_iso()
    res = await db.consultations.update_one({"id": b["id"], "paid": {"$ne": True}}, {"$set": upd})
    if res.modified_count == 0:
        return False  # another path (webhook/verify) already finalized it
    b.update(upd)
    asyncio.create_task(asyncio.to_thread(send_payment_receipt_email, b["email"], b))
    if gst["enabled"]:
        asyncio.create_task(asyncio.to_thread(send_gst_invoice_email, b["email"], b, gst))
    admin_to = os.environ.get("BOOKING_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
    if admin_to:
        asyncio.create_task(asyncio.to_thread(send_new_booking_alert_email, admin_to, b))
    return True


@api_router.post("/payments/webhook")
async def payments_webhook(request: Request):
    """Server-side confirmation backup — captures payments even if the client's browser drops."""
    secret = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "").strip()
    body = await request.body()
    if not secret:
        logger.warning("razorpay webhook received but no secret configured")
        return {"ok": True, "ignored": "no_secret"}
    sig = request.headers.get("X-Razorpay-Signature", "")
    client = _razorpay_client()
    try:
        client.utility.verify_webhook_signature(body.decode("utf-8"), sig, secret)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")
    try:
        payload = json.loads(body)
        event = payload.get("event", "")
        entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = entity.get("order_id")
        payment_id = entity.get("id")
        if event == "payment.captured" and order_id:
            b = await db.consultations.find_one({"razorpay_order_id": order_id})
            if b:
                await _mark_booking_paid(b, payment_id)
    except Exception:
        logger.exception("razorpay webhook handling error")
    return {"ok": True}


async def _process_pending_payments():
    """Nudge abandoned checkouts (after 1h) and release stale holds (after 24h)."""
    now = datetime.now(timezone.utc)
    nudge_before = (now - timedelta(hours=1)).isoformat()
    release_before = (now - timedelta(hours=24)).isoformat()
    # Release stale holds.
    stale = await db.consultations.find(
        {"status": "pending_payment", "paid": {"$ne": True}, "created_at": {"$lt": release_before}}).to_list(200)
    for b in stale:
        await db.consultations.update_one(
            {"id": b["id"], "status": "pending_payment", "paid": {"$ne": True}},
            {"$set": {"status": "expired", "expired_at": now.isoformat()}})
        if b.get("slot_date"):
            await _notify_waitlist(b["slot_date"])
    # Nudge (once) checkouts idle > 1h.
    if os.environ.get("GMAIL_APP_PASSWORD"):
        pend = await db.consultations.find(
            {"status": "pending_payment", "paid": {"$ne": True}, "nudged_at": {"$exists": False},
             "created_at": {"$lt": nudge_before, "$gte": release_before}}).to_list(200)
        for b in pend:
            resume_url = f"{PUBLIC_SITE}/resume/{b['id']}"
            try:
                await asyncio.to_thread(send_abandoned_nudge_email, b.get("email", ""), b, resume_url)
            except Exception:
                pass
            await db.consultations.update_one({"id": b["id"]}, {"$set": {"nudged_at": now_iso()}})
    await _nudge_abandoned_orders(now)
    await _deliver_scheduled_gifts()


async def _deliver_scheduled_gifts(now=None):
    """Deliver gifts whose scheduled date has arrived. Returns count sent."""
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return 0
    now_s = now_iso()
    due = await db.orders.find(
        {"paid": True, "gift_delivered": False, "gift_deliver_at": {"$ne": None, "$lte": now_s}}).to_list(200)
    sent = 0
    for o in due:
        gift = o.get("gift") or {}
        rec = (gift.get("recipient_email") or "").strip().lower()
        if rec:
            try:
                await asyncio.to_thread(send_gift_email, rec, gift.get("recipient_name", ""), o["name"],
                                        o["ref_title"], o["kind"], o.get("download_url", ""),
                                        gift.get("message", ""), PUBLIC_SITE)
                sent += 1
            except Exception:
                logger.warning("scheduled gift delivery failed", exc_info=True)
        await db.orders.update_one({"id": o["id"]}, {"$set": {"gift_delivered": True}})
    return sent


async def _nudge_abandoned_orders(now=None):
    """One-tap 'finish your order' nudge for abandoned product/cohort checkouts (idle 1h-24h, once). Returns count sent."""
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return 0
    now = now or datetime.now(timezone.utc)
    nudge_before = (now - timedelta(hours=1)).isoformat()
    keep_after = (now - timedelta(hours=24)).isoformat()
    pend = await db.orders.find(
        {"status": "pending_payment", "paid": {"$ne": True}, "nudged_at": {"$exists": False},
         "created_at": {"$lt": nudge_before, "$gte": keep_after}}).to_list(200)
    sent = 0
    for o in pend:
        page = "cohorts" if o.get("kind") == "cohort" else "products"
        ref_key = "cohort" if o.get("kind") == "cohort" else "product"
        code = o.get("promo_code") or ""
        resume_url = f"{PUBLIC_SITE}/{page}?{ref_key}={o.get('ref_id', '')}"
        label = ""
        if code:
            resume_url += f"&code={code}"
            p = await db.promo_codes.find_one({"code": code}, {"_id": 0, "type": 1, "value": 1})
            if p:
                label = f"{int(p['value'])}% off" if (p.get("type") or "percent") == "percent" else f"\u20b9{int(p['value'])} off"
        try:
            await asyncio.to_thread(send_commerce_abandoned_email, o.get("email", ""), o.get("name", ""),
                                    o.get("ref_title", "your order"), resume_url, code, label)
            sent += 1
        except Exception:
            logger.warning("commerce nudge failed", exc_info=True)
        await db.orders.update_one({"id": o["id"]}, {"$set": {"nudged_at": now_iso()}})
    return sent


async def _refund_booking(b: dict, reason: str = "") -> bool:
    """Full refund to the client's original payment method (Razorpay). Idempotent."""
    if not b or not b.get("paid") or b.get("refunded") or not b.get("razorpay_payment_id"):
        return False
    client = _razorpay_client()
    if not client:
        logger.warning("refund requested but Razorpay not configured: booking %s", b.get("id"))
        return False
    try:
        refund = await asyncio.to_thread(client.payment.refund, b["razorpay_payment_id"], {
            "amount": int(b.get("amount_paise", 0)) or None,
            "speed": "optimum",
            "notes": {"reason": reason or "Session not confirmed", "booking_id": b.get("id", "")}})
    except Exception:
        logger.exception("razorpay refund failed for booking %s", b.get("id"))
        return False
    upd = {"refunded": True, "refund_id": refund.get("id", ""), "refund_at": now_iso(), "refund_reason": reason or ""}
    await db.consultations.update_one({"id": b["id"]}, {"$set": upd})
    b.update(upd)
    try:
        await asyncio.to_thread(send_refund_email, b.get("email", ""), b, reason)
    except Exception:
        pass
    return True


# ---------------- Admin availability management ----------------
@api_router.get("/admin/availability")
async def admin_availability(week_start: Optional[str] = None, admin: dict = Depends(require_admin)):
    meta = await _get_availability_meta()
    published = meta["published_week_start"]
    ws = _monday_of(date.fromisoformat(week_start) if week_start else date.fromisoformat(published))
    days = _week_days(ws)
    date_strs = [d.isoformat() for d in days]
    blocked = meta.get("blocked", {})
    buffer_min = int(meta.get("buffer_minutes", 0) or 0)
    booked = await _booked_slots_for(date_strs, buffer_min)
    all_slots = _slot_times()
    out_days = []
    for d in days:
        ds = d.isoformat()
        slots = []
        for t in all_slots:
            state = "available"
            if t in booked.get(ds, set()):
                state = "booked"
            elif t in (blocked.get(ds) or []):
                state = "blocked"
            slots.append({"time": t, "state": state})
        out_days.append({"date": ds, "label": d.strftime("%a, %d %b"), "slots": slots})
    return {"week_start": ws.isoformat(), "published_week_start": published,
            "is_published": ws.isoformat() == published, "days": out_days,
            "slot_times": all_slots, "buffer_minutes": buffer_min,
            "reminder_leads": [int(h) for h in (meta.get("reminder_leads") or [])],
            "cancel_cutoff_hours": int(meta.get("cancel_cutoff_hours", 24) or 0)}


class BufferIn(BaseModel):
    minutes: int


@api_router.post("/admin/availability/buffer")
async def set_buffer(body: BufferIn, admin: dict = Depends(require_admin)):
    mins = max(0, min(120, body.minutes))
    meta = await _get_availability_meta()
    await db.app_meta.update_one({"_id": "availability"}, {"$set": {
        "buffer_minutes": mins, "published_week_start": meta["published_week_start"],
        "blocked": meta.get("blocked", {})}}, upsert=True)
    return {"success": True, "buffer_minutes": mins}


class RemindersIn(BaseModel):
    leads: list[int]


@api_router.post("/admin/availability/reminders")
async def set_reminders(body: RemindersIn, admin: dict = Depends(require_admin)):
    leads = sorted({int(h) for h in body.leads if int(h) in (2, 24)})
    meta = await _get_availability_meta()
    await db.app_meta.update_one({"_id": "availability"}, {"$set": {
        "reminder_leads": leads, "published_week_start": meta["published_week_start"],
        "blocked": meta.get("blocked", {})}}, upsert=True)
    return {"success": True, "reminder_leads": leads}


class CancelWindowIn(BaseModel):
    hours: int


@api_router.post("/admin/availability/cancel-window")
async def set_cancel_window(body: CancelWindowIn, admin: dict = Depends(require_admin)):
    hours = max(0, min(168, body.hours))
    meta = await _get_availability_meta()
    await db.app_meta.update_one({"_id": "availability"}, {"$set": {
        "cancel_cutoff_hours": hours, "published_week_start": meta["published_week_start"],
        "blocked": meta.get("blocked", {})}}, upsert=True)
    return {"success": True, "cancel_cutoff_hours": hours}


class WaitlistIn(BaseModel):
    name: str
    email: EmailStr
    package_id: Optional[str] = ""
    date: str
    captcha_token: Optional[str] = None


@api_router.post("/consultation/waitlist")
async def join_waitlist(body: WaitlistIn, request: Request):
    verify_captcha(body.captcha_token, _client_ip(request), request)
    pkg = PACKAGES.get(body.package_id) if body.package_id else None
    existing = await db.waitlist.find_one({"email": body.email.lower(), "date": body.date, "notified": {"$ne": True}})
    if existing:
        return {"success": True, "message": "You're already on the waitlist for that day."}
    await db.waitlist.insert_one({
        "id": str(uuid.uuid4()), "name": body.name, "email": body.email.lower(),
        "package_id": body.package_id or "", "package": (pkg or {}).get("name", ""),
        "date": body.date, "notified": False, "created_at": now_iso()})
    return {"success": True, "message": "You're on the waitlist \u2014 we'll email you if a slot opens for that day."}


@api_router.get("/admin/waitlist")
async def admin_waitlist(admin: dict = Depends(require_admin)):
    return await db.waitlist.find({}, {"_id": 0}).sort("created_at", -1).to_list(200)


async def _notify_waitlist(date_str: str):
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return  # keep entries un-notified until SMTP is live
    front = os.environ.get("WEBAUTHN_ORIGIN", "")
    book_url = f"{front}/#consult" if front else ""
    loop = asyncio.get_event_loop()
    entries = await db.waitlist.find({"date": date_str, "notified": {"$ne": True}}).to_list(100)
    for w in entries:
        if not w.get("email"):
            continue
        await loop.run_in_executor(None, send_waitlist_opening_email, w["email"],
                                   w.get("name", "there"), w.get("package", ""), date_str, book_url)
        await db.waitlist.update_one({"id": w["id"]}, {"$set": {"notified": True, "notified_at": now_iso()}})


class SlotToggleIn(BaseModel):
    date: str
    time: str
    blocked: bool


@api_router.post("/admin/availability/toggle")
async def toggle_slot(body: SlotToggleIn, admin: dict = Depends(require_admin)):
    meta = await _get_availability_meta()
    blocked = meta.get("blocked", {})
    day = set(blocked.get(body.date, []))
    day.add(body.time) if body.blocked else day.discard(body.time)
    if day:
        blocked[body.date] = sorted(day)
    else:
        blocked.pop(body.date, None)
    await db.app_meta.update_one({"_id": "availability"},
                                 {"$set": {"blocked": blocked, "published_week_start": meta["published_week_start"]}}, upsert=True)
    return {"success": True, "date": body.date, "time": body.time, "blocked": body.blocked}


class DayBlockIn(BaseModel):
    date: str
    blocked: bool


@api_router.post("/admin/availability/block-day")
async def block_day(body: DayBlockIn, admin: dict = Depends(require_admin)):
    meta = await _get_availability_meta()
    blocked = meta.get("blocked", {})
    if body.blocked:
        blocked[body.date] = _slot_times()
    else:
        blocked.pop(body.date, None)
    await db.app_meta.update_one({"_id": "availability"},
                                 {"$set": {"blocked": blocked, "published_week_start": meta["published_week_start"]}}, upsert=True)
    return {"success": True}


class PublishIn(BaseModel):
    week_start: str


@api_router.post("/admin/availability/publish")
async def publish_week(body: PublishIn, request: Request, admin: dict = Depends(require_admin)):
    ws = _monday_of(date.fromisoformat(body.week_start)).isoformat()
    meta = await _get_availability_meta()
    await db.app_meta.update_one({"_id": "availability"},
                                 {"$set": {"published_week_start": ws, "blocked": meta.get("blocked", {})}}, upsert=True)
    await audit(request, admin.get("email"), "availability_published", ws)
    return {"success": True, "published_week_start": ws}


# ---------------- Admin bookings queue ----------------
@api_router.get("/admin/bookings")
async def admin_bookings(admin: dict = Depends(require_admin)):
    return await db.consultations.find(
        {"slot_date": {"$exists": True}}, {"_id": 0}).sort("created_at", -1).to_list(500)


class BookingActionIn(BaseModel):
    date: Optional[str] = None
    time: Optional[str] = None
    reason: Optional[str] = ""
    meeting_link: Optional[str] = None


def _booking_token(bid: str) -> str:
    return pyjwt.encode({"purpose": "booking_manage", "bid": bid,
                         "exp": datetime.now(timezone.utc) + timedelta(days=60)},
                        get_jwt_secret(), algorithm="HS256")


def _read_booking_token(tok: str) -> Optional[str]:
    try:
        d = pyjwt.decode(tok, get_jwt_secret(), algorithms=["HS256"])
        return d.get("bid") if d.get("purpose") == "booking_manage" else None
    except Exception:
        return None


def _booking_manage_url(bid: str) -> str:
    front = os.environ.get("WEBAUTHN_ORIGIN", "")
    return f"{front}/booking/manage?token={_booking_token(bid)}" if front else ""


def _schedule_booking_email(booking, background_tasks):
    try:
        start = _dt.fromisoformat(f"{booking['slot_date']}T{booking['slot_time']}:00+00:00")
        end = start + timedelta(minutes=booking.get("minutes", 60))
        background_tasks.add_task(send_booking_email, booking["id"], booking.get("name", "Client"),
                                  booking.get("email", ""), booking.get("package", "Consultation"),
                                  start, end, booking.get("meeting_link", ""), _booking_manage_url(booking["id"]))
    except Exception:
        logger.exception("booking email schedule failed")


@api_router.post("/admin/bookings/{bid}/confirm")
async def confirm_booking(bid: str, body: BookingActionIn, request: Request, background_tasks: BackgroundTasks, admin: dict = Depends(require_admin)):
    b = await db.consultations.find_one({"id": bid})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    upd = {"status": "confirmed"}
    if body.meeting_link is not None:
        upd["meeting_link"] = body.meeting_link.strip()
    await db.consultations.update_one({"id": bid}, {"$set": upd})
    b.update(upd)
    await _apply_calendar_sync(bid, b, "create")
    _schedule_booking_email(b, background_tasks)
    await audit(request, admin.get("email"), "booking_confirmed", bid)
    return {"success": True}


@api_router.post("/admin/bookings/{bid}/decline")
async def decline_booking(bid: str, body: BookingActionIn, request: Request, admin: dict = Depends(require_admin)):
    res = await db.consultations.update_one(
        {"id": bid}, {"$set": {"status": "declined", "decline_reason": body.reason or ""}})
    if res.matched_count == 0:
        raise HTTPException(status_code=404, detail="Booking not found")
    b = await db.consultations.find_one({"id": bid})
    if b and b.get("gcal_event_id"):
        await sync_booking_to_calendar(b, "delete")
        await db.consultations.update_one({"id": bid}, {"$unset": {"gcal_event_id": ""}})
    refunded = await _refund_booking(b, body.reason or "Session could not be accommodated") if b else False
    await audit(request, admin.get("email"), "booking_declined", bid)
    return {"success": True, "refunded": refunded}


@api_router.post("/admin/bookings/{bid}/reschedule")
async def reschedule_booking(bid: str, body: BookingActionIn, request: Request, background_tasks: BackgroundTasks, admin: dict = Depends(require_admin)):
    b = await db.consultations.find_one({"id": bid})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found")
    if not body.date or not body.time or body.time not in _slot_times():
        raise HTTPException(status_code=400, detail="Provide a valid new date and time.")
    occupied = _occupied_slots(body.time, b.get("minutes", 60))
    upd = {"slot_date": body.date, "slot_time": body.time, "occupied": occupied,
           "status": "confirmed", "reminders_sent": []}
    if body.meeting_link:
        upd["meeting_link"] = body.meeting_link.strip()
    await db.consultations.update_one({"id": bid}, {"$set": upd, "$unset": {"reminder_sent": ""}})
    b.update(upd)
    await _apply_calendar_sync(bid, b, "update" if b.get("gcal_event_id") else "create")
    _schedule_booking_email(b, background_tasks)
    await audit(request, admin.get("email"), "booking_rescheduled", bid, meta=f"{body.date} {body.time}")
    return {"success": True}


# ---------------- Client self-service (cancel / request reschedule via email link) ----------------
class TokenIn(BaseModel):
    token: str
    message: Optional[str] = ""


@api_router.get("/booking/manage")
async def booking_manage(token: str):
    bid = _read_booking_token(token)
    if not bid:
        raise HTTPException(status_code=400, detail="This link is invalid or has expired.")
    b = await db.consultations.find_one({"id": bid},
        {"_id": 0, "name": 1, "package": 1, "slot_date": 1, "slot_time": 1, "status": 1,
         "meeting_link": 1, "reschedule_requested": 1})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found.")
    meta = await _get_availability_meta()
    cutoff = int(meta.get("cancel_cutoff_hours", 24) or 0)
    can_cancel = True
    if cutoff > 0 and b.get("slot_date") and b.get("slot_time") and b.get("status") == "confirmed":
        dt = datetime.fromisoformat(f"{b['slot_date']}T{b['slot_time']}:00").replace(tzinfo=IST_TZ)
        can_cancel = (dt.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds() >= cutoff * 3600
    b["can_cancel"] = can_cancel
    b["cancel_cutoff_hours"] = cutoff
    return b


@api_router.post("/booking/cancel")
async def booking_cancel(body: TokenIn, background_tasks: BackgroundTasks):
    bid = _read_booking_token(body.token)
    if not bid:
        raise HTTPException(status_code=400, detail="This link is invalid or has expired.")
    b = await db.consultations.find_one({"id": bid})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if b.get("status") == "cancelled":
        return {"success": True, "status": "cancelled"}
    meta = await _get_availability_meta()
    cutoff = int(meta.get("cancel_cutoff_hours", 24) or 0)
    if cutoff > 0 and b.get("slot_date") and b.get("slot_time") and b.get("status") == "confirmed":
        dt = datetime.fromisoformat(f"{b['slot_date']}T{b['slot_time']}:00").replace(tzinfo=IST_TZ)
        if (dt.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds() < cutoff * 3600:
            raise HTTPException(status_code=400, detail=f"Cancellations within {cutoff} hours of the session can't be made online. Please contact us directly and we'll help.")
    await db.consultations.update_one({"id": bid}, {"$set": {"status": "cancelled"}})
    if b.get("gcal_event_id"):
        b["status"] = "cancelled"
        await sync_booking_to_calendar(b, "delete")
        await db.consultations.update_one({"id": bid}, {"$unset": {"gcal_event_id": ""}})
    if b.get("slot_date"):
        await _notify_waitlist(b["slot_date"])
    refunded = await _refund_booking(b, "Client cancelled the session")
    admin_to = os.environ.get("BOOKING_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
    if admin_to:
        note = dict(b); note["message"] = f"CLIENT CANCELLED this session ({b.get('slot_date')} {b.get('slot_time')} IST)."
        background_tasks.add_task(send_new_booking_alert_email, admin_to, note)
    return {"success": True, "status": "cancelled", "refunded": refunded}


@api_router.post("/booking/reschedule-request")
async def booking_reschedule_request(body: TokenIn, background_tasks: BackgroundTasks):
    bid = _read_booking_token(body.token)
    if not bid:
        raise HTTPException(status_code=400, detail="This link is invalid or has expired.")
    b = await db.consultations.find_one({"id": bid})
    if not b:
        raise HTTPException(status_code=404, detail="Booking not found.")
    await db.consultations.update_one({"id": bid}, {"$set": {
        "reschedule_requested": True, "reschedule_note": (body.message or "")[:500]}})
    admin_to = os.environ.get("BOOKING_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
    if admin_to:
        note = dict(b); note["message"] = f"CLIENT REQUESTED A RESCHEDULE. Note: {body.message or '(none)'}"
        background_tasks.add_task(send_new_booking_alert_email, admin_to, note)
    return {"success": True}


# ---------------- Services ----------------
_SERVICE_ORDER = ["business-strategy", "ma-advisory", "fund-raising", "premium-consultation",
                  "business-coaching", "re-storage-hydrogen", "green-climate-financing", "asset-monetisation"]


@api_router.get("/services")
async def list_services():
    ordered = sorted(SERVICE_PAGES, key=lambda s: _SERVICE_ORDER.index(s["slug"]) if s["slug"] in _SERVICE_ORDER else 99)
    return [{"slug": s["slug"], "title": s["title"], "tagline": s["tagline"],
             "overview": s["overview"], "portrait": s["portrait"], "hero_image": s["hero_image"],
             "signature": s.get("signature", False)}
            for s in ordered]


@api_router.get("/services/{slug}")
async def get_service(slug: str):
    for s in SERVICE_PAGES:
        if s["slug"] == slug:
            return s
    raise HTTPException(status_code=404, detail="Service not found")


@api_router.get("/strategy-tools")
async def list_strategy_tools():
    from strategy_tools import STRATEGY_TOOLS
    return [{"slug": t["slug"], "name": t["name"], "category": t["category"],
             "tagline": t["tagline"], "what_it_is": t["what_it_is"]} for t in STRATEGY_TOOLS]


@api_router.get("/strategy-tools-bundle.pdf")
async def strategy_toolkit_bundle():
    from strategy_pdf import build_toolkit_bundle_pdf
    pdf = await asyncio.to_thread(build_toolkit_bundle_pdf)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="SK-Complete-Strategy-Toolkit.pdf"'})


@api_router.get("/strategy-tools/{slug}.pdf")
async def strategy_tool_pdf(slug: str):
    from strategy_tools import tool_by_slug
    from strategy_pdf import build_tool_pdf
    t = tool_by_slug(slug)
    if not t:
        raise HTTPException(status_code=404, detail="Tool not found")
    pdf = await asyncio.to_thread(build_tool_pdf, t)
    fname = f"SK-{slug}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{fname}"'})


@api_router.get("/strategy-tools/{slug}")
async def get_strategy_tool(slug: str):
    from strategy_tools import tool_by_slug
    t = tool_by_slug(slug)
    if not t:
        raise HTTPException(status_code=404, detail="Tool not found")
    return t


@api_router.get("/strategy-insights")
async def list_strategy_insights():
    from strategy_insights import STRATEGY_INSIGHTS
    return [{"slug": a["slug"], "title": a["title"], "dek": a["dek"],
             "read_time": a["read_time"], "category": a["category"]} for a in STRATEGY_INSIGHTS]


@api_router.get("/strategy-insights/{slug}")
async def get_strategy_insight(slug: str):
    from strategy_insights import insight_by_slug
    a = insight_by_slug(slug)
    if not a:
        raise HTTPException(status_code=404, detail="Insight not found")
    return a


# ---------------- Service Insights engine (SK Insights, per service) ----------------
def _slugify(s: str) -> str:
    import re
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s[:80]


async def _generate_service_blog(service_slug: str, service_title: str, title: str, category: str) -> dict:
    prompt = (
        "You are a senior strategy partner writing for Sudarshan Karweer's advisory platform. "
        "Sudarshan is an ex-EY Big-4 advisory leader (23+ years, 60+ projects, $2B+ debt syndication, "
        "M&A incl. airline loyalty-programme carve-outs, over $3bn raised, RE/BESS/hydrogen/climate-finance, "
        "public-asset monetisation like MSRTC bus depots). Write a McKinsey/BCG/Bain-caliber long-form insight article.\n\n"
        f"SERVICE CONTEXT: {service_title}\n"
        f"CATEGORY: {category}\n"
        f"ARTICLE TITLE: {title}\n\n"
        "Rules:\n"
        "- Write grounded, evidence-led analysis using PUBLIC-DOMAIN facts about the named companies/deals. "
        "Do NOT invent precise figures, dates, quotes or private data; when you reference numbers keep them "
        "widely-reported and round, and frame as analysis, not reporting.\n"
        "- Voice: crisp, senior, structured, 'so-what' oriented. No fluff, no hype, no emojis, no marketing tone.\n"
        "- Cover, where relevant, current practice, what worked/failed and WHY, and practical learnings.\n"
        "- If the category involves technology, address the AI/technology angle concretely.\n\n"
        "Return STRICT JSON only (no markdown, no code fences) with keys:\n"
        "  dek: string, 25-40 word standfirst that sharpens the argument.\n"
        "  read_time: string like '7 min read'.\n"
        "  sections: array of 5-6 objects {h: 6-10 word section heading, p: 70-120 word paragraph}. "
        "Make the analysis specific to the named case, not generic.\n"
        "  key_takeaways: array of exactly 3 strings, each a punchy 12-20 word lesson.\n"
        "  sk_insight: object {take: 45-70 word first-person view as Sudarshan with a distinctive, contrarian-but-grounded angle; "
        "corporate_relevance: 35-55 words on exactly what a corporate leader should DO about this now}.\n"
        "  tags: array of 3 short tag strings.\n"
        "Output JSON only."
    )
    chat = new_chat("insight-" + str(uuid.uuid4())).with_model("anthropic", "claude-sonnet-4-6")
    text = ""
    async for ev in chat.stream_message(UserMessage(text=prompt)):
        if isinstance(ev, TextDelta):
            text += ev.content
        elif isinstance(ev, StreamDone):
            break
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    data = json.loads(text)
    sections = []
    for s in (data.get("sections") or []):
        if isinstance(s, dict) and s.get("h") and s.get("p"):
            sections.append({"h": str(s["h"]).strip(), "p": str(s["p"]).strip()})
    ski = data.get("sk_insight") or {}
    return {
        "dek": str(data.get("dek") or "").strip(),
        "read_time": str(data.get("read_time") or "7 min read").strip(),
        "sections": sections[:6],
        "key_takeaways": [str(x).strip() for x in (data.get("key_takeaways") or []) if str(x).strip()][:3],
        "sk_insight": {"take": str(ski.get("take") or "").strip(),
                       "corporate_relevance": str(ski.get("corporate_relevance") or "").strip()},
        "tags": [str(x).strip() for x in (data.get("tags") or []) if str(x).strip()][:3],
    }


_insights_gen_lock = asyncio.Lock()


async def _store_blog(doc: dict, archive_previous: bool = False):
    """Upsert a blog; optionally snapshot the prior version into the archive first."""
    prev = await db.service_blogs.find_one({"slug": doc["slug"]}, {"_id": 0})
    version = 1
    if prev:
        version = int(prev.get("version", 1))
        if archive_previous:
            snap = {k: v for k, v in prev.items() if k != "related"}
            snap["archive_id"] = str(uuid.uuid4())
            snap["archived_at"] = now_iso()
            await db.service_blogs_archive.insert_one(snap)
            version += 1
    doc["version"] = version
    doc["updated_at"] = now_iso()
    if prev and not archive_previous:
        doc["published_at"] = prev.get("published_at") or doc.get("published_at")
    await db.service_blogs.replace_one({"slug": doc["slug"]}, doc, upsert=True)


async def _build_blog_doc(service_slug, service_title, title, category, idx):
    from insights_data import hero_for
    body = await _generate_service_blog(service_slug, service_title, title, category)
    return {
        "slug": _slugify(title), "service_slug": service_slug, "service_title": service_title,
        "title": title, "category": category,
        "hero_image": hero_for(service_slug, category, idx),
        "sort": idx, "published_at": now_iso(), **body,
    }


async def _generate_all_service_insights(force: bool = False, concurrency: int = 5) -> dict:
    """Generate & store 10 blogs per service. Skips services already populated unless force."""
    from insights_data import TOPIC_PLAN
    from services_data import SERVICES
    title_by_slug = {s["slug"]: s["title"] for s in SERVICES}
    sem = asyncio.Semaphore(concurrency)
    generated, failed = 0, 0

    async def one(service_slug, idx, title, category):
        nonlocal generated, failed
        existing = await db.service_blogs.find_one({"slug": _slugify(title)})
        if existing and not force:
            return
        async with sem:
            try:
                doc = await _build_blog_doc(service_slug, title_by_slug.get(service_slug, service_slug), title, category, idx)
            except Exception:
                logger.exception("service insight generation failed: %s", title)
                failed += 1
                return
        await _store_blog(doc, archive_previous=force)
        generated += 1

    tasks = []
    for service_slug, topics in TOPIC_PLAN.items():
        for idx, (title, category) in enumerate(topics):
            tasks.append(one(service_slug, idx, title, category))
    await asyncio.gather(*tasks)
    return {"generated": generated, "failed": failed}


async def _refresh_stale_insights(max_items: int = 4, older_than_hours: int = 20) -> int:
    """Rolling dynamic refresh: regenerate the few oldest blogs, archiving prior versions.
    Cycles the whole set fresh over time. Guarded so it runs a small batch per call."""
    if _insights_gen_lock.locked():
        return 0
    from insights_data import TOPIC_PLAN
    from services_data import SERVICES
    title_by_slug = {s["slug"]: s["title"] for s in SERVICES}
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=older_than_hours)).isoformat()
    stale = await db.service_blogs.find(
        {"$or": [{"updated_at": {"$lt": cutoff}}, {"updated_at": {"$exists": False}}]},
        {"_id": 0, "slug": 1, "service_slug": 1, "title": 1, "category": 1, "sort": 1}
    ).sort("updated_at", 1).to_list(max_items)
    if not stale:
        return 0
    done = 0
    async with _insights_gen_lock:
        for b in stale:
            try:
                doc = await _build_blog_doc(b["service_slug"], title_by_slug.get(b["service_slug"], b["service_slug"]),
                                            b["title"], b.get("category", ""), b.get("sort", 0))
                await _store_blog(doc, archive_previous=True)
                done += 1
            except Exception:
                logger.exception("stale insight refresh failed: %s", b.get("title"))
    return done


def _blog_card(d: dict) -> dict:
    return {"slug": d.get("slug"), "service_slug": d.get("service_slug"),
            "service_title": d.get("service_title"), "title": d.get("title"),
            "dek": d.get("dek"), "category": d.get("category"),
            "hero_image": d.get("hero_image"), "read_time": d.get("read_time"),
            "tags": d.get("tags", []), "published_at": d.get("published_at")}


@api_router.get("/service-insights")
async def list_service_insights(service: Optional[str] = None, category: Optional[str] = None, limit: int = 200):
    q = {}
    if service:
        q["service_slug"] = service
    if category:
        q["category"] = category
    docs = await db.service_blogs.find(q, {"_id": 0}).sort("sort", 1).to_list(limit)
    return [_blog_card(d) for d in docs]


@api_router.get("/service-insights/services")
async def service_insights_services():
    """Per-service counts for the hub filter."""
    from services_data import SERVICES
    counts = {}
    async for d in db.service_blogs.aggregate([{"$group": {"_id": "$service_slug", "n": {"$sum": 1}}}]):
        counts[d["_id"]] = d["n"]
    return [{"slug": s["slug"], "title": s["title"], "count": counts.get(s["slug"], 0)}
            for s in SERVICES if counts.get(s["slug"], 0) > 0]


@api_router.get("/service-insights/archive")
async def service_insights_archive(limit: int = 60, service: Optional[str] = None):
    """Past editions of blogs that have since been refreshed (newest snapshot first)."""
    q = {}
    if service:
        q["service_slug"] = service
    docs = await db.service_blogs_archive.find(q, {"_id": 0}).sort("archived_at", -1).to_list(min(limit, 200))
    return [{"archive_id": d.get("archive_id"), "slug": d.get("slug"), "title": d.get("title"),
             "service_title": d.get("service_title"), "service_slug": d.get("service_slug"),
             "category": d.get("category"), "version": d.get("version"),
             "hero_image": d.get("hero_image"), "dek": d.get("dek"),
             "read_time": d.get("read_time"), "archived_at": d.get("archived_at")} for d in docs]


@api_router.get("/service-insights/archive/{archive_id}")
async def service_insights_archive_item(archive_id: str):
    d = await db.service_blogs_archive.find_one({"archive_id": archive_id}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Archived edition not found")
    return d


@api_router.get("/archive")
async def unified_archive(type: str = "all", theme: str = "all", limit: int = 300):
    """Unified content archive across blogs, articles, videos, audio and market signals.
    Every item carries a normalised `theme` tag for cross-content filtering."""
    items = []
    want = (type or "all").lower()

    SERVICE_THEME = {
        "business-strategy": "Strategy", "ma-advisory": "M&A",
        "fund-raising": "Capital & Finance", "premium-consultation": "Leadership",
        "re-storage-hydrogen": "Energy & Climate", "green-climate-financing": "Energy & Climate",
        "asset-monetisation": "Economy", "business-coaching": "Leadership",
    }
    THEME_RULES = [
        ("Technology", ["artificial intelligence", "machine intelligence", "technology", "digital", "software", "data", "automation"]),
        ("M&A", ["m&a", "merger", "acquisition", "carve-out", "carve out", "takeover", "consolidation"]),
        ("Capital & Finance", ["capital", "fundrais", "fund raise", "ipo", "bond", "invest", "finance", "valuation", "debt", "equity", "bankable"]),
        ("Energy & Climate", ["energy", "renewable", "solar", "storage", "bess", "hydrogen", "climate", "green", "carbon", "sustainab", "esg", "wind"]),
        ("Leadership", ["leader", "coach", "ceo", "founder", "culture", "talent", "succession", "mindset", "executive"]),
        ("Economy", ["econom", "macro", "policy", "inflation", "gdp", "monetis", "infrastructure", "government", "public asset"]),
        ("Markets", ["market", "signal", "sector", "competit", "consumer"]),
        ("Strategy", ["strategy", "strategic", "portfolio", "market entry", "feasibility", "moat", "disruption", "growth"]),
    ]

    def classify(text: str) -> str:
        t = (text or "").lower()
        for th, kws in THEME_RULES:
            if any(k in t for k in kws):
                return th
        return "Strategy"

    async def add_blogs():
        docs = await db.service_blogs.find({}, {"_id": 0}).sort("updated_at", -1).to_list(200)
        for d in docs:
            th = "Technology" if d.get("category") == "AI & Technology" else SERVICE_THEME.get(d.get("service_slug"), "Strategy")
            items.append({"type": "blog", "title": d.get("title"), "subtitle": d.get("service_title"),
                          "image": d.get("hero_image"), "url": f"/insight/{d.get('slug')}",
                          "date": (d.get("updated_at") or d.get("published_at") or "")[:10],
                          "tag": d.get("category"), "theme": th, "external": False})
        arch = await db.service_blogs_archive.find({}, {"_id": 0}).sort("archived_at", -1).to_list(120)
        for d in arch:
            th = "Technology" if d.get("category") == "AI & Technology" else SERVICE_THEME.get(d.get("service_slug"), "Strategy")
            items.append({"type": "blog", "title": d.get("title"), "subtitle": f"{d.get('service_title')} · earlier edition",
                          "image": d.get("hero_image"), "url": f"/archive/edition/{d.get('archive_id')}",
                          "date": (d.get("archived_at") or "")[:10], "tag": "Earlier edition", "theme": th, "external": False})

    async def add_articles():
        docs = await db.articles.find({}, {"_id": 0}).sort("created_at", -1).to_list(120)
        for d in docs:
            items.append({"type": "article", "title": d.get("title"), "subtitle": d.get("category"),
                          "image": d.get("image"), "url": f"/insights/{d.get('slug')}",
                          "date": (d.get("created_at") or "")[:10], "tag": d.get("sector") or d.get("category"),
                          "theme": classify(f"{d.get('category','')} {d.get('sector','')} {d.get('title','')} {' '.join(d.get('tags',[]) or [])}"),
                          "external": False})

    async def add_signals():
        docs = await db.signals_archive.find({}, {"_id": 0}).sort("date", -1).to_list(90)
        for d in docs:
            items.append({"type": "signal", "title": d.get("hero_headline", "Market Signals"),
                          "subtitle": "Market Signals", "image": None, "url": f"/signals/{d.get('date')}",
                          "date": d.get("date"), "tag": "Market Signals", "theme": "Markets", "external": False})

    async def add_videos():
        try:
            vids = await asyncio.to_thread(curator.library, None, 40)
        except Exception:
            vids = []
        for v in vids:
            items.append({"type": "video", "title": v.get("title"), "subtitle": v.get("source"),
                          "image": v.get("thumbnail"),
                          "url": v.get("source_url") or (f"https://www.youtube.com/watch?v={v.get('video_id')}" if v.get("video_id") else ""),
                          "date": (v.get("published") or "")[:10],
                          "tag": (v.get("topics") or ["Learning"])[0] if v.get("topics") else "Learning",
                          "theme": classify(f"{v.get('title','')} {' '.join(v.get('topics',[]) or [])}"),
                          "external": True})

    def add_audio():
        for b in BOOKS:
            if b.get("audio"):
                items.append({"type": "audio", "title": b.get("title"), "subtitle": f"{b.get('author')} · Audiobook",
                              "image": None, "url": f"/library/{b.get('slug')}",
                              "date": "", "tag": "Audiobook",
                              "theme": classify(f"{b.get('theme','')} {b.get('title','')} {b.get('blurb','')}"),
                              "external": False})

    if want in ("all", "blog"):
        await add_blogs()
    if want in ("all", "article"):
        await add_articles()
    if want in ("all", "signal"):
        await add_signals()
    if want in ("all", "video"):
        await add_videos()
    if want in ("all", "audio"):
        add_audio()

    if theme and theme.lower() != "all":
        items = [it for it in items if it.get("theme") == theme]

    items.sort(key=lambda x: (x.get("date") or ""), reverse=True)
    type_counts, theme_counts = {}, {}
    for it in items:
        type_counts[it["type"]] = type_counts.get(it["type"], 0) + 1
        theme_counts[it["theme"]] = theme_counts.get(it["theme"], 0) + 1
    themes = ["Strategy", "M&A", "Capital & Finance", "Markets", "Economy", "Technology", "Energy & Climate", "Leadership"]
    return {"items": items[:limit], "counts": type_counts, "theme_counts": theme_counts,
            "themes": [t for t in themes if theme_counts.get(t)], "total": len(items)}


@api_router.get("/service-insights/{slug}")
async def get_service_insight(slug: str):
    d = await db.service_blogs.find_one({"slug": slug}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Insight not found")
    related = await db.service_blogs.find(
        {"service_slug": d["service_slug"], "slug": {"$ne": slug}}, {"_id": 0}).sort("sort", 1).to_list(3)
    d["related"] = [_blog_card(r) for r in related]
    d["earlier_editions"] = await db.service_blogs_archive.count_documents({"slug": slug})
    # More in the same theme (across services)
    theme = _insight_theme(d.get("service_slug"), d.get("category"))
    pool = await db.service_blogs.find({"slug": {"$ne": slug}}, {"_id": 0}).sort("updated_at", -1).to_list(200)
    same = [r for r in pool if _insight_theme(r.get("service_slug"), r.get("category")) == theme][:4]
    d["theme"] = theme
    d["theme_slug"] = THEME_SLUGS.get(theme, "strategy")
    d["related_by_theme"] = [_blog_card(r) for r in same]
    return d


@api_router.get("/admin/service-insights/status")
async def admin_service_insights_status(admin: dict = Depends(require_admin)):
    from insights_data import TOPIC_PLAN
    total = sum(len(v) for v in TOPIC_PLAN.values())
    have = await db.service_blogs.count_documents({})
    return {"expected": total, "generated": have, "running": _insights_gen_lock.locked()}


@api_router.post("/admin/service-insights/regenerate")
async def admin_service_insights_regenerate(force: bool = False, admin: dict = Depends(require_admin)):
    if _insights_gen_lock.locked():
        return {"success": False, "message": "Generation already running."}

    async def _run():
        async with _insights_gen_lock:
            try:
                await _generate_all_service_insights(force=force)
            except Exception:
                logger.exception("insights batch failed")

    asyncio.create_task(_run())
    return {"success": True, "message": "Insight generation started in the background."}

INSIGHT_THEMES = ["Strategy", "M&A", "Capital & Finance", "Markets", "Economy", "Technology", "Energy & Climate", "Leadership"]
THEME_SLUGS = {
    "Strategy": "strategy", "M&A": "m-and-a", "Capital & Finance": "capital-finance",
    "Markets": "markets", "Economy": "economy", "Technology": "technology",
    "Energy & Climate": "energy-climate", "Leadership": "leadership",
}
_SLUG_TO_THEME = {v: k for k, v in THEME_SLUGS.items()}
_THEME_BLURB = {
    "Strategy": "How great companies choose where to play, what to kill and when to bet — corporate strategy, portfolio and market entry.",
    "M&A": "Dealmaking that creates value and the mergers that destroyed it — diligence, integration and the first 100 days.",
    "Capital & Finance": "Raising capital on the right terms — IPOs, private rounds, debt and the discipline behind fundable stories.",
    "Markets": "Competitive dynamics, sector shifts and the market signals that separate winners from also-rans.",
    "Economy": "Macro, policy and public-asset economics — from monetisation pipelines to infrastructure capital.",
    "Technology": "Where AI and technology actually change the decision — not the hype, the operating reality.",
    "Energy & Climate": "The energy transition and climate capital — renewables, storage, hydrogen and bankable green finance.",
    "Leadership": "Building leaders who scale — the founder-to-CEO transition, culture, succession and executive judgement.",
}
_SERVICE_THEME = {
    "business-strategy": "Strategy", "ma-advisory": "M&A",
    "fund-raising": "Capital & Finance", "premium-consultation": "Leadership",
    "re-storage-hydrogen": "Energy & Climate", "green-climate-financing": "Energy & Climate",
    "asset-monetisation": "Economy", "business-coaching": "Leadership",
}


def _insight_theme(service_slug: str, category: str) -> str:
    if category == "AI & Technology":
        return "Technology"
    return _SERVICE_THEME.get(service_slug, "Strategy")


async def _resolve_featured_slug() -> Optional[str]:
    """Current featured slug: rotates through the queue if set, else the single pin."""
    meta = await db.app_meta.find_one({"_id": "featured_insight"}) or {}
    queue = [s for s in (meta.get("queue") or []) if s]
    if queue:
        idx = int(meta.get("index", 0)) % len(queue)
        return queue[idx]
    return meta.get("slug")


def _iso_week(dt=None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime("%G-W%V")


# ---------------- Featured insight (pinned/rotating on hub + homepage) ----------------
@api_router.get("/service-insights-featured")
async def get_featured_insight():
    slug = await _resolve_featured_slug()
    d = None
    if slug:
        d = await db.service_blogs.find_one({"slug": slug}, {"_id": 0})
    if not d:  # fall back to the freshest blog
        d = await db.service_blogs.find_one({}, {"_id": 0}, sort=[("updated_at", -1)])
    if not d:
        return {}
    card = _blog_card(d)
    card["sk_take"] = (d.get("sk_insight") or {}).get("take", "")
    return card


@api_router.post("/admin/service-insights/{slug}/feature")
async def admin_feature_insight(slug: str, admin: dict = Depends(require_admin)):
    """Toggle a slug in the featured rotation queue."""
    d = await db.service_blogs.find_one({"slug": slug}, {"_id": 0, "slug": 1})
    if not d:
        raise HTTPException(status_code=404, detail="Insight not found")
    meta = await db.app_meta.find_one({"_id": "featured_insight"}) or {}
    queue = [s for s in (meta.get("queue") or []) if s]
    current = queue[int(meta.get("index", 0)) % len(queue)] if queue else None
    if slug in queue:
        queue.remove(slug)
        in_queue = False
    else:
        queue.append(slug)
        in_queue = True
    # Preserve the currently-live slug across edits so rotation doesn't jump mid-week.
    new_index = queue.index(current) if (current in queue) else 0
    await db.app_meta.update_one({"_id": "featured_insight"},
                                 {"$set": {"queue": queue, "index": new_index,
                                           "slug": queue[new_index] if queue else None,
                                           "set_at": now_iso()}}, upsert=True)
    return {"success": True, "in_queue": in_queue, "queue": queue}


@api_router.get("/admin/featured-queue")
async def admin_featured_queue(admin: dict = Depends(require_admin)):
    meta = await db.app_meta.find_one({"_id": "featured_insight"}) or {}
    queue = [s for s in (meta.get("queue") or []) if s]
    current = await _resolve_featured_slug()
    titles = {}
    if queue:
        async for b in db.service_blogs.find({"slug": {"$in": queue}}, {"_id": 0, "slug": 1, "title": 1, "service_title": 1}):
            titles[b["slug"]] = b
    return {"queue": [{"slug": s, "title": titles.get(s, {}).get("title", s),
                       "service_title": titles.get(s, {}).get("service_title", ""),
                       "current": s == current} for s in queue],
            "rotated_at": meta.get("rotated_at"), "cadence": "weekly"}


async def _rotate_featured():
    meta = await db.app_meta.find_one({"_id": "featured_insight"}) or {}
    queue = [s for s in (meta.get("queue") or []) if s]
    if len(queue) < 2:
        return
    idx = (int(meta.get("index", 0)) + 1) % len(queue)
    await db.app_meta.update_one({"_id": "featured_insight"},
                                 {"$set": {"index": idx, "slug": queue[idx], "rotated_at": now_iso()}})


# ---------------- Trending (most read this week) ----------------
@api_router.get("/service-insights-trending")
async def trending_insights(limit: int = 6):
    wk = _iso_week()
    stats = await db.insight_stats.find({"week": wk}, {"_id": 0}).sort("reads_week", -1).to_list(50)
    slugs = [s["slug"] for s in stats if int(s.get("reads_week", 0) or 0) > 0][:limit]
    docs = []
    if slugs:
        by_slug = {d["slug"]: d for d in await db.service_blogs.find({"slug": {"$in": slugs}}, {"_id": 0}).to_list(limit)}
        docs = [by_slug[s] for s in slugs if s in by_slug]
    if len(docs) < limit:  # top up with freshest so the strip is never empty
        have = {d["slug"] for d in docs}
        extra = await db.service_blogs.find({"slug": {"$nin": list(have)}}, {"_id": 0}).sort("updated_at", -1).to_list(limit - len(docs))
        docs += extra
    return [_blog_card(d) for d in docs[:limit]]


@api_router.get("/service-insights-trending-slugs")
async def trending_slugs(limit: int = 8, min_reads: int = 2):
    """Slugs genuinely spiking this week (for the flame badge)."""
    wk = _iso_week()
    stats = await db.insight_stats.find({"week": wk}, {"_id": 0, "slug": 1, "reads_week": 1}).sort("reads_week", -1).to_list(50)
    return [s["slug"] for s in stats if int(s.get("reads_week", 0) or 0) >= min_reads][:limit]


@api_router.get("/service-insights-themes")
async def list_insight_themes():
    """All themes with counts + slugs for theme landing pages / navigation."""
    docs = await db.service_blogs.find({}, {"_id": 0, "service_slug": 1, "category": 1}).to_list(300)
    counts = {}
    for d in docs:
        th = _insight_theme(d.get("service_slug"), d.get("category"))
        counts[th] = counts.get(th, 0) + 1
    return [{"theme": t, "slug": THEME_SLUGS[t], "count": counts.get(t, 0), "blurb": _THEME_BLURB.get(t, "")}
            for t in INSIGHT_THEMES if counts.get(t, 0) > 0]


@api_router.get("/service-insights-theme/{theme_slug}")
async def insights_by_theme(theme_slug: str):
    theme = _SLUG_TO_THEME.get(theme_slug)
    if not theme:
        raise HTTPException(status_code=404, detail="Theme not found")
    docs = await db.service_blogs.find({}, {"_id": 0}).sort("updated_at", -1).to_list(300)
    items = [_blog_card(d) for d in docs if _insight_theme(d.get("service_slug"), d.get("category")) == theme]
    return {"theme": theme, "slug": theme_slug, "blurb": _THEME_BLURB.get(theme, ""),
            "count": len(items), "items": items}


def _prev_iso_week() -> str:
    return (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%G-W%V")


async def _weekly_recap_stats(week_key: str) -> dict:
    """Reads/shares/themes for a given ISO week from insight_stats rolling counters."""
    stats = await db.insight_stats.find({}, {"_id": 0}).to_list(500)
    rows = []
    for s in stats:
        rd = int(s.get("reads_week", 0) or 0) if s.get("week") == week_key else 0
        sh = int(s.get("shares_week", 0) or 0) if s.get("share_week") == week_key else 0
        if rd or sh:
            rows.append({"slug": s.get("slug"), "title": s.get("title"),
                         "theme": s.get("theme") or _insight_theme(s.get("service_slug"), s.get("category")),
                         "reads": rd, "shares": sh})
    theme = {}
    for r in rows:
        t = theme.setdefault(r["theme"], {"theme": r["theme"], "reads": 0, "shares": 0})
        t["reads"] += r["reads"]
        t["shares"] += r["shares"]
    return {"week": week_key,
            "total_reads": sum(r["reads"] for r in rows), "total_shares": sum(r["shares"] for r in rows),
            "top_read": sorted([r for r in rows if r["reads"]], key=lambda x: x["reads"], reverse=True)[:5],
            "top_shared": sorted([r for r in rows if r["shares"]], key=lambda x: x["shares"], reverse=True)[:5],
            "by_theme": sorted(theme.values(), key=lambda x: x["reads"], reverse=True)}


async def _auto_feature_winner(week_key: str) -> Optional[str]:
    """Add last week's most-read insight to the featured queue and make it the live pick."""
    recap = await _weekly_recap_stats(week_key)
    top = recap.get("top_read") or []
    if not top:
        await _rotate_featured()  # nothing to crown — just advance the queue
        return None
    winner = top[0]["slug"]
    meta = await db.app_meta.find_one({"_id": "featured_insight"}) or {}
    queue = [s for s in (meta.get("queue") or []) if s]
    if winner not in queue:
        queue.append(winner)
    idx = queue.index(winner)
    await db.app_meta.update_one({"_id": "featured_insight"},
                                 {"$set": {"queue": queue, "index": idx, "slug": winner,
                                           "rotated_at": now_iso(), "auto_winner": winner}}, upsert=True)
    return winner


async def _send_weekly_recap(week_key: Optional[str] = None):
    to = os.environ.get("BOOKING_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
    stats = await _weekly_recap_stats(week_key or _prev_iso_week())
    if not to:
        return {"sent": False, "skipped": "no_admin_email", "stats": stats}
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, lambda: send_insights_recap_email(to, stats, PUBLIC_SITE))
    await db.app_meta.update_one({"_id": "insights_recap"}, {"$set": {"last_run": now_iso()}}, upsert=True)
    return {"sent": True, "to": to, "stats": stats}


@api_router.get("/admin/insights/recap-preview")
async def admin_insights_recap_preview(week: str = "current", admin: dict = Depends(require_admin)):
    wk = _prev_iso_week() if week == "prev" else _iso_week()
    return await _weekly_recap_stats(wk)


@api_router.post("/admin/insights/recap-run")
async def admin_insights_recap_run(week: str = "current", admin: dict = Depends(require_admin)):
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return {"sent": False, "skipped": "email_not_configured"}
    wk = _prev_iso_week() if week == "prev" else _iso_week()

    async def _run():
        try:
            await _send_weekly_recap(wk)
        except Exception:
            logger.exception("weekly recap send failed")

    asyncio.create_task(_run())
    return {"sent": True, "queued": True, "week": wk}


@api_router.post("/admin/insights/auto-feature-run")
async def admin_auto_feature_run(week: str = "current", admin: dict = Depends(require_admin)):
    wk = _prev_iso_week() if week == "prev" else _iso_week()
    winner = await _auto_feature_winner(wk)
    return {"success": True, "winner": winner}


@api_router.get("/admin/insights/recap-settings")
async def admin_recap_settings_get(admin: dict = Depends(require_admin)):
    meta = await db.app_meta.find_one({"_id": "insights_recap"}) or {}
    return {"cadence": meta.get("cadence", "weekly"), "last_run": meta.get("last_run")}


class RecapSettingsIn(BaseModel):
    cadence: str  # weekly | fortnightly | monthly


@api_router.post("/admin/insights/recap-settings")
async def admin_recap_settings_set(body: RecapSettingsIn, admin: dict = Depends(require_admin)):
    if body.cadence not in ("weekly", "fortnightly", "monthly", "off"):
        raise HTTPException(status_code=400, detail="Invalid cadence")
    await db.app_meta.update_one({"_id": "insights_recap"}, {"$set": {"cadence": body.cadence}}, upsert=True)
    return {"success": True, "cadence": body.cadence}


def _recap_due(cadence: str, ist_now) -> bool:
    if cadence == "off":
        return False
    if cadence == "weekly":
        return True
    if cadence == "fortnightly":
        return (ist_now.isocalendar()[1] % 2) == 0
    if cadence == "monthly":
        return ist_now.day <= 7  # first Monday of the month
    return True


# ---------------- Reading & share analytics ----------------
class InsightTrackIn(BaseModel):
    slug: str
    event: str  # "view" | "share"
    platform: Optional[str] = None


SHARE_PLATFORMS = {"linkedin", "twitter", "whatsapp", "email", "quote", "copy", "native"}


@api_router.post("/insights/track")
async def track_insight(body: InsightTrackIn):
    if body.event not in ("view", "share"):
        raise HTTPException(status_code=400, detail="Invalid event")
    blog = await db.service_blogs.find_one({"slug": body.slug}, {"_id": 0, "slug": 1, "title": 1, "service_slug": 1, "category": 1})
    if not blog:
        return {"ok": True}  # ignore unknown slugs silently
    theme = _insight_theme(blog.get("service_slug"), blog.get("category"))
    base = {"title": blog.get("title"), "service_slug": blog.get("service_slug"),
            "category": blog.get("category"), "theme": theme, "updated_at": now_iso()}
    if body.event == "share":
        wk = _iso_week()
        existing = await db.insight_stats.find_one({"slug": body.slug}, {"_id": 0, "share_week": 1, "shares_week": 1})
        shares_week = int((existing or {}).get("shares_week", 0) or 0) + 1 if (existing or {}).get("share_week") == wk else 1
        inc = {"shares": 1}
        if body.platform in SHARE_PLATFORMS:
            inc[f"share_by.{body.platform}"] = 1
        await db.insight_stats.update_one({"slug": body.slug}, {"$inc": inc, "$set": {**base, "share_week": wk, "shares_week": shares_week}}, upsert=True)
        return {"ok": True}
    # view: maintain cumulative reads + a weekly rolling counter
    wk = _iso_week()
    existing = await db.insight_stats.find_one({"slug": body.slug}, {"_id": 0, "week": 1, "reads_week": 1})
    reads_week = int((existing or {}).get("reads_week", 0) or 0) + 1 if (existing or {}).get("week") == wk else 1
    await db.insight_stats.update_one(
        {"slug": body.slug},
        {"$inc": {"reads": 1}, "$set": {**base, "week": wk, "reads_week": reads_week}},
        upsert=True)
    return {"ok": True}


@api_router.get("/admin/insights/analytics")
async def admin_insights_analytics(admin: dict = Depends(require_admin)):
    stats = await db.insight_stats.find({}, {"_id": 0}).to_list(500)
    total_reads = sum(int(s.get("reads", 0) or 0) for s in stats)
    total_shares = sum(int(s.get("shares", 0) or 0) for s in stats)
    top_read = sorted(stats, key=lambda s: s.get("reads", 0) or 0, reverse=True)[:8]
    top_shared = sorted(stats, key=lambda s: s.get("shares", 0) or 0, reverse=True)[:8]
    theme = {}
    for s in stats:
        th = s.get("theme") or _insight_theme(s.get("service_slug"), s.get("category"))
        t = theme.setdefault(th, {"theme": th, "reads": 0, "shares": 0})
        t["reads"] += int(s.get("reads", 0) or 0)
        t["shares"] += int(s.get("shares", 0) or 0)

    def _row(s):
        return {"slug": s.get("slug"), "title": s.get("title"), "reads": int(s.get("reads", 0) or 0),
                "shares": int(s.get("shares", 0) or 0), "share_by": s.get("share_by", {})}
    return {"total_reads": total_reads, "total_shares": total_shares,
            "top_read": [_row(s) for s in top_read if s.get("reads")],
            "top_shared": [_row(s) for s in top_shared if s.get("shares")],
            "by_theme": sorted(theme.values(), key=lambda x: x["reads"], reverse=True)}


# ---------------- Admin insights panel (edit / reorder / refresh / editions) ----------------
@api_router.get("/admin/service-insights")
async def admin_list_service_insights(admin: dict = Depends(require_admin)):
    docs = await db.service_blogs.find({}, {"_id": 0}).sort([("service_slug", 1), ("sort", 1)]).to_list(300)
    meta = await db.app_meta.find_one({"_id": "featured_insight"}) or {}
    queue = set(s for s in (meta.get("queue") or []) if s)
    current = await _resolve_featured_slug()
    stats = {s["slug"]: s for s in await db.insight_stats.find({}, {"_id": 0}).to_list(500)}
    arch = {}
    async for d in db.service_blogs_archive.aggregate([{"$group": {"_id": "$slug", "n": {"$sum": 1}}}]):
        arch[d["_id"]] = d["n"]
    out = []
    for d in docs:
        st = stats.get(d["slug"], {})
        out.append({"slug": d["slug"], "title": d["title"], "service_slug": d["service_slug"],
                    "service_title": d["service_title"], "category": d["category"], "sort": d.get("sort", 0),
                    "hero_image": d.get("hero_image"), "version": d.get("version", 1),
                    "updated_at": d.get("updated_at"), "featured": d["slug"] in queue,
                    "is_current": d["slug"] == current,
                    "reads": int(st.get("reads", 0) or 0), "shares": int(st.get("shares", 0) or 0),
                    "editions": arch.get(d["slug"], 0)})
    return out


class InsightEditIn(BaseModel):
    title: Optional[str] = None
    dek: Optional[str] = None
    category: Optional[str] = None
    sort: Optional[int] = None
    hero_image: Optional[str] = None
    read_time: Optional[str] = None
    sections: Optional[list] = None
    key_takeaways: Optional[list] = None
    sk_insight: Optional[dict] = None


@api_router.patch("/admin/service-insights/{slug}")
async def admin_edit_service_insight(slug: str, body: InsightEditIn, admin: dict = Depends(require_admin)):
    d = await db.service_blogs.find_one({"slug": slug}, {"_id": 0, "slug": 1})
    if not d:
        raise HTTPException(status_code=404, detail="Insight not found")
    upd = {k: v for k, v in body.model_dump(exclude_none=True).items()}
    if upd:
        upd["updated_at"] = now_iso()
        await db.service_blogs.update_one({"slug": slug}, {"$set": upd})
    return {"success": True}


@api_router.post("/admin/service-insights/{slug}/refresh")
async def admin_refresh_one_insight(slug: str, admin: dict = Depends(require_admin)):
    from services_data import SERVICES
    d = await db.service_blogs.find_one({"slug": slug}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Insight not found")
    title_by_slug = {s["slug"]: s["title"] for s in SERVICES}
    try:
        doc = await _build_blog_doc(d["service_slug"], title_by_slug.get(d["service_slug"], d["service_slug"]),
                                    d["title"], d.get("category", ""), d.get("sort", 0))
        await _store_blog(doc, archive_previous=True)
    except Exception:
        logger.exception("single insight refresh failed")
        raise HTTPException(status_code=502, detail="Refresh failed. Please try again.")
    return {"success": True, "message": "Insight refreshed; prior edition archived."}


@api_router.get("/admin/service-insights/{slug}/editions")
async def admin_insight_editions(slug: str, admin: dict = Depends(require_admin)):
    docs = await db.service_blogs_archive.find({"slug": slug}, {"_id": 0}).sort("archived_at", -1).to_list(50)
    return [{"archive_id": d.get("archive_id"), "title": d.get("title"), "version": d.get("version"),
             "archived_at": d.get("archived_at"), "dek": d.get("dek")} for d in docs]


# ---------------- Insights newsletter (weekly, freshest 5) ----------------
async def _collect_fresh_insights(limit: int = 5, pool: int = 30) -> list:
    docs = await db.service_blogs.find({}, {"_id": 0}).sort("updated_at", -1).to_list(pool)
    out = []
    for d in docs:
        out.append({"slug": d.get("slug"), "title": d.get("title"), "dek": d.get("dek"),
                    "category": d.get("category"), "service_title": d.get("service_title"),
                    "service_slug": d.get("service_slug"), "hero_image": d.get("hero_image"),
                    "theme": _insight_theme(d.get("service_slug"), d.get("category"))})
    return out[:limit] if limit and pool <= limit else out


def _pick_for_subscriber(pool: list, themes: list, limit: int = 5) -> list:
    """Freshest N insights, preferring the subscriber's chosen themes."""
    if themes:
        matched = [p for p in pool if p.get("theme") in themes]
        if matched:
            picks = matched[:limit]
            if len(picks) < limit:
                picks += [p for p in pool if p not in picks][:limit - len(picks)]
            return picks
    return pool[:limit]


async def _send_insights_newsletter():
    """Email newsletter subscribers the freshest SK Insights, tailored to their chosen themes."""
    pool = await _collect_fresh_insights(limit=0, pool=30)
    if not pool:
        return {"sent": False, "reason": "no_insights"}
    subs = await db.subscribers.find({}, {"_id": 0, "email": 1, "name": 1, "interests_themes": 1}).to_list(5000)
    loop = asyncio.get_event_loop()
    for c in subs:
        items = _pick_for_subscriber(pool, c.get("interests_themes") or [], 5)
        await loop.run_in_executor(None, lambda cc=c, it=items: send_insights_newsletter_email(
            cc["email"], cc.get("name", "there"), it, PUBLIC_SITE, _unsub_url(cc["email"])))
    await db.app_meta.update_one({"_id": "insights_newsletter"}, {"$set": {"last_run": now_iso()}}, upsert=True)
    return {"sent": True, "subscribers": len(subs), "items": len(pool[:5])}


@api_router.post("/admin/insights-newsletter/run")
async def admin_insights_newsletter_run(admin: dict = Depends(require_admin)):
    if not os.environ.get("GMAIL_APP_PASSWORD"):
        return {"sent": False, "skipped": "email_not_configured"}
    subs = await db.subscribers.count_documents({})
    asyncio.create_task(_send_insights_newsletter())
    return {"sent": True, "queued": True, "subscribers": subs}






# ---------------- Deals ticker (Google News RSS) ----------------
_deals_cache = {"ts": 0, "data": []}
DEALS_QUERY = ('("renewable energy" OR solar OR BESS OR "energy storage" OR "green hydrogen") '
               '(acquisition OR merger OR stake OR "fund raise" OR "raises" OR investment) when:14d')


def _fetch_deals():
    try:
        url = "https://news.google.com/rss/search"
        params = {"q": DEALS_QUERY, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"}
        r = requests.get(url, params=params, headers={"User-Agent": YF_UA}, timeout=8)
        root = ET.fromstring(r.content)
        items = []
        for item in root.iter("item"):
            title = item.findtext("title") or ""
            link = item.findtext("link") or ""
            pub = item.findtext("pubDate") or ""
            source_el = item.find("source")
            source = source_el.text if source_el is not None else ""
            if " - " in title and not source:
                source = title.rsplit(" - ", 1)[-1]
                title = title.rsplit(" - ", 1)[0]
            items.append({"title": title, "link": link, "source": source, "pubDate": pub})
            if len(items) >= 15:
                break
        return items
    except Exception:
        return []


@api_router.get("/deals")
async def deals():
    now = time.time()
    if now - _deals_cache["ts"] < 21600 and _deals_cache["data"]:
        return {"data": _deals_cache["data"], "cached": True}
    loop = asyncio.get_event_loop()
    data = await loop.run_in_executor(None, _fetch_deals)
    if data:
        _deals_cache["ts"] = now
        _deals_cache["data"] = data
    return {"data": data or _deals_cache["data"], "cached": False}


IST_TZ = ZoneInfo("Asia/Kolkata")


async def _send_session_reminders():
    """Email confirmed clients at the configured lead time(s) before their session (INERT until SMTP configured)."""
    meta = await _get_availability_meta()
    leads = sorted({int(h) for h in (meta.get("reminder_leads") or [])}, reverse=True)
    if not leads:
        return
    now = datetime.now(timezone.utc)
    loop = asyncio.get_event_loop()
    cur = db.consultations.find({"status": "confirmed", "slot_date": {"$exists": True}},
                                {"_id": 0, "id": 1, "name": 1, "email": 1, "package": 1,
                                 "slot_date": 1, "slot_time": 1, "meeting_link": 1,
                                 "reminders_sent": 1, "reminder_sent": 1})
    async for b in cur:
        try:
            if not b.get("email"):
                continue
            sent = {int(h) for h in (b.get("reminders_sent") or [])}
            if b.get("reminder_sent") is True:
                sent.add(24)  # migrate legacy flag
            dt = datetime.fromisoformat(f"{b['slot_date']}T{b['slot_time']}:00").replace(tzinfo=IST_TZ)
            delta = (dt.astimezone(timezone.utc) - now).total_seconds()
            fired = False
            for h in leads:
                if h in sent:
                    continue
                if (h - 1) * 3600 <= delta <= (h + 1) * 3600:
                    label = "tomorrow" if h >= 24 else f"in about {h} hour" + ("s" if h != 1 else "")
                    await loop.run_in_executor(None, send_session_reminder_email, b["email"],
                                               b.get("name", "there"), b.get("package", "session"),
                                               b["slot_date"], b["slot_time"], label, b.get("meeting_link", ""))
                    sent.add(h)
                    fired = True
            if fired:
                await db.consultations.update_one({"id": b["id"]},
                                                  {"$set": {"reminders_sent": sorted(sent)},
                                                   "$unset": {"reminder_sent": ""}})
        except Exception:
            logger.exception("reminder failed for %s", b.get("id"))


async def _send_weekly_agenda():
    """Monday-morning email to the advisor with the coming week's confirmed sessions."""
    admin_to = os.environ.get("BOOKING_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL")
    if not admin_to:
        return
    today = datetime.now(IST_TZ).date()
    end = today + timedelta(days=7)
    sessions = await db.consultations.find(
        {"status": "confirmed", "slot_date": {"$gte": today.isoformat(), "$lt": end.isoformat()}},
        {"_id": 0, "name": 1, "package": 1, "slot_date": 1, "slot_time": 1, "meeting_link": 1}).to_list(200)
    sessions.sort(key=lambda s: (s.get("slot_date", ""), s.get("slot_time", "")))
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_weekly_agenda_email, admin_to, sessions)


# ---------------- Google Calendar sync (admin's own calendar) ----------------
GCAL_CLIENT_ID = os.environ.get("GOOGLE_CALENDAR_CLIENT_ID", "")
GCAL_CLIENT_SECRET = os.environ.get("GOOGLE_CALENDAR_CLIENT_SECRET", "")
GCAL_REDIRECT_URI = os.environ.get("GOOGLE_CALENDAR_REDIRECT_URI", "")
GCAL_SCOPES = ["https://www.googleapis.com/auth/calendar"]
GCAL_TZ = "Asia/Kolkata"
GCAL_TOKEN_URI = "https://oauth2.googleapis.com/token"


def _gcal_configured() -> bool:
    return bool(GCAL_CLIENT_ID and GCAL_CLIENT_SECRET and GCAL_REDIRECT_URI)


def _gcal_state_token(email: str) -> str:
    return pyjwt.encode({"purpose": "gcal_oauth", "email": email,
                         "exp": datetime.now(timezone.utc) + timedelta(minutes=10)},
                        get_jwt_secret(), algorithm="HS256")


def _gcal_read_state(token: str) -> Optional[str]:
    try:
        d = pyjwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        return d.get("email") if d.get("purpose") == "gcal_oauth" else None
    except Exception:
        return None


async def _gcal_get_conn():
    return await db.app_meta.find_one({"_id": "google_calendar"})


def _slot_end_hhmm(time_hhmm: str, minutes: int) -> str:
    total = int(time_hhmm[:2]) * 60 + int(time_hhmm[3:]) + minutes
    return f"{total // 60:02d}:{total % 60:02d}"


def _gcal_build_service_sync(conn: dict):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GRequest
    from googleapiclient.discovery import build
    creds = Credentials(
        token=_dec(conn["token_enc"]),
        refresh_token=_dec(conn["refresh_token_enc"]) if conn.get("refresh_token_enc") else None,
        token_uri=GCAL_TOKEN_URI, client_id=GCAL_CLIENT_ID, client_secret=GCAL_CLIENT_SECRET,
        scopes=GCAL_SCOPES)
    refreshed = None
    if creds.refresh_token and (creds.expired or not creds.expiry):
        creds.refresh(GRequest())
        refreshed = creds.token
    return build("calendar", "v3", credentials=creds, cache_discovery=False), refreshed


async def _gcal_service():
    conn = await _gcal_get_conn()
    if not conn or not _gcal_configured():
        return None
    loop = asyncio.get_event_loop()
    service, refreshed = await loop.run_in_executor(None, _gcal_build_service_sync, conn)
    if refreshed:
        await db.app_meta.update_one({"_id": "google_calendar"}, {"$set": {"token_enc": _enc(refreshed)}})
    return service


async def _gcal_mark_healthy():
    await db.app_meta.update_one({"_id": "google_calendar"},
                                 {"$unset": {"needs_reconnect": "", "last_error": ""}})


async def _gcal_mark_unhealthy(err: str):
    await db.app_meta.update_one({"_id": "google_calendar"},
                                 {"$set": {"needs_reconnect": True, "last_error": (err or "")[:300]}})


def _event_body(booking: dict, want_meet: bool = False):
    start = f"{booking['slot_date']}T{booking['slot_time']}:00"
    end = f"{booking['slot_date']}T{_slot_end_hhmm(booking['slot_time'], booking.get('minutes', 60))}:00"
    link = (booking.get("meeting_link") or "").strip()
    desc = (f"Client: {booking.get('name','')}\nEmail: {booking.get('email','')}\n"
            f"Phone: {booking.get('phone','')}\nFocus: {booking.get('area','')}\n\n{booking.get('message','')}")
    if link:
        desc += f"\n\nJoin: {link}"
    body = {
        "summary": f"{booking.get('package','Consultation')} — {booking.get('name','')}",
        "description": desc,
        "start": {"dateTime": start, "timeZone": GCAL_TZ},
        "end": {"dateTime": end, "timeZone": GCAL_TZ},
    }
    if link:
        body["location"] = link
    elif want_meet:
        body["conferenceData"] = {"createRequest": {
            "requestId": f"{booking['id']}-{booking.get('slot_time','')}",
            "conferenceSolutionKey": {"type": "hangoutsMeet"}}}
    if booking.get("email"):
        body["attendees"] = [{"email": booking["email"]}]
    return body


def _extract_meet_link(ev: dict) -> str:
    if ev.get("hangoutLink"):
        return ev["hangoutLink"]
    for ep in (ev.get("conferenceData", {}) or {}).get("entryPoints", []):
        if ep.get("entryPointType") == "video" and ep.get("uri"):
            return ep["uri"]
    return ""


async def sync_booking_to_calendar(booking: dict, action: str):
    """Create/update/delete the calendar event. Returns {event_id, meet_link} or None. Never raises."""
    try:
        service = await _gcal_service()
        if not service:
            return None
        loop = asyncio.get_event_loop()
        event_id = booking.get("gcal_event_id")
        if action == "delete":
            if event_id:
                await loop.run_in_executor(None, lambda: service.events().delete(
                    calendarId="primary", eventId=event_id).execute())
            return None
        want_meet = not (booking.get("meeting_link") or "").strip()
        body = _event_body(booking, want_meet)
        if event_id:
            ev = await loop.run_in_executor(None, lambda: service.events().update(
                calendarId="primary", eventId=event_id, body=body, conferenceDataVersion=1).execute())
        else:
            ev = await loop.run_in_executor(None, lambda: service.events().insert(
                calendarId="primary", body=body, conferenceDataVersion=1).execute())
        await _gcal_mark_healthy()
        return {"event_id": ev.get("id", event_id), "meet_link": _extract_meet_link(ev)}
    except Exception as e:
        from google.auth.exceptions import RefreshError
        if isinstance(e, RefreshError):
            await _gcal_mark_unhealthy(str(e))
        logger.exception("Google Calendar sync failed (%s)", action)
        return None


async def _apply_calendar_sync(bid: str, booking: dict, action: str):
    """Sync to calendar, persist event id + any auto Meet link onto the booking dict + DB."""
    res = await sync_booking_to_calendar(booking, action)
    if not res:
        return
    set_fields = {}
    if res.get("event_id") and not booking.get("gcal_event_id"):
        set_fields["gcal_event_id"] = res["event_id"]
        booking["gcal_event_id"] = res["event_id"]
    if res.get("meet_link") and not (booking.get("meeting_link") or "").strip():
        set_fields["meeting_link"] = res["meet_link"]
        booking["meeting_link"] = res["meet_link"]
    if set_fields:
        await db.consultations.update_one({"id": bid}, {"$set": set_fields})


@api_router.get("/admin/calendar/status")
async def calendar_status(admin: dict = Depends(require_admin)):
    conn = await _gcal_get_conn()
    healthy = True
    if conn:
        healthy = not conn.get("needs_reconnect")
        try:
            svc = await _gcal_service()
            if svc:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: svc.calendars().get(calendarId="primary").execute())
                await _gcal_mark_healthy()
                healthy = True
        except Exception as e:
            from google.auth.exceptions import RefreshError
            if isinstance(e, RefreshError):
                await _gcal_mark_unhealthy(str(e))
                healthy = False
    return {"configured": _gcal_configured(),
            "connected": bool(conn),
            "healthy": healthy,
            "email": (conn or {}).get("email"),
            "connected_at": (conn or {}).get("connected_at")}


@api_router.get("/admin/calendar/oauth/start")
async def calendar_oauth_start(admin: dict = Depends(require_admin)):
    if not _gcal_configured():
        raise HTTPException(status_code=400, detail="Google Calendar not configured")
    from urllib.parse import urlencode
    params = {
        "client_id": GCAL_CLIENT_ID, "redirect_uri": GCAL_REDIRECT_URI,
        "response_type": "code", "scope": " ".join(GCAL_SCOPES),
        "access_type": "offline", "prompt": "consent",
        "include_granted_scopes": "true", "state": _gcal_state_token(admin.get("email")),
    }
    return {"authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)}


@api_router.get("/admin/calendar/oauth/callback")
async def calendar_oauth_callback(request: Request, code: str = "", state: str = "", error: str = ""):
    front = os.environ.get("WEBAUTHN_ORIGIN", "")
    if error or not code:
        return RedirectResponse(f"{front}/admin?calendar=error")
    email = _gcal_read_state(state)
    if not email or email.lower() not in ADMIN_ALLOWLIST:
        return RedirectResponse(f"{front}/admin?calendar=error")
    try:
        loop = asyncio.get_event_loop()
        resp = await loop.run_in_executor(None, lambda: requests.post(GCAL_TOKEN_URI, data={
            "code": code, "client_id": GCAL_CLIENT_ID, "client_secret": GCAL_CLIENT_SECRET,
            "redirect_uri": GCAL_REDIRECT_URI, "grant_type": "authorization_code"}, timeout=20))
        tok = resp.json()
        if not tok.get("access_token"):
            return RedirectResponse(f"{front}/admin?calendar=error")
        update = {"_id": "google_calendar", "email": email,
                  "token_enc": _enc(tok["access_token"]), "connected_at": now_iso()}
        if tok.get("refresh_token"):
            update["refresh_token_enc"] = _enc(tok["refresh_token"])
        await db.app_meta.update_one({"_id": "google_calendar"}, {"$set": update}, upsert=True)
        await audit(request, email, "calendar_connected")
    except Exception:
        logger.exception("Calendar OAuth callback failed")
        return RedirectResponse(f"{front}/admin?calendar=error")
    return RedirectResponse(f"{front}/admin?calendar=connected")


@api_router.post("/admin/calendar/disconnect")
async def calendar_disconnect(request: Request, admin: dict = Depends(require_admin)):
    await db.app_meta.delete_one({"_id": "google_calendar"})
    await audit(request, admin.get("email"), "calendar_disconnected")
    return {"success": True}


# ---------------- Booking scheduling + email ----------------
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


@app.middleware("http")
async def security_guard(request: Request, call_next):
    """Site-wide attack detection & automatic blocking for all /api traffic."""
    path = request.url.path
    _current_host.set((request.headers.get("x-forwarded-host") or request.headers.get("origin") or request.headers.get("host") or "").lower())
    if request.method == "OPTIONS" or not path.startswith("/api"):
        return await call_next(request)
    ip = _client_ip(request)

    def _blocked(status, detail):
        headers = {}
        origin = request.headers.get("origin")
        if origin:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
        return JSONResponse(status_code=status, content={"detail": detail}, headers=headers)

    # 1) Already banned → stop immediately.
    if await is_ip_banned(ip):
        return _blocked(403, "Access blocked due to suspicious activity. Contact support if this is a mistake.")

    # 1b) Oversized request body → reject (basic DoS / abuse guard).
    try:
        clen = int(request.headers.get("content-length") or 0)
        if clen > 2_000_000:
            return _blocked(413, "Request too large.")
    except Exception:
        pass

    # 2) Malicious signature in path/query → ban + stop.
    from urllib.parse import unquote
    raw = (path + "?" + (request.url.query or "")).lower()
    probe = unquote(raw)
    if any(p in probe or p in raw for p in MALICIOUS_PATTERNS):
        await ban_ip(ip, "Malicious request pattern", probe[:180])
        return _blocked(403, "Request blocked.")

    # 3) Request flood (sliding window) → ban + stop.
    now = _time.time()
    dq = _req_log[ip]
    dq.append(now)
    while dq and dq[0] < now - RATE_WINDOW_SEC:
        dq.popleft()
    if len(dq) > RATE_MAX_REQUESTS:
        await ban_ip(ip, "Request flood", f"{len(dq)} requests in {RATE_WINDOW_SEC}s")
        return _blocked(429, "Too many requests — temporarily blocked.")

    # 4) VPN / proxy guard — block browsing & login unless allowlisted or TOTP-verified.
    if not path.startswith("/api/vpn/"):
        def _cors_json(status, content):
            headers = {}
            origin = request.headers.get("origin")
            if origin:
                headers["Access-Control-Allow-Origin"] = origin
                headers["Access-Control-Allow-Credentials"] = "true"
            return JSONResponse(status_code=status, headers=headers, content=content)
        try:
            cblk, country, _cc = await country_should_block(request)
            if cblk:
                return _cors_json(403, {
                    "detail": f"Access from {country} is not available.",
                    "country_block": True, "country": country})
            if await vpn_should_block(request):
                return _cors_json(403, {
                    "detail": "Your connection was flagged as a security threat (Tor / known-abusive network) and blocked. If you're a trusted user, verify with your access code to continue.",
                    "vpn_block": True, "threat_block": True})
        except Exception:
            pass

    return await call_next(request)


async def _ensure_index(coll, keys, **opts):
    """Create an index idempotently. If an index with the same key already exists
    with different options (e.g. a non-unique 'email_1' in the production DB), drop
    and recreate it. Never let index reconciliation crash startup."""
    from pymongo.errors import OperationFailure
    want = [(keys, 1)] if isinstance(keys, str) else list(keys)
    try:
        await coll.create_index(keys, **opts)
    except OperationFailure as e:
        if e.code in (85, 86):  # IndexOptionsConflict / IndexKeySpecsConflict
            try:
                info = await coll.index_information()
                for name, meta in info.items():
                    if name == "_id_":
                        continue
                    if [(k, v) for k, v in meta.get("key", [])] == want:
                        await coll.drop_index(name)
                        break
                await coll.create_index(keys, **opts)
                logger.warning("Reconciled index on %s.%s %s", db.name, coll.name, keys)
            except Exception as e2:
                logger.warning("Could not reconcile index on %s.%s %s: %s (continuing)", db.name, coll.name, keys, e2)
        else:
            logger.warning("Index create failed on %s.%s %s: %s (continuing)", db.name, coll.name, keys, e)
    except Exception as e:
        logger.warning("Index create error on %s.%s %s: %s (continuing)", db.name, coll.name, keys, e)


# ==================== Revenue & Credibility: Products · Cohorts · Corporate · Case Studies · Testimonials ====================
CATALOG_ACCENTS = ["from-[#1f1a2e] to-[#0b0a18]", "from-[#12222b] to-[#08131a]", "from-[#2a1810] to-[#0f0a06]",
                   "from-[#102a1f] to-[#08170f]", "from-[#1a1327] to-[#0a0814]", "from-[#101f2b] to-[#080f18]"]


NOTIFY_EMAIL = os.environ.get("BOOKING_ADMIN_EMAIL") or os.environ.get("ADMIN_EMAIL", "")


def _smtp_notify(subject: str, body_txt: str):
    """Fire an internal alert email to the advisor/team (best-effort)."""
    if not NOTIFY_EMAIL:
        return
    send_admin_notify(NOTIFY_EMAIL, subject, body_txt)


def _pub(d: dict) -> dict:
    d.pop("_id", None)
    return d


async def _resolve_promo(code, kind, price):
    """Validate a promo code against an item price. Returns (promo_doc|None, discount, final_price, message)."""
    code = (code or "").strip().upper()
    price = float(price)
    if not code:
        return None, 0.0, price, ""
    p = await db.promo_codes.find_one({"code": code, "active": True})
    if not p:
        return None, 0.0, price, "That code isn't valid."
    exp = p.get("expires_at")
    if exp and str(exp) < now_iso():
        return None, 0.0, price, "That code has expired."
    if int(p.get("max_uses", 0) or 0) > 0 and int(p.get("used_count", 0) or 0) >= int(p["max_uses"]):
        return None, 0.0, price, "That code has reached its usage limit."
    applies = p.get("applies_to", "all") or "all"
    if applies not in ("all", kind):
        return None, 0.0, price, "That code isn't valid for this item."
    min_amt = float(p.get("min_amount", 0) or 0)
    if price < min_amt:
        return None, 0.0, price, f"This code needs a minimum order of \u20b9{int(min_amt)}."
    if (p.get("type") or "percent") == "flat":
        disc = min(float(p.get("value", 0) or 0), price)
    else:
        disc = round(price * float(p.get("value", 0) or 0) / 100.0)
    disc = max(0.0, min(disc, price - 1))  # always leave at least ₹1 to charge
    return p, disc, price - disc, "Code applied!"


async def _seed_commerce():
    if await db.products.count_documents({}) == 0:
        await db.products.insert_many([
            {"id": str(uuid.uuid4()), "slug": "leadership-blueprint-pro", "title": "SK Leadership Blueprint (Pro)",
             "subtitle": "Your Big-Five profile, turned into a 20-page executive playbook",
             "description": "A premium, personalised deep-dive built on your free assessment — strengths, blind spots, a 90-day operating plan and the rituals to run your leadership like a system.",
             "price": 1499, "type": "blueprint", "download_url": "", "active": True, "sort": 1, "created_at": now_iso()},
            {"id": str(uuid.uuid4()), "slug": "cxo-strategy-playbook", "title": "The CXO Strategy Playbook",
             "subtitle": "The frameworks SK uses in every war-room", "description": "A practical playbook of strategy, capital and scaling frameworks with worked examples and one-page templates you can use on Monday.",
             "price": 999, "type": "playbook", "download_url": "", "active": True, "sort": 2, "created_at": now_iso()},
            {"id": str(uuid.uuid4()), "slug": "fundraising-toolkit", "title": "Fundraising & Bankability Toolkit",
             "subtitle": "Model, de-risk, and court capital", "description": "Templates and checklists to make your business bankable before you approach investors — financial model skeleton, data-room checklist and an investor-narrative canvas.",
             "price": 1299, "type": "template", "download_url": "", "active": True, "sort": 3, "created_at": now_iso()},
        ])
    if await db.cohorts.count_documents({}) == 0:
        await db.cohorts.insert_one({
            "id": str(uuid.uuid4()), "slug": "cxo-leadership-cohort", "title": "CXO Leadership Cohort",
            "subtitle": "A 6-week live intensive for founders & senior leaders",
            "description": "Six live war-room sessions with Sudarshan — strategy, capital, scaling and leadership — with peer accountability and a personal 90-day plan. Seats are deliberately limited.",
            "price": 24999, "seats_total": 20, "seats_taken": 0, "start_date": "", "end_date": "",
            "schedule": "Live · 6 weekly sessions · 90 mins each", "waitlist": [], "active": True, "sort": 1, "created_at": now_iso()})
    if await db.case_studies.count_documents({}) == 0:
        await db.case_studies.insert_many([
            {"id": str(uuid.uuid4()), "slug": "renewable-scaleup", "client": "Confidential · Renewables IPP", "sector": "Renewable Energy",
             "headline": "From stalled pipeline to a bankable 500 MW roadmap", "challenge": "A fast-growing IPP had ambition but an un-fundable model and a scattered project pipeline.",
             "approach": "Rebuilt the strategy around a focused, de-risked portfolio and a bankable financial model with clear offtake and capital structure.",
             "result": "Secured growth capital and a clear 3-year roadmap.", "metrics": [{"label": "Pipeline made bankable", "value": "500 MW"}, {"label": "Capital unlocked", "value": "₹1,200 Cr"}],
             "quote": "He turned our ambition into something investors could actually back.", "active": True, "sort": 1, "created_at": now_iso()},
            {"id": str(uuid.uuid4()), "slug": "cost-transformation", "client": "Confidential · Manufacturing CXO", "sector": "Manufacturing",
             "headline": "A cost transformation that protected the growth engine", "challenge": "Margins were eroding and blunt cost-cuts were threatening the very teams driving growth.",
             "approach": "Surgical cost transformation — protecting revenue drivers while removing low-ROI spend and fixing the operating rhythm.",
             "result": "Double-digit margin recovery within two quarters.", "metrics": [{"label": "Cost reduced", "value": "18%"}, {"label": "Margin recovery", "value": "2 quarters"}],
             "quote": "Scalpel, not axe. We came out leaner and stronger.", "active": True, "sort": 2, "created_at": now_iso()},
        ])
    if await db.testimonials.count_documents({}) == 0:
        await db.testimonials.insert_many([
            {"id": str(uuid.uuid4()), "name": "Founder & CEO", "role": "Renewable Energy", "company": "", "quote": "The clearest strategic thinking I've had in the room in years. Practical, and it moved the needle fast.", "featured": True, "sort": 1, "created_at": now_iso()},
            {"id": str(uuid.uuid4()), "name": "Group CFO", "role": "Infrastructure", "company": "", "quote": "He made our business bankable. Investors finally saw what we saw.", "featured": True, "sort": 2, "created_at": now_iso()},
            {"id": str(uuid.uuid4()), "name": "Managing Director", "role": "Manufacturing", "company": "", "quote": "Rare mix of big-picture strategy and hands-on execution. Worth every minute.", "featured": True, "sort": 3, "created_at": now_iso()},
        ])
    if await db.bundles.count_documents({}) == 0:
        await db.bundles.insert_one({
            "id": str(uuid.uuid4()), "slug": "leadership-accelerator", "title": "Leadership Accelerator Bundle",
            "subtitle": "The CXO Playbook + the live Cohort, one price",
            "description": "Get the CXO Strategy Playbook to work through on your own, plus a seat in the live CXO Leadership Cohort — the fastest way to turn frameworks into results. Priced well below buying both separately.",
            "product_slug": "cxo-strategy-playbook", "cohort_slug": "cxo-leadership-cohort",
            "price": 22999, "active": True, "sort": 1, "created_at": now_iso()})


# ---- Public catalogue ----
@api_router.get("/products")
async def list_products():
    return [_pub(d) for d in await db.products.find({"active": True}, {"_id": 0}).sort("sort", 1).to_list(100)]


@api_router.get("/products/{slug}")
async def get_product(slug: str):
    d = await db.products.find_one({"slug": slug, "active": True}, {"_id": 0})
    if not d:
        raise HTTPException(status_code=404, detail="Product not found")
    return d


@api_router.get("/cohorts")
async def list_cohorts():
    out = []
    for c in await db.cohorts.find({"active": True}, {"_id": 0, "waitlist": 0}).sort("sort", 1).to_list(100):
        c["seats_left"] = max(0, int(c.get("seats_total", 0)) - int(c.get("seats_taken", 0)))
        out.append(c)
    return out


@api_router.get("/cohorts/{slug}")
async def get_cohort(slug: str):
    c = await db.cohorts.find_one({"slug": slug, "active": True}, {"_id": 0, "waitlist": 0})
    if not c:
        raise HTTPException(status_code=404, detail="Cohort not found")
    c["seats_left"] = max(0, int(c.get("seats_total", 0)) - int(c.get("seats_taken", 0)))
    return c


@api_router.get("/case-studies")
async def list_case_studies():
    return [_pub(d) for d in await db.case_studies.find({"active": True}, {"_id": 0}).sort("sort", 1).to_list(100)]


@api_router.get("/testimonials")
async def list_testimonials():
    return [_pub(d) for d in await db.testimonials.find({}, {"_id": 0}).sort("sort", 1).to_list(100)]


@api_router.get("/bundles")
async def list_bundles():
    out = []
    for b in await db.bundles.find({"active": True}, {"_id": 0}).sort("sort", 1).to_list(100):
        prod = await db.products.find_one({"slug": b.get("product_slug")}, {"_id": 0, "title": 1, "price": 1})
        coh = await db.cohorts.find_one({"slug": b.get("cohort_slug")}, {"_id": 0, "title": 1, "price": 1, "seats_taken": 1, "seats_total": 1})
        sep = float((prod or {}).get("price", 0) or 0) + float((coh or {}).get("price", 0) or 0)
        b["product_title"] = (prod or {}).get("title")
        b["cohort_title"] = (coh or {}).get("title")
        b["separate_price"] = sep
        b["savings"] = max(0.0, round(sep - float(b.get("price", 0) or 0), 2))
        b["cohort_seats_left"] = max(0, int((coh or {}).get("seats_total", 0)) - int((coh or {}).get("seats_taken", 0))) if coh else 0
        out.append(b)
    return out


# ---- Corporate / enterprise inquiry ----
class CorporateIn(BaseModel):
    name: str
    email: str
    company: str
    phone: Optional[str] = ""
    budget: Optional[str] = ""
    engagement: Optional[str] = ""
    message: Optional[str] = ""
    captcha_token: Optional[str] = None


@api_router.post("/corporate/inquiry")
async def corporate_inquiry(body: CorporateIn, request: Request):
    verify_captcha(body.captcha_token, _client_ip(request), request)
    doc = {"id": str(uuid.uuid4()), "name": body.name, "email": body.email.lower(), "company": body.company,
           "phone": body.phone or "", "area": "Corporate / Enterprise", "package": "Corporate Inquiry",
           "budget": body.budget or "", "engagement": body.engagement or "",
           "message": body.message or "", "status": "new", "source": "corporate-inquiry", "created_at": now_iso()}
    await db.consultations.insert_one(doc)
    try:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, lambda: send_test_email and None)  # noop guard
        if os.environ.get("GMAIL_APP_PASSWORD") and NOTIFY_EMAIL:
            body_txt = (f"New corporate inquiry\n\n{body.name} · {body.company}\n{body.email} · {body.phone}\n"
                        f"Budget: {body.budget}\nEngagement: {body.engagement}\n\n{body.message}")
            loop.run_in_executor(None, lambda: _smtp_notify("New corporate / enterprise inquiry", body_txt))
    except Exception:
        logger.warning("corporate inquiry notify failed", exc_info=True)
    return {"success": True, "message": "Thank you — your enquiry is with Sudarshan's team. We'll be in touch shortly."}


# ---- Lead magnet capture (nurture funnel entry) ----
class LeadMagnetIn(BaseModel):
    email: str
    name: Optional[str] = ""
    source: Optional[str] = "lead-magnet"
    captcha_token: Optional[str] = None


@api_router.post("/nurture/subscribe")
async def nurture_subscribe(body: LeadMagnetIn, request: Request):
    verify_captcha(body.captcha_token, _client_ip(request), request)
    email = body.email.lower().strip()
    await db.subscribers.update_one({"email": email}, {"$setOnInsert": {
        "email": email, "name": body.name or "there", "source": body.source or "lead-magnet",
        "created_at": now_iso()}}, upsert=True)
    if os.environ.get("GMAIL_APP_PASSWORD"):
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, lambda: send_nurture_welcome_email(email, body.name or "there", PUBLIC_SITE, _unsub_url(email)))
    return {"success": True, "message": "You're in. Check your inbox — your first insight from Sudarshan is on its way."}


# ---- Commerce: paid products & cohort seats (Razorpay) ----
class CommerceOrderIn(BaseModel):
    kind: str  # "product" | "cohort"
    ref_id: str
    name: str
    email: str
    phone: Optional[str] = ""
    promo_code: Optional[str] = None
    gift: Optional[dict] = None  # {recipient_name, recipient_email, message}
    meta: Optional[dict] = None  # e.g. assessment result for a personalised Blueprint
    captcha_token: Optional[str] = None


@api_router.post("/commerce/order")
async def commerce_order(body: CommerceOrderIn, request: Request):
    verify_captcha(body.captcha_token, _client_ip(request), request)
    client = _razorpay_client()
    if not client:
        raise HTTPException(status_code=503, detail="Payments are not configured yet. Please try again shortly.")
    if body.kind == "product":
        item = await db.products.find_one({"slug": body.ref_id, "active": True}, {"_id": 0})
        title = item and item["title"]
    elif body.kind == "cohort":
        item = await db.cohorts.find_one({"slug": body.ref_id, "active": True}, {"_id": 0})
        title = item and item["title"]
        if item and int(item.get("seats_taken", 0)) >= int(item.get("seats_total", 0)):
            return {"success": False, "waitlist": True, "message": "This cohort is full. Join the waitlist and we'll offer you the next seat."}
    elif body.kind == "bundle":
        item = await db.bundles.find_one({"slug": body.ref_id, "active": True}, {"_id": 0})
        title = item and item["title"]
        if item:
            coh = await db.cohorts.find_one({"slug": item.get("cohort_slug"), "active": True}, {"_id": 0})
            if coh and int(coh.get("seats_taken", 0)) >= int(coh.get("seats_total", 0)):
                return {"success": False, "waitlist": True, "message": "This bundle's cohort is full right now — join the cohort waitlist and we'll be in touch."}
    else:
        raise HTTPException(status_code=400, detail="Invalid kind")
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    list_price = float(item["price"])
    promo, discount, final_price, _ = await _resolve_promo(body.promo_code, body.kind, list_price)
    if body.promo_code and not promo:
        raise HTTPException(status_code=400, detail="That promo code isn't valid for this item.")
    amount_paise = int(round(final_price * 100))
    oid = str(uuid.uuid4())
    try:
        order = await asyncio.to_thread(client.order.create, {
            "amount": amount_paise, "currency": "INR", "payment_capture": 1, "receipt": oid[:40],
            "notes": {"kind": body.kind, "item": title, "email": body.email.lower(),
                      "promo": (promo or {}).get("code", "")}})
    except Exception:
        logger.exception("razorpay commerce order failed")
        raise HTTPException(status_code=502, detail="Could not start the payment. Please try again.")
    await db.orders.insert_one({
        "id": oid, "kind": body.kind, "ref_id": body.ref_id, "ref_title": title,
        "name": body.name, "email": body.email.lower(), "phone": body.phone or "",
        "amount": final_price, "list_price": list_price, "discount": discount,
        "promo_code": (promo or {}).get("code") or None,
        "currency": "INR", "amount_paise": amount_paise,
        "meta": body.meta or {},
        "gift": body.gift or None,
        "status": "pending_payment", "paid": False, "delivered": False,
        "razorpay_order_id": order["id"], "source": f"{body.kind}-checkout", "created_at": now_iso()})
    return {"success": True, "our_order_id": oid, "order_id": order["id"], "amount": amount_paise,
            "currency": "INR", "key_id": os.environ.get("RAZORPAY_KEY_ID", ""), "item": title,
            "prefill": {"name": body.name, "email": body.email.lower(), "contact": body.phone or ""}}


class CommerceVerifyIn(BaseModel):
    our_order_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@api_router.post("/commerce/verify")
async def commerce_verify(body: CommerceVerifyIn):
    client = _razorpay_client()
    if not client:
        raise HTTPException(status_code=503, detail="Payments are not configured.")
    o = await db.orders.find_one({"id": body.our_order_id})
    if not o or o.get("razorpay_order_id") != body.razorpay_order_id:
        raise HTTPException(status_code=404, detail="Order not found for this payment.")
    if o.get("paid"):
        return {"success": True, "kind": o["kind"], "download_url": o.get("download_url", ""), "message": "Already confirmed."}
    try:
        client.utility.verify_payment_signature({
            "razorpay_order_id": body.razorpay_order_id, "razorpay_payment_id": body.razorpay_payment_id,
            "razorpay_signature": body.razorpay_signature})
    except Exception:
        raise HTTPException(status_code=400, detail="Payment could not be verified.")
    download_url = ""
    if o["kind"] == "product":
        prod = await db.products.find_one({"slug": o["ref_id"]}, {"_id": 0})
        if (prod or {}).get("type") == "blueprint" and (o.get("meta") or {}).get("scores"):
            download_url = f"/api/blueprint/download/{o['id']}"
        elif (prod or {}).get("download_url"):
            download_url = prod["download_url"]
        else:
            download_url = "/api/blueprint/starter.pdf"
    elif o["kind"] == "cohort":
        res = await db.cohorts.update_one(
            {"slug": o["ref_id"], "$expr": {"$lt": ["$seats_taken", "$seats_total"]}},
            {"$inc": {"seats_taken": 1}})
        if res.modified_count == 0:
            await db.cohorts.update_one({"slug": o["ref_id"], "waitlist": {"$ne": o["email"]}},
                                        {"$push": {"waitlist": o["email"]}})
    elif o["kind"] == "bundle":
        b = await db.bundles.find_one({"slug": o["ref_id"]}, {"_id": 0})
        prod = await db.products.find_one({"slug": (b or {}).get("product_slug")}, {"_id": 0})
        download_url = (prod or {}).get("download_url") or "/api/blueprint/starter.pdf"
        if b and b.get("cohort_slug"):
            res = await db.cohorts.update_one(
                {"slug": b["cohort_slug"], "$expr": {"$lt": ["$seats_taken", "$seats_total"]}},
                {"$inc": {"seats_taken": 1}})
            if res.modified_count == 0:
                await db.cohorts.update_one({"slug": b["cohort_slug"], "waitlist": {"$ne": o["email"]}},
                                            {"$push": {"waitlist": o["email"]}})
    await db.orders.update_one({"id": o["id"]}, {"$set": {
        "paid": True, "status": "paid", "delivered": True, "download_url": download_url,
        "razorpay_payment_id": body.razorpay_payment_id, "paid_at": now_iso()}})
    if o.get("promo_code"):
        await db.promo_codes.update_one({"code": o["promo_code"]}, {"$inc": {"used_count": 1}})
    gift = o.get("gift") or {}
    recipient = (gift.get("recipient_email") or "").strip().lower()
    deliver_at = (gift.get("deliver_at") or "").strip()
    scheduled = bool(recipient and deliver_at and deliver_at > now_iso())
    if recipient:
        await db.orders.update_one({"id": o["id"]}, {"$set": {
            "gift_deliver_at": deliver_at or None, "gift_delivered": not scheduled}})
    if os.environ.get("GMAIL_APP_PASSWORD"):
        loop = asyncio.get_event_loop()
        if recipient:
            # Buyer gets a forwardable gift receipt; recipient gets access now or on the scheduled date.
            loop.run_in_executor(None, lambda: send_gift_receipt_email(
                o["email"], o["name"], o["ref_title"], gift.get("recipient_name", ""),
                recipient, o.get("amount", 0), gift.get("message", ""), PUBLIC_SITE,
                deliver_at if scheduled else ""))
            if not scheduled:
                loop.run_in_executor(None, lambda: send_gift_email(
                    recipient, gift.get("recipient_name", ""), o["name"], o["ref_title"], o["kind"],
                    download_url, gift.get("message", ""), PUBLIC_SITE))
        else:
            loop.run_in_executor(None, lambda: send_purchase_email(
                o["email"], o["name"], o["kind"], o["ref_title"], download_url, PUBLIC_SITE))
        if NOTIFY_EMAIL:
            loop.run_in_executor(None, lambda: _smtp_notify(
                f"New {o['kind']} purchase: {o['ref_title']}",
                f"{o['name']} ({o['email']}) paid ₹{o['amount']} for {o['ref_title']}."
                + (f" (gift to {recipient}{', scheduled ' + deliver_at if scheduled else ''})" if recipient else "")))
    if recipient:
        msg = (f"Payment received! We'll deliver the gift to {recipient} on {deliver_at[:10]}."
               if scheduled else f"Payment received! We've emailed access to {recipient}.")
        return {"success": True, "kind": o["kind"], "gifted": True, "download_url": "", "message": msg}
    return {"success": True, "kind": o["kind"], "download_url": download_url,
            "message": "Payment received! Check your email for access." if o["kind"] in ("product", "bundle")
            else "Payment received! Your seat is booked — details are on the way to your inbox."}


class PromoValidateIn(BaseModel):
    code: str
    kind: str
    ref_id: str


class GiftPreviewIn(BaseModel):
    recipient_name: Optional[str] = ""
    buyer_name: Optional[str] = ""
    item_title: str
    kind: str = "product"
    message: Optional[str] = ""
    deliver_at: Optional[str] = ""


@api_router.post("/commerce/gift-preview")
async def commerce_gift_preview(body: GiftPreviewIn):
    from emailer import render_gift_email_html
    html = render_gift_email_html(body.recipient_name, body.buyer_name, body.item_title,
                                  body.kind, "#", body.message, PUBLIC_SITE, body.deliver_at)
    return {"html": html}


@api_router.post("/promo/validate")
async def promo_validate(body: PromoValidateIn):
    coll = db.products if body.kind == "product" else db.cohorts if body.kind == "cohort" else db.bundles if body.kind == "bundle" else None
    if coll is None:
        raise HTTPException(status_code=400, detail="Invalid kind")
    item = await coll.find_one({"slug": body.ref_id, "active": True}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    p, disc, final, msg = await _resolve_promo(body.code, body.kind, item["price"])
    if not p:
        return {"valid": False, "message": msg or "That code isn't valid."}
    label = f"{int(p['value'])}% off" if (p.get("type") or "percent") == "percent" else f"\u20b9{int(p['value'])} off"
    return {"valid": True, "message": msg, "code": p["code"], "label": label,
            "discount": disc, "final_price": final, "original_price": item["price"]}


@api_router.post("/cohorts/{slug}/waitlist")
async def cohort_waitlist(slug: str, body: LeadMagnetIn, request: Request):
    verify_captcha(body.captcha_token, _client_ip(request), request)
    email = body.email.lower().strip()
    r = await db.cohorts.update_one({"slug": slug, "waitlist": {"$ne": email}}, {"$push": {"waitlist": email}})
    if r.matched_count == 0:
        raise HTTPException(status_code=404, detail="Cohort not found")
    return {"success": True, "message": "You're on the waitlist — we'll offer you the next available seat."}


# ---- Admin CMS (upsert / delete) ----
_CMS = {"products": db.products, "cohorts": db.cohorts, "case-studies": db.case_studies,
        "testimonials": db.testimonials, "promo-codes": db.promo_codes, "bundles": db.bundles}


@api_router.get("/admin/cms/{collection}")
async def cms_list(collection: str, admin: dict = Depends(require_admin)):
    coll = _CMS.get(collection)
    if coll is None:
        raise HTTPException(status_code=404, detail="Unknown collection")
    return [_pub(d) for d in await coll.find({}, {"_id": 0}).sort("sort", 1).to_list(500)]


async def _validate_cms(collection: str, body: dict):
    """Guardrails so an admin typo can't silently break a live page. Coerces numbers, checks required fields + references."""
    def _num(field, default=None, minimum=None, required=False, integer=False):
        raw = body.get(field, default)
        if raw is None or raw == "":
            if required:
                raise HTTPException(status_code=400, detail=f"'{field}' is required.")
            return
        try:
            val = int(raw) if integer else float(raw)
        except (TypeError, ValueError):
            raise HTTPException(status_code=400, detail=f"'{field}' must be a number.")
        if minimum is not None and val < minimum:
            raise HTTPException(status_code=400, detail=f"'{field}' must be at least {minimum}.")
        body[field] = val

    def _req(field, label=None):
        if not str(body.get(field, "") or "").strip():
            raise HTTPException(status_code=400, detail=f"'{label or field}' is required.")

    if collection == "products":
        _req("title"); _req("slug"); _num("price", minimum=0, required=True); _num("sort")
        if body.get("type") and body["type"] not in ("playbook", "template", "blueprint", "guide"):
            raise HTTPException(status_code=400, detail="Invalid product type.")
    elif collection == "cohorts":
        _req("title"); _req("slug"); _num("price", minimum=0, required=True)
        _num("seats_total", minimum=1, required=True, integer=True); _num("sort")
    elif collection == "case-studies":
        _req("headline"); _req("slug"); _num("sort")
    elif collection == "testimonials":
        _req("quote"); _req("name"); _num("sort")
    elif collection == "promo-codes":
        _req("code"); _num("value", minimum=0, required=True)
        _num("min_amount", minimum=0); _num("max_uses", minimum=0, integer=True); _num("sort")
        if (body.get("type") or "percent") not in ("percent", "flat"):
            raise HTTPException(status_code=400, detail="Discount type must be 'percent' or 'flat'.")
        if (body.get("applies_to") or "all") not in ("all", "product", "cohort"):
            raise HTTPException(status_code=400, detail="'Applies to' must be all, product or cohort.")
    elif collection == "bundles":
        _req("title"); _req("slug"); _num("price", minimum=0, required=True); _num("sort")
        ps = str(body.get("product_slug", "") or "").strip()
        cs = str(body.get("cohort_slug", "") or "").strip()
        if not ps or not await db.products.find_one({"slug": ps}):
            raise HTTPException(status_code=400, detail=f"Bundle product '{ps or '(blank)'}' doesn't match any product. Check the product slug.")
        if not cs or not await db.cohorts.find_one({"slug": cs}):
            raise HTTPException(status_code=400, detail=f"Bundle cohort '{cs or '(blank)'}' doesn't match any cohort. Check the cohort slug.")


@api_router.post("/admin/cms/{collection}")
async def cms_upsert(collection: str, body: dict, admin: dict = Depends(require_admin)):
    coll = _CMS.get(collection)
    if coll is None:
        raise HTTPException(status_code=404, detail="Unknown collection")
    body.pop("_id", None)
    if collection == "promo-codes":
        body["code"] = (body.get("code") or "").strip().upper()
        if not body["code"]:
            raise HTTPException(status_code=400, detail="Promo code is required.")
    await _validate_cms(collection, body)
    if body.get("id"):
        body["updated_at"] = now_iso()
        await coll.update_one({"id": body["id"]}, {"$set": body})
        return {"success": True, "id": body["id"]}
    body["id"] = str(uuid.uuid4())
    body.setdefault("created_at", now_iso())
    body.setdefault("active", True)
    body.setdefault("sort", 99)
    if collection == "cohorts":
        body.setdefault("seats_taken", 0)
        body.setdefault("waitlist", [])
    if collection == "promo-codes":
        body.setdefault("used_count", 0)
        if await coll.find_one({"code": body["code"]}):
            raise HTTPException(status_code=400, detail="A code with that name already exists.")
    await coll.insert_one(body)
    return {"success": True, "id": body["id"]}


@api_router.delete("/admin/cms/{collection}/{item_id}")
async def cms_delete(collection: str, item_id: str, admin: dict = Depends(require_admin)):
    coll = _CMS.get(collection)
    if coll is None:
        raise HTTPException(status_code=404, detail="Unknown collection")
    await coll.delete_one({"id": item_id})
    return {"success": True}


@api_router.get("/admin/commerce/orders")
async def admin_commerce_orders(admin: dict = Depends(require_admin)):
    return [_pub(d) for d in await db.orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)]


@api_router.get("/admin/commerce/orders/export")
async def admin_commerce_orders_export(admin: dict = Depends(require_admin)):
    """Streams all orders as CSV for bookkeeping / GST filing."""
    import csv as _csv

    def _safe(v):
        # Neutralise CSV formula injection (Excel/Sheets) on user-controlled text.
        s = "" if v is None else str(v)
        if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
            return "'" + s
        return s

    orders = await db.orders.find({}, {"_id": 0}).sort("created_at", -1).to_list(5000)
    buf = io.StringIO()
    w = _csv.writer(buf)
    w.writerow(["Date", "Order ID", "Buyer Name", "Buyer Email", "Item", "Kind",
                "List Price (INR)", "Discount (INR)", "Amount Paid (INR)", "Promo Code",
                "Status", "Paid At", "Razorpay Payment ID", "Gift Recipient", "Gift Recipient Email"])
    for o in orders:
        gift = o.get("gift") or {}
        w.writerow([_safe(x) for x in [
            (o.get("created_at") or "")[:19].replace("T", " "),
            o.get("id", ""),
            o.get("name", ""),
            o.get("email", ""),
            o.get("ref_title", ""),
            o.get("kind", ""),
            o.get("list_price", o.get("amount", "")),
            o.get("discount", 0),
            o.get("amount", ""),
            o.get("promo_code") or "",
            "paid" if o.get("paid") else (o.get("status") or ""),
            (o.get("paid_at") or "")[:19].replace("T", " "),
            o.get("razorpay_payment_id", ""),
            gift.get("recipient_name", ""),
            gift.get("recipient_email", ""),
        ]])
    fname = f"sk-orders-{datetime.now(timezone.utc).date().isoformat()}.csv"
    return Response(content=buf.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f"attachment; filename={fname}"})


@api_router.get("/me/orders")
async def my_orders(user: dict = Depends(get_current_user)):
    """The signed-in client's own purchases (matched by email), with download links + gifts sent."""
    email = (user.get("email") or "").strip().lower()
    if not email:
        return {"purchases": [], "gifts_sent": []}
    docs = await db.orders.find({"email": email, "paid": True}, {"_id": 0}).sort("paid_at", -1).to_list(500)
    purchases, gifts_sent = [], []
    for o in docs:
        gift = o.get("gift") or {}
        row = {
            "id": o.get("id"),
            "kind": o.get("kind"),
            "title": o.get("ref_title"),
            "amount": o.get("amount"),
            "promo_code": o.get("promo_code"),
            "discount": o.get("discount", 0),
            "paid_at": o.get("paid_at") or o.get("created_at"),
            "download_url": o.get("download_url") or "",
        }
        if gift.get("recipient_email"):
            gifts_sent.append({**row,
                               "recipient_name": gift.get("recipient_name", ""),
                               "recipient_email": gift.get("recipient_email", ""),
                               "message": gift.get("message", ""),
                               "delivered": o.get("gift_delivered", True),
                               "deliver_at": o.get("gift_deliver_at")})
        else:
            purchases.append(row)
    return {"purchases": purchases, "gifts_sent": gifts_sent}


@api_router.post("/admin/commerce/nudge-abandoned")
async def admin_nudge_abandoned(admin: dict = Depends(require_admin)):
    sent = await _nudge_abandoned_orders()
    return {"success": True, "sent": sent,
            "message": (f"Sent {sent} nudge email(s)." if sent else
                        "No abandoned orders to nudge right now (must be idle 1-24h, unpaid, and email configured).")}


@api_router.get("/admin/commerce/revenue-analytics")
async def admin_revenue_analytics(admin: dict = Depends(require_admin)):
    paid = await db.orders.find({"paid": True},
                                {"_id": 0, "amount": 1, "paid_at": 1, "created_at": 1,
                                 "ref_title": 1, "kind": 1, "ref_id": 1}).to_list(5000)
    from collections import defaultdict, OrderedDict
    today = datetime.now(timezone.utc).date()
    series = OrderedDict(((today - timedelta(days=i)).isoformat(), 0.0) for i in range(29, -1, -1))
    items = defaultdict(lambda: {"units": 0, "revenue": 0.0, "title": "", "kind": ""})
    total = 0.0
    for o in paid:
        amt = float(o.get("amount", 0) or 0)
        total += amt
        ts = (o.get("paid_at") or o.get("created_at") or "")[:10]
        if ts in series:
            series[ts] += amt
        key = (o.get("kind"), o.get("ref_id"))
        it = items[key]
        it["units"] += 1
        it["revenue"] += amt
        it["title"] = o.get("ref_title") or o.get("ref_id")
        it["kind"] = o.get("kind")
    top = sorted(items.values(), key=lambda x: x["revenue"], reverse=True)[:6]
    n = len(paid)
    return {"series": [{"date": k[5:], "revenue": round(v, 2)} for k, v in series.items()],
            "top_items": [{**t, "revenue": round(t["revenue"], 2)} for t in top],
            "total_revenue": round(total, 2), "orders": n,
            "aov": round(total / n, 2) if n else 0}


@api_router.get("/commerce/best-sellers")
async def commerce_best_sellers():
    """Top-converting product + cohort by paid-order count (for 'Most popular' badges)."""
    out = {"product": None, "cohort": None}
    for kind, key in (("product", "product"), ("cohort", "cohort")):
        agg = await db.orders.aggregate([
            {"$match": {"kind": kind, "paid": True}},
            {"$group": {"_id": "$ref_id", "n": {"$sum": 1}}},
            {"$sort": {"n": -1}}, {"$limit": 1},
        ]).to_list(1)
        if agg:
            out[key] = agg[0]["_id"]
    return out


@api_router.get("/admin/promo/analytics")
async def admin_promo_analytics(admin: dict = Depends(require_admin)):
    codes = await db.promo_codes.find({}, {"_id": 0}).sort("sort", 1).to_list(500)
    out = []
    for c in codes:
        started = await db.orders.count_documents({"promo_code": c["code"]})
        paid = await db.orders.find({"promo_code": c["code"], "paid": True},
                                    {"_id": 0, "amount": 1, "discount": 1}).to_list(2000)
        uses = len(paid)
        revenue = round(sum(float(o.get("amount", 0) or 0) for o in paid), 2)
        discount_given = round(sum(float(o.get("discount", 0) or 0) for o in paid), 2)
        conv = round(uses / started * 100) if started else 0
        out.append({**c, "started": started, "uses": uses, "revenue": revenue,
                    "discount_given": discount_given, "conversion_rate": conv})
    return out


@api_router.get("/blueprint/starter.pdf")
async def blueprint_starter():
    from blueprint_pdf import build_starter_pdf
    pdf = await asyncio.to_thread(build_starter_pdf)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="SK-Leadership-Blueprint-Starter.pdf"'})


@api_router.get("/blueprint/download/{order_id}")
async def blueprint_download(order_id: str):
    o = await db.orders.find_one({"id": order_id}, {"_id": 0})
    if not o or not o.get("paid"):
        raise HTTPException(status_code=404, detail="Blueprint not found or payment not confirmed.")
    meta = o.get("meta") or {}
    from blueprint_pdf import build_personalized_pdf, build_starter_pdf
    if meta.get("scores"):
        pdf = await asyncio.to_thread(build_personalized_pdf, o.get("name", ""),
                                      meta.get("scores"), meta.get("quadrant"), meta.get("blueprint") or {})
    else:
        pdf = await asyncio.to_thread(build_starter_pdf)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": 'attachment; filename="SK-Leadership-Blueprint.pdf"'})


app.include_router(api_router)


@app.on_event("startup")
async def startup():
    await _ensure_index(db.users, "email", unique=True)
    await _ensure_index(db.users, "id")
    await _ensure_index(db.user_sessions, "session_token")
    await _ensure_index(db.activity_events, "user_id")
    await _ensure_index(db.support_tickets, "user_id")
    await _ensure_index(db.support_tickets, "status")
    await _ensure_index(db.login_attempts, "identifier", unique=True)
    await _ensure_index(db.login_attempts, "ip")
    await _ensure_index(db.blocked_ips, "ip", unique=True)
    await _ensure_index(db.security_alerts, "created_at")
    await _ensure_index(db.consent_logs, "created_at")
    await _ensure_index(db.consent_logs, "email")
    await _ensure_index(db.signals_archive, "date", unique=True)
    await _ensure_index(db.audit_log, "at")
    await _ensure_index(db.audit_log, "expire_at", expireAfterSeconds=0)
    _meta = await db.app_meta.find_one({"_id": "audit_retention"})
    if _meta and _meta.get("days"):
        global _audit_retention_days
        _audit_retention_days = int(_meta["days"])
    await _ensure_index(db.articles, "slug", unique=True)
    await _ensure_index(db.consultations, "slot_date")
    # Warm the in-memory ban cache with any still-active bans.
    now = datetime.now(timezone.utc)
    async for b in db.blocked_ips.find({}, {"_id": 0, "ip": 1, "banned_until": 1, "scope": 1}):
        try:
            t = datetime.fromisoformat(b.get("banned_until"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            if t > now:
                if b.get("scope") == "cidr":
                    _banned_cidrs[b["ip"]] = t.timestamp()
                else:
                    _banned_ips[b["ip"]] = t.timestamp()
        except Exception:
            continue
    # Seed admin
    admin_email = os.environ["ADMIN_EMAIL"].lower()
    admin_password = os.environ["ADMIN_PASSWORD"]
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": str(uuid.uuid4()), "email": admin_email, "name": "Sudarshan Karweer",
            "password_hash": hash_password(admin_password), "role": "admin", "created_at": now_iso(),
        })
        logger.info("Admin seeded")
    elif not verify_password(admin_password, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_password)}})
    # Enforce admin allowlist strictly: promote allowlisted users, demote everyone else.
    if ADMIN_ALLOWLIST:
        await db.users.update_many(
            {"email": {"$in": list(ADMIN_ALLOWLIST)}}, {"$set": {"role": "admin"}})
        await db.users.update_many(
            {"role": "admin", "email": {"$nin": list(ADMIN_ALLOWLIST)}}, {"$set": {"role": "client"}})
        logger.info("Admin allowlist enforced: %s", ", ".join(sorted(ADMIN_ALLOWLIST)))
    # Backfill unique client codes for any users missing one
    async for u in db.users.find({"client_code": {"$exists": False}}, {"_id": 0, "id": 1}):
        await db.users.update_one({"id": u["id"]}, {"$set": {"client_code": gen_client_code()}})
    # Seed articles
    # Seed / ensure articles (upsert by slug, non-destructive)
    for a in ARTICLES:
        if not await db.articles.find_one({"slug": a["slug"]}):
            d = dict(a)
            d.update({"id": str(uuid.uuid4()), "author": "Sudarshan Karweer", "created_at": now_iso()})
            await db.articles.insert_one(d)
    logger.info("Articles ensured")
    await _seed_commerce()
    # Load any admin-set Terms/Privacy policy version override.
    global CONSENT_POLICY_VERSION
    _pol = await db.app_meta.find_one({"_id": "policy"})
    if _pol and _pol.get("version"):
        CONSENT_POLICY_VERSION = _pol["version"]
    # Backfill today's Signals Archive from the current cached content (if any).
    _hc = await db.app_meta.find_one({"_id": "home_content"})
    if _hc and _hc.get("generated_at"):
        _day = datetime.now(timezone.utc).date().isoformat()
        if not await db.signals_archive.find_one({"date": _day}):
            await db.signals_archive.update_one({"date": _day}, {"$set": {
                "date": _day, "hero_headline": _hc.get("hero_headline", ""),
                "hero_subtext": _hc.get("hero_subtext", ""), "insights": _hc.get("insights", []),
                "feed": _hc.get("feed", []), "generated_at": _hc.get("generated_at")}}, upsert=True)
    asyncio.create_task(_refresh_home_content())  # warm the content cache
    asyncio.create_task(_digest_scheduler())
    asyncio.create_task(_warm_entities())  # warm sector/agency/OEM profiles in background


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
