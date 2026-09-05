"""The SK Strategy Brief — AI-generated podcast: script (Claude) + narration (OpenAI TTS) + storage."""
import os
import re
import json
import uuid
import logging
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone
from emergentintegrations.llm.openai import OpenAITextToSpeech
import storage_helper

log = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")
PODCAST_NAME = "The SK Strategy Brief"
VOICE = "onyx"
TTS_MODEL = "tts-1-hd"
TTS_CHUNK = 3600  # under the 4096-char per-request limit

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
    "incisive, story-led, no fluff, no jargon-for-jargon's-sake. Audience: founders and CXOs."
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
        "It must be spoken by ME (Sudarshan Karweer) in first person. Structure the narration:\n"
        "1) A signature 2-3 sentence open that starts EXACTLY with: \"I'm Sudarshan Karweer, and this is "
        f"{PODCAST_NAME}.\" Then a punchy hook for today's topic.\n"
        "2) The body: a rich, highly engaging 700-1000 word take — a clear point of view, 2-3 vivid real-world "
        "examples or mini-stories, a simple framework or checklist leaders can use, and one contrarian insight.\n"
        "3) A tight close with a single call to action to book a 1:1 strategy session.\n\n"
        "Sound natural for the EAR (short sentences, spoken rhythm, no headings, no bullet symbols, no markdown). "
        "Return STRICT JSON only, no markdown fences: {\"title\": punchy episode title (<70 chars), "
        "\"description\": 2-sentence show-notes summary, \"script\": the full spoken narration as plain text, "
        "\"key_takeaways\": [3-5 short bullet strings]}."
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


async def synthesize(script_text: str) -> bytes:
    """Narrate the script with OpenAI TTS (onyx), concatenating chunk audio into one mp3."""
    tts = OpenAITextToSpeech(api_key=EMERGENT_LLM_KEY)
    audio = b""
    for c in chunk_text(clean_for_tts(script_text)):
        audio += await tts.generate_speech(text=c, model=TTS_MODEL, voice=VOICE, response_format="mp3")
    return audio


def store_audio(episode_id: str, audio: bytes) -> str:
    path = f"podcast/{episode_id}.mp3"
    storage_helper.put_object(path, audio, "audio/mpeg")
    return path


def estimate_minutes(script_text: str) -> int:
    words = len(script_text.split())
    return max(1, round(words / 150))
