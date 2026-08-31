"""Curated YouTube learning engine — no API key required.

Pulls each reputable channel's public RSS feed (latest uploads) so the
catalogue always stays fresh, then rotates a daily selection and supports
personalised recommendations based on a client's browsing interests.
"""
import time
import re
import json
import hashlib
import logging
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

import requests

logger = logging.getLogger(__name__)

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
_ATOM = "{http://www.w3.org/2005/Atom}"
_YT = "{http://www.youtube.com/xml/schemas/2015}"
_MEDIA = "{http://search.yahoo.com/mrss/}"

TOPICS = [
    {"id": "global-macro", "label": "Global Macro & Economy", "blurb": "Growth, inflation, rates and the forces shaping the world economy."},
    {"id": "india-economy", "label": "India Economy", "blurb": "Markets, policy and business intelligence from India."},
    {"id": "energy", "label": "Energy & Renewables", "blurb": "The energy transition — solar, storage, hydrogen and power markets."},
    {"id": "climate-finance", "label": "Climate & Green Finance", "blurb": "Financing decarbonisation and the road to net-zero."},
    {"id": "ai", "label": "Machine Intelligence", "blurb": "How machine intelligence is reshaping industry and strategy."},
    {"id": "technology", "label": "Emerging Technology", "blurb": "Deep tech, innovation and the ideas moving fastest."},
    {"id": "fundraising", "label": "Fundraising & Startups", "blurb": "Raising capital, building and scaling ventures."},
    {"id": "leadership", "label": "Leadership & Coaching", "blurb": "Strategy, decision-making and world-class leadership."},
    {"id": "geopolitics", "label": "Geopolitics", "blurb": "Power, policy and the geopolitics of a shifting order."},
]
TOPIC_IDS = [t["id"] for t in TOPICS]

# Reputable channels (verified channel IDs) mapped to topic tags.
CHANNELS = [
    {"channel_id": "UCIYhr3JsLYfKkCM7-W5B6DA", "source": "IMF", "topics": ["global-macro"]},
    {"channel_id": "UCoUxsWakJucWg46KW5RsvPw", "source": "Financial Times", "topics": ["global-macro", "geopolitics"]},
    {"channel_id": "UC0p5jTq6Xx_DosDFxVXnWaQ", "source": "The Economist", "topics": ["global-macro", "geopolitics"]},
    {"channel_id": "UC-dgj7woFJuUG0As9kuGNhw", "source": "Bloomberg", "topics": ["global-macro", "energy"]},
    {"channel_id": "UCw-kH-Od73XDAt7qtH9uBYA", "source": "World Economic Forum", "topics": ["global-macro", "climate-finance", "geopolitics"]},
    {"channel_id": "UCmRbHAgG2k2vDUvb3xsEunQ", "source": "CNBC-TV18", "topics": ["india-economy", "global-macro"]},
    {"channel_id": "UCiMPkzrVSCEDm3TatvdVylw", "source": "International Energy Agency", "topics": ["energy", "climate-finance"]},
    {"channel_id": "UCP7jMXSY2xbc3KCAE0MHQ-A", "source": "Google DeepMind", "topics": ["ai", "technology"]},
    {"channel_id": "UCSHZKyawb77ixDdsGog4iWA", "source": "Lex Fridman", "topics": ["ai", "technology"]},
    {"channel_id": "UC9cn0TuPq4dnbTY-CBsm8XA", "source": "a16z", "topics": ["ai", "technology", "fundraising"]},
    {"channel_id": "UCAuUUnT6oDeKwE6v1NGQxug", "source": "TED", "topics": ["technology", "leadership", "ai"]},
    {"channel_id": "UCcefcZRL2oaA_uBNeo5UOWg", "source": "Y Combinator", "topics": ["fundraising", "leadership"]},
    {"channel_id": "UCGwuxdEeCf0TIA2RbPOj-8g", "source": "Stanford Graduate School of Business", "topics": ["leadership", "fundraising"]},
    {"channel_id": "UCRH2-9Jc5Dk334o1uX4Z74w", "source": "Council on Foreign Relations", "topics": ["geopolitics", "global-macro"]},
]

# Map a browsing context to learning topics for the recommendation engine.
SERVICE_TOPICS = {
    "premium-consultation": ["leadership", "fundraising"],
    "re-storage-hydrogen": ["energy", "technology"],
    "green-climate-financing": ["climate-finance", "global-macro"],
    "asset-monetisation": ["global-macro", "india-economy"],
    "business-coaching": ["leadership"],
}
KIND_TOPICS = {
    "market": ["global-macro", "energy"],
    "deals": ["energy", "climate-finance"],
    "insight": ["energy", "global-macro"],
    "casestudy": ["energy", "climate-finance"],
}

_CACHE = {"ts": 0, "videos": []}
_TTL = 6 * 3600  # refresh pool every 6 hours


def derive_topics(kind: str, ref: str = "") -> list:
    kind = (kind or "").lower()
    ref = (ref or "").lower()
    if kind == "video" and ref in TOPIC_IDS:
        return [ref]
    if kind == "service":
        return SERVICE_TOPICS.get(ref, ["leadership"])
    if kind == "topic" and ref in TOPIC_IDS:
        return [ref]
    return KIND_TOPICS.get(kind, [])


def _fetch_channel(ch: dict) -> list:
    try:
        url = "https://www.youtube.com/feeds/videos.xml"
        r = requests.get(url, params={"channel_id": ch["channel_id"]}, headers={"User-Agent": _UA}, timeout=8)
        root = ET.fromstring(r.content)
        out = []
        for entry in root.findall(f"{_ATOM}entry"):
            vid = entry.findtext(f"{_YT}videoId") or ""
            title = entry.findtext(f"{_ATOM}title") or ""
            published = entry.findtext(f"{_ATOM}published") or ""
            link_el = entry.find(f"{_ATOM}link")
            href = link_el.get("href") if link_el is not None else ""
            if not vid or "/shorts/" in href:  # skip shorts, keep full talks
                continue
            group = entry.find(f"{_MEDIA}group")
            thumb = ""
            desc = ""
            if group is not None:
                th = group.find(f"{_MEDIA}thumbnail")
                if th is not None:
                    thumb = th.get("url", "")
                d = group.find(f"{_MEDIA}description")
                desc = (d.text or "")[:220] if d is not None else ""
            out.append({
                "video_id": vid,
                "title": title,
                "source": ch["source"],
                "source_url": f"https://www.youtube.com/channel/{ch['channel_id']}",
                "topics": ch["topics"],
                "published": published,
                "thumbnail": thumb or f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                "description": desc,
            })
            if len(out) >= 12:
                break
        return out
    except Exception as e:
        logger.warning("curator: failed to fetch %s: %s", ch["source"], e)
        return []


def _pool() -> list:
    now = time.time()
    if now - _CACHE["ts"] < _TTL and _CACHE["videos"]:
        return _CACHE["videos"]
    with ThreadPoolExecutor(max_workers=10) as ex:
        results = list(ex.map(_fetch_channel, CHANNELS))
    videos = [v for batch in results for v in batch]
    if videos:
        _CACHE["ts"] = now
        _CACHE["videos"] = videos
    return _CACHE["videos"]


def _published_ts(v: dict) -> float:
    try:
        return datetime.fromisoformat(v["published"].replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _seed(video_id: str, salt: str) -> int:
    return int(hashlib.md5(f"{salt}:{video_id}".encode()).hexdigest(), 16)


def _dedupe(videos: list) -> list:
    seen, out = set(), []
    for v in videos:
        if v["video_id"] in seen:
            continue
        seen.add(v["video_id"])
        out.append(v)
    return out


def _interleave_by_source(videos: list) -> list:
    """Round-robin across sources (each already freshness-ordered) for a balanced grid."""
    buckets = {}
    for v in videos:
        buckets.setdefault(v["source"], []).append(v)
    order = sorted(buckets.keys(), key=lambda s: _published_ts(buckets[s][0]), reverse=True)
    out = []
    while any(buckets[s] for s in order):
        for s in order:
            if buckets[s]:
                out.append(buckets[s].pop(0))
    return out


def library(topic: str = None, limit: int = 60) -> list:
    videos = _dedupe(_pool())
    if topic and topic in TOPIC_IDS:
        videos = [v for v in videos if topic in v["topics"]]
    videos.sort(key=_published_ts, reverse=True)
    return _interleave_by_source(videos)[:limit]


def daily(limit: int = 10) -> list:
    """Deterministic per-day selection that spreads across topics and refreshes daily."""
    videos = _dedupe(_pool())
    if not videos:
        return []
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Rank recent uploads, then shuffle-by-day so the set feels fresh each day.
    videos.sort(key=lambda v: (_published_ts(v), _seed(v["video_id"], day)), reverse=True)
    recent = videos[: max(limit * 4, 30)]
    recent.sort(key=lambda v: _seed(v["video_id"], day))
    picked, used_topics, out = [], {}, []
    # First pass: one per topic for variety.
    for v in recent:
        t = v["topics"][0]
        if used_topics.get(t):
            continue
        used_topics[t] = True
        out.append(v)
        if len(out) >= limit:
            return out
    # Fill remaining slots.
    for v in recent:
        if v in out:
            continue
        out.append(v)
        if len(out) >= limit:
            break
    return out[:limit]


def recommended(topic_weights: dict, limit: int = 12) -> list:
    """topic_weights: {topic_id: score}. Returns videos ranked by interest + freshness."""
    videos = _dedupe(_pool())
    if not videos:
        return []
    if not topic_weights:
        return daily(limit)
    max_ts = max((_published_ts(v) for v in videos), default=0) or 1
    min_ts = min((_published_ts(v) for v in videos if _published_ts(v) > 0), default=0)
    span = (max_ts - min_ts) or 1
    max_w = max(topic_weights.values()) or 1

    def score(v):
        interest = sum(topic_weights.get(t, 0) for t in v["topics"]) / max_w
        freshness = (_published_ts(v) - min_ts) / span
        return interest * 2.2 + freshness
    videos.sort(key=score, reverse=True)
    return videos[:limit]


# ---- Book-specific YouTube search (no API key; scrapes public search results) ----
_SEARCH_CACHE: dict = {}
_SEARCH_TTL = 24 * 3600  # cache each book's videos for a day


def book_videos(query: str, limit: int = 6) -> list:
    """Return YouTube videos specifically about a book (title + author query).

    Scrapes YouTube's public search results (videos-only filter) and parses
    ytInitialData. Cached per query for a day. Returns [] on any failure so the
    caller can hide the Watch tab when nothing specific is found.
    """
    key = (query or "").lower().strip()
    if not key:
        return []
    now = time.time()
    c = _SEARCH_CACHE.get(key)
    if c and now - c["ts"] < _SEARCH_TTL:
        return c["videos"][:limit]
    try:
        r = requests.get(
            "https://www.youtube.com/results",
            params={"search_query": query, "sp": "EgIQAQ%3D%3D"},  # type=video
            headers={"User-Agent": _UA, "Accept-Language": "en-US,en;q=0.9"},
            timeout=10,
        )
        m = re.search(r"var ytInitialData = (\{.*?\});</script>", r.text)
        if not m:
            m = re.search(r'ytInitialData\s*=\s*(\{.*?\});', r.text)
        data = json.loads(m.group(1)) if m else {}
        found = []

        def walk(node):
            if isinstance(node, dict):
                vr = node.get("videoRenderer")
                if vr and vr.get("videoId"):
                    runs = (vr.get("title", {}) or {}).get("runs") or []
                    title = runs[0].get("text", "") if runs else ""
                    ot = ((vr.get("ownerText", {}) or {}).get("runs")
                          or (vr.get("longBylineText", {}) or {}).get("runs") or [])
                    owner = ot[0].get("text", "") if ot else ""
                    vid = vr["videoId"]
                    found.append({
                        "video_id": vid,
                        "title": title,
                        "source": owner or "YouTube",
                        "source_url": f"https://www.youtube.com/watch?v={vid}",
                        "topics": ["leadership"],
                        "published": "",
                        "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
                        "description": "",
                    })
                for v in node.values():
                    walk(v)
            elif isinstance(node, list):
                for v in node:
                    walk(v)

        walk(data)
        seen, out = set(), []
        for v in found:
            if v["video_id"] in seen:
                continue
            seen.add(v["video_id"])
            out.append(v)
        if out:
            _SEARCH_CACHE[key] = {"ts": now, "videos": out}
        return out[:limit]
    except Exception as e:
        logger.warning("curator.book_videos failed for %s: %s", query, e)
        return []
