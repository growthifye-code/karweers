# Sudarshan Karweer — Thought Leadership & Advisory Platform (PRD)

## Product
Premium dark-theme (lime accent) advisory + thought-leadership site for Sudarshan Karweer.
Stack: React + FastAPI + MongoDB. Commerce (Razorpay), AI insight engines, enterprise security
(CORS allowlist, CSP, reCAPTCHA v3, VPN/country block, brute-force, audit logs), Learning Hub,
Admin CRM, client dashboards, and the "SK Strategy Brief" podcast (Hinglish script + ElevenLabs
cloned-voice narration + corporate music intro via ffmpeg).

## Recent changes (2026-06)
- **Security hardening (podcast)**: audio endpoint now serves unpublished episodes only to a valid
  admin token (`?token=` or Bearer) — public gets 404, cache `private,no-store`; helper `_is_admin_request`.
  Approve is now an atomic `update_one` guard (status != generating_audio) → concurrent approve = 409,
  no duplicate audio task. Verified via curl. Files: backend/server.py, frontend PodcastAdmin.jsx.
- **Podcast approval workflow**: episodes now generate in two gated stages —
  (1) `POST /admin/podcast/generate` writes only the SCRIPT → status `pending_review` (hidden from
  public); (2) admin reviews/edits via `PUT /admin/podcast/{eid}`, then `POST /admin/podcast/{eid}/approve`
  narrates it in SK's ElevenLabs voice (`generating_audio`) and auto-publishes. Nothing reaches the
  public feed until a script is approved. Weekly auto-scheduler now DRAFTS a script for approval
  (no auto-publish). Files: backend/server.py (_run_podcast_script/_run_podcast_audio, approve/edit
  endpoints), frontend/src/components/PodcastAdmin.jsx (review/edit/approve UI, "Needs approval" banner).
  Verified end-to-end via curl: generate→pending_review→edit→approve→published; public feed excludes
  drafts. UI compiles clean; live UI login blocked by reCAPTCHA in automation (humans pass).
- Navbar optimized: slimmed to 5 primary links (About · Explore · Insights · Podcast · Cases),
  renamed "Sectors & Capital" → "Explore", "Case Studies" → "Cases". Added a **More** dropdown
  (Leadership Lab, Learning, Archive, Market, Deals). Renamed "Work with SK" dropdown → "Programs".
  File: frontend/src/components/Navbar.jsx
- Added floating **Sticky Book Consultation CTA** (appears after 500px scroll, bottom-center,
  hidden on login/register/dashboard/admin/booking pages). Files: frontend/src/components/StickyBookCTA.jsx, App.js
- AI wording cleanup (authorship-label scope only): public pages already attribute content to
  "Sudarshan Karweer"; reworded admin PodcastAdmin note "Scripted by AI" → "Scripted in-house".
  File: frontend/src/components/PodcastAdmin.jsx
- Podcast voice check: verified ElevenLabs cloned-voice (ID LS37n1cCTuLWrUIuYGQ1) synthesizes valid
  Hinglish audio via primary path (not OpenAI fallback). settings: stability 0.55, similarity 0.75,
  style 0.0, speaker_boost. Test: backend/tests/voice_check.py
- Featured Episode banner on homepage (frontend/src/components/sections/FeaturedPodcast.jsx) — shows
  latest published episode with emblem, play button, inline player (intro→episode) and All-episodes link.

## Integrations
Claude Sonnet 4.6 (Emergent key), Gemini image gen, OpenAI TTS (fallback), ElevenLabs (user key,
voice clone), reCAPTCHA v3 (user keys), Razorpay (live), Emergent Google Auth, Google Calendar.

## Backlog
- P1: Add Razorpay Webhook Secret to production env.
- P2: WhatsApp Business API; IPQualityScore fallback for VPN guard; replace coaching hero video with
  real footage; Live Trend Topics via Perplexity/Tavily (user opted to skip for now).
- Future: live low-value payment decline test (auto-refund path); SPF/DKIM/DMARC DNS; confirm edge
  IP header w/ Emergent Support and set CLIENT_IP_HEADER.
- Blocked: starlette/litellm CVEs (platform-managed wheels).

## Notes
- Env changes (CORS, ElevenLabs, reCAPTCHA keys) require user "Redeploy" to reach live site.
- server.py is >8000 lines: define static routes before parameterized routes.
- Admin: sudarshan@karweers.com; ADMIN_PATH in backend/.env; creds in memory/test_credentials.md.
