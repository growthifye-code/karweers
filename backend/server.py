from fastapi import FastAPI, APIRouter, Request, HTTPException, Depends
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import logging
import uuid
from pathlib import Path
from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

from auth import hash_password, verify_password, create_access_token, decode_token
from seed_data import ARTICLES, SERVICES, STATS, MARKET_PULSE, TESTIMONIALS

from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

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


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ConsultationIn(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = ""
    company: Optional[str] = ""
    area: str
    message: str


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
async def register(body: RegisterIn):
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
async def login(body: LoginIn):
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
async def create_consultation(body: ConsultationIn):
    doc = body.model_dump()
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


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    if await db.articles.count_documents({}) == 0:
        docs = []
        for a in ARTICLES:
            d = dict(a)
            d.update({"id": str(uuid.uuid4()), "author": "Sudarshan Karweer", "created_at": now_iso()})
            docs.append(d)
        await db.articles.insert_many(docs)
        logger.info("Articles seeded: %d", len(docs))


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
