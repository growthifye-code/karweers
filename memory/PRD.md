# Sudarshan Karweer — Thought Leadership & Advisory Platform (PRD)

## Product
Premium dark-theme (lime accent) advisory + thought-leadership site for Sudarshan Karweer.
Stack: React + FastAPI + MongoDB. Commerce (Razorpay), AI insight engines, enterprise security
(CORS allowlist, CSP, reCAPTCHA v3, VPN/country block, brute-force, audit logs), Learning Hub,
Admin CRM, client dashboards, and the "SK Strategy Brief" podcast (Hinglish script + ElevenLabs
cloned-voice narration + corporate music intro via ffmpeg).

## Recent changes (2026-06)
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
