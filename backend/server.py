from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import asyncio
import logging
import uuid
import time
import requests
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timezone, timedelta

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
import xml.etree.ElementTree as ET
from datetime import datetime as _dt

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionRequest

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


def verify_captcha(token, ip=None):
    if not token:
        raise HTTPException(status_code=400, detail="Captcha verification required")
    # Lenient mode: real site key set but real secret not yet configured.
    # A valid hCaptcha token must still be present (bot must solve the widget).
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


def issue_captcha_gate() -> str:
    payload = {"purpose": "captcha_gate",
               "exp": datetime.now(timezone.utc) + timedelta(seconds=CAPTCHA_GATE_TTL)}
    return pyjwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def verify_captcha_gate(token) -> bool:
    if not token:
        return False
    try:
        data = pyjwt.decode(token, get_jwt_secret(), algorithms=["HS256"])
        return data.get("purpose") == "captcha_gate"
    except Exception:
        return False
    return True

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


class LoginIn(BaseModel):
    email: EmailStr
    password: str
    captcha_token: Optional[str] = None


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
    verify_captcha(body.captcha_token, request.client.host if request.client else None)
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
    """Cached VPN/proxy/Tor detection via vpnapi.io (fail-open on error)."""
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
                        "flagged": hit.get("flagged", False)}
        except Exception:
            pass
    vpn = proxy = tor = False
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
                provider = "ipqualityscore"
        except Exception:
            pass
    flagged = vpn or proxy or tor
    ttl = timedelta(minutes=2) if provider in ("error", "none") else timedelta(hours=24)
    await db.ip_risk_cache.update_one({"_id": ip}, {"$set": {
        "_id": ip, "vpn": vpn, "proxy": proxy, "tor": tor, "provider": provider,
        "flagged": flagged, "expireAt": (now + ttl).isoformat()}}, upsert=True)
    return {"vpn": vpn, "proxy": proxy, "tor": tor, "provider": provider, "flagged": flagged}


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
    if not await vpn_guard_enabled():
        return False
    ip = _client_ip(request)
    if ip in await vpn_allowlist():
        return False
    if _verify_vpn_totp_cookie(request.cookies.get("vpn_totp")):
        return False
    return (await detect_vpn(ip))["flagged"]


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
    verify_captcha(body.captcha_token, request.client.host if request.client else None)
    email = body.email.lower()
    identifier = _login_identifier(request, email)
    await check_login_lockout(identifier)
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        await register_failed_login(identifier, request.client.host if request.client else "unknown", email)
        raise HTTPException(status_code=401, detail="Invalid email or password")
    await clear_login_attempts(identifier)
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


@api_router.post("/auth/captcha-gate")
async def captcha_gate(body: CaptchaGateIn, request: Request, response: Response):
    """Verify a solved hCaptcha, then set a short-lived cookie that gates the Google OAuth redirect."""
    verify_captcha(body.captcha_token, request.client.host if request.client else None)
    response.set_cookie("captcha_gate", issue_captcha_gate(), httponly=True, secure=True,
                        samesite="none", path="/", max_age=CAPTCHA_GATE_TTL)
    return {"ok": True}


@api_router.post("/auth/session")
async def create_session(body: SessionIn, request: Request, response: Response):
    # hCaptcha must have been solved on the login/register page before the Google redirect.
    if not verify_captcha_gate(request.cookies.get("captcha_gate")):
        raise HTTPException(status_code=403, detail="Captcha verification required")
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


@api_router.get("/admin/vault/status")
async def vault_status(request: Request, admin: dict = Depends(require_admin)):
    email = admin.get("email")
    mfa = await db.superadmin_mfa.find_one({"email": email})
    pk = await db.webauthn_credentials.count_documents({"user_id": email})
    return {"totp_enrolled": bool(mfa and mfa.get("totp_enrolled")),
            "passkey_enrolled": pk > 0,
            "unlocked": _read_vault_jwt(request.cookies.get("vault_unlock"), "unlocked") == email,
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
    mfa = await db.superadmin_mfa.find_one({"email": email})
    if not mfa or not mfa.get("totp_enrolled"):
        raise HTTPException(status_code=400, detail="Enroll authenticator first")
    if not pyotp.TOTP(_dec(mfa["totp_secret_enc"])).verify(body.code, valid_window=1):
        await audit(request, email, "vault_totp_fail")
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
        raise HTTPException(status_code=400, detail=f"Passkey authentication failed: {e}")
    await db.webauthn_credentials.update_one({"_id": row["_id"]}, {"$set": {"sign_count": v.new_sign_count}})
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


async def _digest_scheduler():
    while True:
        try:
            await _auto_escalate_tickets()  # hourly SLA escalation pass
            now = datetime.now(timezone.utc)
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
    verify_captcha(body.captcha_token, request.client.host if request.client else None)
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
    "You are 'Karweer AI', the intelligent advisory engine on Sudarshan Karweer's platform. "
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


@api_router.post("/newsletter")
async def subscribe(body: NewsletterIn, request: Request):
    verify_captcha(body.captcha_token, request.client.host if request.client else None)
    email = body.email.lower()
    if await db.subscribers.find_one({"email": email}):
        return {"success": True, "message": "You're already subscribed — thank you!"}
    await db.subscribers.insert_one({"id": str(uuid.uuid4()), "email": email, "created_at": now_iso()})
    return {"success": True, "message": "Subscribed! You'll receive Sudarshan's latest insights."}


@api_router.get("/newsletter")
async def list_subscribers(admin: dict = Depends(require_admin)):
    return await db.subscribers.find({}, {"_id": 0}).sort("created_at", -1).to_list(2000)


# ---------------- Paid Consultation (Stripe) ----------------
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY", "sk_test_emergent")
PACKAGES = {
    "discovery": {"name": "Discovery Call", "amount": 99.0, "duration": "30 minutes",
                  "features": ["Focused problem framing", "Direct next-step guidance", "Ideal first touchpoint"]},
    "strategy": {"name": "1:1 Strategy Session", "amount": 299.0, "duration": "60 minutes",
                 "features": ["Deep strategy & fundraising review", "Actionable roadmap", "Follow-up notes"]},
    "deepdive": {"name": "Deep-Dive Advisory", "amount": 599.0, "duration": "90 minutes",
                 "features": ["Full business / deal deep-dive", "Bankability & scaling plan", "Priority follow-up access"]},
}


class CheckoutIn(BaseModel):
    package_id: str
    origin_url: str
    name: str
    email: EmailStr
    phone: Optional[str] = ""
    area: Optional[str] = ""
    message: Optional[str] = ""
    captcha_token: Optional[str] = None


@api_router.get("/payments/packages")
async def get_packages():
    return [{"id": k, **v} for k, v in PACKAGES.items()]


@api_router.post("/payments/checkout")
async def create_checkout(body: CheckoutIn, request: Request):
    verify_captcha(body.captcha_token, request.client.host if request.client else None)
    pkg = PACKAGES.get(body.package_id)
    if not pkg:
        raise HTTPException(status_code=400, detail="Invalid package")
    webhook_url = f"{str(request.base_url)}api/webhook/stripe"
    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
    success_url = f"{body.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = f"{body.origin_url}/payment/cancel"
    req = CheckoutSessionRequest(
        amount=pkg["amount"], currency="usd", success_url=success_url, cancel_url=cancel_url,
        metadata={"package_id": body.package_id, "name": body.name, "email": body.email,
                  "phone": body.phone or "", "area": body.area or "", "message": body.message or "",
                  "type": "consultation"},
    )
    session = await stripe_checkout.create_checkout_session(req)
    await db.payment_transactions.insert_one({
        "id": str(uuid.uuid4()), "session_id": session.session_id, "package_id": body.package_id,
        "amount": pkg["amount"], "currency": "usd", "status": "initiated", "payment_status": "pending",
        "name": body.name, "email": body.email, "created_at": now_iso(), "updated_at": now_iso(),
    })
    await db.consultations.insert_one({
        "id": str(uuid.uuid4()), "name": body.name, "email": body.email, "phone": body.phone or "",
        "company": "", "area": body.area or pkg["name"], "message": body.message or "",
        "status": "payment_pending", "package": pkg["name"], "amount": pkg["amount"],
        "source": "consultation-checkout", "session_id": session.session_id, "created_at": now_iso(),
    })
    return {"checkout_url": session.url, "session_id": session.session_id}


async def _sync_paid(session_id: str):
    await db.payment_transactions.update_one(
        {"session_id": session_id, "payment_status": {"$ne": "paid"}},
        {"$set": {"status": "completed", "payment_status": "paid", "updated_at": now_iso()}})
    await db.consultations.update_one({"session_id": session_id}, {"$set": {"status": "paid"}})


@api_router.get("/payments/status/{session_id}")
async def payment_status(session_id: str, request: Request):
    record = await db.payment_transactions.find_one({"session_id": session_id})
    if not record:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if record.get("payment_status") != "paid":
        try:
            webhook_url = f"{str(request.base_url)}api/webhook/stripe"
            stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
            status = await stripe_checkout.get_checkout_status(session_id)
            if status.payment_status == "paid":
                await _sync_paid(session_id)
                record = await db.payment_transactions.find_one({"session_id": session_id})
        except Exception:
            pass
    return {"session_id": session_id, "status": record["status"], "payment_status": record["payment_status"],
            "amount": record.get("amount"), "package_id": record.get("package_id")}


@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("Stripe-Signature")
    try:
        webhook_url = f"{str(request.base_url)}api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)
        resp = await stripe_checkout.handle_webhook(body, sig)
        if resp.payment_status == "paid":
            await _sync_paid(resp.session_id)
    except Exception:
        logger.exception("Stripe webhook error")
        return {"status": "error"}
    return {"status": "ok"}


# ---------------- Services ----------------
@api_router.get("/services")
async def list_services():
    return [{"slug": s["slug"], "title": s["title"], "tagline": s["tagline"],
             "overview": s["overview"], "portrait": s["portrait"], "hero_image": s["hero_image"]}
            for s in SERVICE_PAGES]


@api_router.get("/services/{slug}")
async def get_service(slug: str):
    for s in SERVICE_PAGES:
        if s["slug"] == slug:
            return s
    raise HTTPException(status_code=404, detail="Service not found")


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


# ---------------- Booking scheduling + email ----------------
class ScheduleIn(BaseModel):
    session_id: str
    start: str
    end: str


@api_router.post("/bookings/schedule")
async def schedule_booking(body: ScheduleIn, background_tasks: BackgroundTasks):
    txn = await db.payment_transactions.find_one({"session_id": body.session_id})
    if not txn:
        raise HTTPException(status_code=404, detail="Booking not found")
    if txn.get("payment_status") != "paid":
        raise HTTPException(status_code=402, detail="Payment not confirmed yet")
    consult = await db.consultations.find_one({"session_id": body.session_id})
    try:
        start_dt = _dt.fromisoformat(body.start.replace("Z", "+00:00"))
        end_dt = _dt.fromisoformat(body.end.replace("Z", "+00:00"))
    except Exception:
        raise HTTPException(status_code=422, detail="Invalid date")
    await db.consultations.update_one({"session_id": body.session_id},
                                      {"$set": {"status": "scheduled", "slot_start": body.start, "slot_end": body.end}})
    name = (consult or {}).get("name", "Client")
    email = (consult or {}).get("email", txn.get("email", ""))
    service = (consult or {}).get("package", "Consultation")
    background_tasks.add_task(send_booking_email, body.session_id, name, email, service, start_dt, end_dt)
    return {"success": True, "message": "Session scheduled. A calendar invite is on its way."}


app.include_router(api_router)
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
                    "detail": "You appear to be connecting over a VPN or proxy. Disable it or verify with your access code to continue.",
                    "vpn_block": True})
        except Exception:
            pass

    return await call_next(request)


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id")
    await db.user_sessions.create_index("session_token")
    await db.activity_events.create_index("user_id")
    await db.support_tickets.create_index("user_id")
    await db.support_tickets.create_index("status")
    await db.login_attempts.create_index("identifier", unique=True)
    await db.login_attempts.create_index("ip")
    await db.blocked_ips.create_index("ip", unique=True)
    await db.security_alerts.create_index("created_at")
    await db.audit_log.create_index("at")
    await db.audit_log.create_index("expire_at", expireAfterSeconds=0)
    _meta = await db.app_meta.find_one({"_id": "audit_retention"})
    if _meta and _meta.get("days"):
        global _audit_retention_days
        _audit_retention_days = int(_meta["days"])
    await db.articles.create_index("slug", unique=True)
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
    asyncio.create_task(_digest_scheduler())


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
