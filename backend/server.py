from fastapi import FastAPI, APIRouter, Request, HTTPException, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
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
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from auth import hash_password, verify_password, create_access_token, decode_token
from seed_data import ARTICLES, SERVICES, STATS, MARKET_PULSE, TESTIMONIALS
from services_data import SERVICES as SERVICE_PAGES
from emailer import send_booking_email
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
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


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
    doc = {
        "id": uid, "email": email, "name": body.name,
        "password_hash": hash_password(body.password), "role": "client",
        "created_at": now_iso(),
    }
    await db.users.insert_one(doc)
    token = create_access_token(uid, email, "client")
    return {"token": token, "user": {"id": uid, "email": email, "name": body.name, "role": "client"}}


@api_router.post("/auth/login")
async def login(body: LoginIn, request: Request):
    verify_captcha(body.captcha_token, request.client.host if request.client else None)
    email = body.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], email, user["role"])
    return {"token": token, "user": {"id": user["id"], "email": email, "name": user["name"], "role": user["role"]}}


@api_router.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user


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
    doc.update({"id": str(uuid.uuid4()), "status": "new", "created_at": now_iso()})
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
        "session_id": session.session_id, "created_at": now_iso(),
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


@app.on_event("startup")
async def startup():
    await db.users.create_index("email", unique=True)
    await db.users.create_index("id")
    await db.articles.create_index("slug", unique=True)
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
    # Seed articles
    # Seed / ensure articles (upsert by slug, non-destructive)
    for a in ARTICLES:
        if not await db.articles.find_one({"slug": a["slug"]}):
            d = dict(a)
            d.update({"id": str(uuid.uuid4()), "author": "Sudarshan Karweer", "created_at": now_iso()})
            await db.articles.insert_one(d)
    logger.info("Articles ensured")


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
