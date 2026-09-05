"""The SK Strategy Brief — podcast: script (Claude) + narration (ElevenLabs, SK's cloned voice; OpenAI TTS fallback) + storage."""
import os
import re
import json
import uuid
import logging
import requests
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
from emergentintegrations.llm.openai import OpenAITextToSpeech
import storage_helper

log = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
PODCAST_NAME = "The SK Strategy Brief"
# ElevenLabs — Sudarshan Karweer's cloned voice (primary narration).
ELEVENLABS_API_KEY = os.environ.get("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.environ.get("ELEVENLABS_VOICE_ID", "")
ELEVENLABS_MODEL = os.environ.get("ELEVENLABS_MODEL", "eleven_multilingual_v2")
EL_CHUNK = 2400  # keep each TTS request well under ElevenLabs limits
# OpenAI TTS — silent fallback only if ElevenLabs is unavailable.
VOICE = "onyx"
TTS_MODEL = "tts-1-hd"
TTS_CHUNK = 3600

TOPICS = [
    "The energy transition and what boards keep getting wrong",
    "Battery energy storage (BESS): the economics leaders miss",
    "Green hydrogen — hype, reality, and where the money actually is",
    "Climate finance and unlocking capital for the transition",
    "Fundraising: how founders win the room with CFOs and lenders",
    "Scaling a company without breaking what made it work",
    "Strategy vs. execution: closing the say-do gap",
    "Designing org structure that actually supports the strategy",
    "People and culture as a competitive moat",
    "Processes that scale — removing friction without adding bureaucracy",
    "KPIs and scorecards that drive the right behaviour",
    "What separates winning companies from the rest",
    "Transition management: leading change people will follow",
    "Hiring for slope, not just for the role",
    "Turning complexity into competitive advantage",
    "Capital allocation discipline for growth-stage CEOs",
]

_SYSTEM = (
    "You are the scriptwriter and voice of Sudarshan Karweer — a business coach and strategic advisor, "
    "former EY (Big 4) management consultant with 23+ years and 60+ corporate projects across India and "
    "globally, and $2B+ in debt syndication. You write in first person AS Sudarshan: warm, direct, "
    "incisive, story-led, no fluff, no jargon-for-jargon's-sake. Audience: founders and CXOs.\n\n"
    "LANGUAGE — write in natural HINGLISH, the way urban Indian business leaders actually speak: fluidly "
    "code-mixing Hindi and English in the same sentence. Keep business/technical terms in English. Use "
    "DEVANAGARI script for the Hindi words and phrases (e.g. मतलब, असली सवाल यह है, समझिए, है ना) and Latin "
    "for the English — this makes the voice pronounce each language correctly. It should feel like a real "
    "conversation, relatable and warm — never a translation. Do NOT overdo the Hindi; roughly 30-40% Hindi, "
    "60-70% English, mixed naturally."
)


def clean_for_tts(text: str) -> str:
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"`{1,3}[^`]*`{1,3}", "", text)
    text = re.sub(r"[*_#>~|]", "", text)
    text = re.sub(r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF]", "", text)  # emoji/dingbats
    return re.sub(r"\s+", " ", text).strip()


def chunk_text(text: str, size: int = TTS_CHUNK):
    """Split into <size chunks on sentence boundaries."""
    text = text.strip()
    if len(text) <= size:
        return [text] if text else []
    out, cur = [], ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if len(cur) + len(sentence) + 1 > size:
            if cur:
                out.append(cur.strip())
            # a single monster sentence: hard-split
            while len(sentence) > size:
                out.append(sentence[:size])
                sentence = sentence[size:]
            cur = sentence
        else:
            cur = f"{cur} {sentence}".strip()
    if cur:
        out.append(cur.strip())
    return out


async def generate_script(topic: str) -> dict:
    """Returns {title, description, script, key_takeaways[]}. `script` is the full narration."""
    prompt = (
        f"Write ONE episode of my weekly podcast '{PODCAST_NAME}'. Topic: {topic}.\n\n"
        "It must be spoken by ME (Sudarshan Karweer) in first person, in natural HINGLISH (Hindi in "
        "Devanagari, English in Latin, code-mixed the way Indian CXOs really talk). Structure the narration:\n"
        "1) A signature 2-3 sentence open that starts EXACTLY with: \"I'm Sudarshan Karweer, and this is "
        f"{PODCAST_NAME}.\" Then a punchy Hinglish hook for today's topic.\n"
        "2) The body: a rich, highly engaging 700-1000 word Hinglish take — a clear point of view, 2-3 vivid "
        "real-world examples or mini-stories, a simple framework or checklist leaders can use, and one "
        "contrarian insight.\n"
        "3) Sprinkle in 4-6 ENGAGING RHETORICAL QUESTIONS to pull the listener in. Ask several of them in BOTH "
        "languages back-to-back for punch — the Hindi version in Devanagari immediately followed by the English "
        "version (e.g. 'असली सवाल यह है — क्या आपका business cash पर चल रहा है या hope पर? The real question is: "
        "is your business running on cash, or on hope?'). Make these questions feel provocative and personal.\n"
        "4) A tight Hinglish close with a single call to action to book a 1:1 strategy session.\n\n"
        "Sound natural for the EAR (short sentences, spoken rhythm, no headings, no bullet symbols, no markdown). "
        "Return STRICT JSON only, no markdown fences: {\"title\": punchy episode title (<70 chars, English is fine), "
        "\"description\": 2-sentence Hinglish show-notes summary, \"script\": the full spoken Hinglish narration as "
        "plain text, \"key_takeaways\": [3-5 short Hinglish bullet strings]}."
    )
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id="podcast-" + uuid.uuid4().hex,
                   system_message=_SYSTEM).with_model("anthropic", "claude-sonnet-4-6")
    text = ""
    async for ev in chat.stream_message(UserMessage(text=prompt)):
        if isinstance(ev, TextDelta):
            text += ev.content
        elif isinstance(ev, StreamDone):
            break
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text[:4].lower() == "json":
            text = text[4:]
    data = json.loads(text)
    return {
        "title": (data.get("title") or topic)[:120],
        "description": data.get("description", ""),
        "script": data.get("script", ""),
        "key_takeaways": [t for t in (data.get("key_takeaways") or []) if isinstance(t, str)][:6],
    }


def _elevenlabs_tts(text: str) -> bytes:
    """Narrate with ElevenLabs using SK's cloned voice. Raises on any failure."""
    if not (ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID):
        raise RuntimeError("ElevenLabs not configured")
    audio = b""
    for c in chunk_text(clean_for_tts(text), EL_CHUNK):
        r = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}",
            headers={"xi-api-key": ELEVENLABS_API_KEY, "Content-Type": "application/json"},
            json={
                "text": c,
                "model_id": ELEVENLABS_MODEL,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.85,
                                    "style": 0.0, "use_speaker_boost": True},
            },
            timeout=120,
        )
        if r.status_code != 200 or not r.content:
            raise RuntimeError(f"ElevenLabs TTS {r.status_code}: {r.text[:200]}")
        audio += r.content
    return audio


async def synthesize(script_text: str) -> bytes:
    """Narrate the script in Sudarshan's cloned voice (ElevenLabs). Falls back to OpenAI TTS
    only if ElevenLabs is unavailable, so episode generation never hard-fails."""
    try:
        return _elevenlabs_tts(script_text)
    except Exception as e:
        log.warning("ElevenLabs narration failed (%s) — falling back to OpenAI TTS.", e)
    tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
    audio = b""
    for c in chunk_text(clean_for_tts(script_text), TTS_CHUNK):
        audio += await tts.generate_speech(text=c, model=TTS_MODEL, voice=VOICE, response_format="mp3")
    return audio


def store_audio(episode_id: str, audio: bytes) -> str:
    path = f"podcast/{episode_id}.mp3"
    storage_helper.put_object(path, audio, "audio/mpeg")
    return path


def estimate_minutes(script_text: str) -> int:
    words = len(script_text.split())
    return max(1, round(words / 150))



async def suggest_topics(site_context: str = "", n: int = 8) -> list:
    """AI-generate fresh podcast topic ideas grounded in (i) the site's positioning/content,
    (ii) themes currently resonating socially with business audiences, and (iii) the economic
    sentiment facing organisations by size — small, MSME, and large. Returns a list of
    {topic, segment, angle, rationale}."""
    prompt = (
        "Generate " + str(n) + " sharp, timely episode topics for my weekly podcast "
        f"'{PODCAST_NAME}'. Ground them in THREE lenses:\n"
        "1) MY WORK / SITE CONTENT — what I advise on: strategy, scaling, org design, people & "
        "culture, fundraising & debt syndication, the energy transition (BESS, green hydrogen, "
        "climate finance), KPIs, transition management.\n"
        + (f"Extra context from my site:\n{site_context}\n" if site_context else "")
        + "2) WHAT'S RESONATING SOCIALLY right now with founders and CXOs — the conversations "
        "leaders are actually having (AI adoption, cost discipline, talent, capital access, etc.).\n"
        "3) ECONOMIC SENTIMENT by ORGANISATION SIZE — what SMALL businesses, MSMEs, and LARGE "
        "enterprises each most want to hear given the current economic climate (cashflow, credit, "
        "demand, growth vs. survival). Spread the topics across these three segments.\n\n"
        "Each topic must be specific and provocative (not generic), and something I (Sudarshan "
        "Karweer) can deliver a strong, contrarian point of view on. Return STRICT JSON only, no "
        "markdown fences: {\"topics\": [{\"topic\": short episode topic (<90 chars), "
        "\"segment\": one of \"small\"|\"msme\"|\"large\"|\"all\", "
        "\"angle\": one-line spoken hook/angle, "
        "\"rationale\": one line on why it lands now}]}"
    )
    chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id="topics-" + uuid.uuid4().hex,
                   system_message=_SYSTEM).with_model("anthropic", "claude-sonnet-4-6")
    text = ""
    async for ev in chat.stream_message(UserMessage(text=prompt)):
        if isinstance(ev, TextDelta):
            text += ev.content
        elif isinstance(ev, StreamDone):
            break
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text[:4].lower() == "json":
            text = text[4:]
    data = json.loads(text)
    out = []
    for t in (data.get("topics") or []):
        if isinstance(t, dict) and t.get("topic"):
            out.append({
                "topic": str(t["topic"])[:140],
                "segment": (t.get("segment") or "all").lower(),
                "angle": str(t.get("angle", ""))[:200],
                "rationale": str(t.get("rationale", ""))[:200],
            })
    return out[:n]
