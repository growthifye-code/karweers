# PRD — Sudarshan Karweer Thought-Leadership Platform

## Original Problem Statement
Build www.sudarshankarweer.com — a contemporary, rich, "colourful and classy" personal-brand site that showcases Sudarshan Karweer's thought leadership and work; a Premium 1:1 Consultation CTA for business owners in RE / energy storage (fundraising, strategy, new business development, scaling); positions him as a renowned business coach (23Y+, 60+ projects, corporates/CXOs). Content: macro/micro economic news, blogs (business/economics/sustainability/climate change/climate & green financing), company analysis (RE, Storage, Green Hydrogen), climate/storage/hydrogen tech R&D, and government asset monetisation (e.g. MSRTC bus depots). Embedded AI engine across the site. UI similar to growthifye.com. Client login + admin panel (admin: sudarshan@karweers.com).

## Architecture
- **Backend**: FastAPI + MongoDB (motor). All routes under `/api`. JWT Bearer auth (localStorage token), bcrypt hashing. Admin + articles seeded on startup.
- **Frontend**: React 19 + Tailwind + shadcn + framer-motion + lucide + sonner. Dark-default premium theme (obsidian + emerald #118D57 + ochre #F2A900), Playfair Display + Manrope.
- **AI**: Claude Sonnet 4.6 via emergentintegrations (Emergent Universal LLM key). SSE streaming chat widget + admin article generator.

## User Personas
1. **Business owner / founder (RE, storage)** — reads insights, books premium consultation.
2. **Client (registered)** — dashboard, saved access, AI engine.
3. **Admin (Sudarshan / team)** — manages articles, consultation leads, AI content generation.

## Core Requirements (static)
- Premium personal brand with Uber-style wordmark logo (Sudarshan.K)
- Thought leadership + services + case studies + market pulse
- Insights hub: news, analysis, blogs, R&D, case studies with filters
- Consultation lead capture (DB stored)
- Embedded AI engine (chat + admin generation)
- Client auth + admin panel

## Implemented (2026-06)
### Iteration 6 additions
- Hero now uses an AI-generated image of Sudarshan coaching a leadership team (boardroom, lime-accented); auto-animates (Ken-Burns), play button removed
- Sector case studies added: Aviation, Metals & Mining, Telecom, Agriculture (appear in Case Studies + Insights)
- All home-page Service cards are clickable → link to their /services/:slug pages (slugs added to seed SERVICES + /api/meta)
- Article seeding made idempotent (upsert by slug) so new content lands in existing DBs

### Iteration 5 additions
- Fresh, bolder UI: display font switched to Bricolage Grotesque (distinctive contemporary grotesque), Cormorant serif retained for the logo, Outfit body — high-contrast, fresh feel
- Hero now plays a real coaching VIDEO (boardroom/leadership footage, autoplay muted loop) with a transparent gradient overlay + "Coaching CXOs & senior leadership" caption (stock placeholder for Sudarshan's own coaching film)
- Multi-sector positioning: new Sectors marquee (M&A, Aviation, Metals & Mining, Industrial & Consumer, Cement, Steel, Telecom, Agriculture, Start-up Funding, RE, Storage, Green Hydrogen, Climate Finance, Asset Monetisation); stat updated to "12+ Sectors Covered"; About page sectors band

### Iteration 4 (redesign) additions
- New "Uber-rich" editorial UI: unique font pairing — Cormorant Garamond (display) + Outfit (UI); deeper near-black canvas (#050505) with brighter lime accent (#C6F135)
- SK favicon (lime monogram) wired into index.html
- SEO heading hierarchy confirmed (one H1 per page, H2 sections, H3 cards) + per-page titles/OG/JSON-LD, robots.txt, sitemap.xml
- Service pages now use relevant SERVICE photos (battery storage, green finance, bus depot, boardroom); only the Premium 1:1 Consultation page/card keeps Sudarshan's portrait

### Iteration 3 additions
- Detailed Service pages (/services + /services/:slug) with workflow, approach & key outcomes; each workflow phase has its own sub-page (/services/:slug/:phase)
- Growthifye-style header: lime top bar (phone/email), Services hover dropdown + links to every page; new SK logo (Playfair wordmark + lime monogram)
- Impressive About Me page (/about) — journey timeline + philosophy, single processed portrait
- Lime-green theme across site; AI-processed zoomed portraits (bg removed, lime rim light); max ONE Sudarshan photo per page
- Animated Ken-Burns hero portrait with play button (brand-film placeholder)
- hCaptcha (test keys) on login/register/consultation/newsletter/checkout
- Security: hardened headers (HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy), 30-min inactivity auto-logout, admin locked to sudarshan@karweers.com
- Live Deals ticker (Google News RSS, renewables M&A/fundraises, 6h refresh)
- In-app scheduling after paid consultation + emailed .ics invite (Gmail SMTP; no-op until app password set)
- Legal: Privacy/GDPR, Terms (incl. payment terms), Refund policy pages
- SEO: per-page titles + OG + JSON-LD, robots.txt, sitemap.xml
- AI widget renamed to "Ask SK"

### Iteration 2 additions
- Real client photos of Sudarshan Karweer across hero, about, login, register (src/lib/assets.js)
- Uber-style typography (Plus Jakarta Sans) replacing serif headings
- Paid consultation via Stripe (test mode, shared sandbox) — 3 packages ($99/$299/$599), checkout + success/cancel pages, bookings tracked as consultation leads
- Live Market Pulse — real Yahoo Finance quotes (lithium, solar ETFs, First Solar, Enphase, Tesla, copper, crude), auto-refresh every 2 min, LIVE badge
- Newsletter signup + admin Subscribers tab
- Real contact details (email sudarshan@karweers.com, phone +91 72089 98944, WhatsApp 917208998944)

### Iteration 1
- Landing page: Hero, Stats, About/Thought Leadership, Services (bento), Market Pulse (+ticker), Insights preview, Case Studies, Consultation + testimonials, Footer
- Insights list page with category filters; Article detail page with related + CTA
- Consultation lead form → POST /api/consultations (stored, confirmation toast)
- AI chat widget "Ask Karweer AI" (Claude Sonnet 4.6, SSE streaming)
- Auth: register/login/me (JWT Bearer, admin sudarshan@karweers.com seeded)
- Client dashboard; Admin dashboard (Overview stats, Leads mgmt + status, Articles list + delete, Create+AI: AI draft generation + publish)
- 12 seeded articles across all categories incl. MSRTC bus depot monetisation case study
- Dark/light theme toggle; responsive; data-testids throughout
- Verified: 25/25 backend tests pass, all frontend flows pass

## Backlog / Remaining
- **P1**: Paid consultation (Stripe) — user listed as an option; currently lead-form only
- **P1**: Live news/market data feeds (currently AI-curated + admin-managed; benchmarks are indicative)
- **P2**: Cookie-based auth + login rate-limiting/lockout (playbook hardening)
- **P2**: Object storage for admin image uploads (currently image URL field)
- **P2**: Upsert-by-slug so seed_data changes propagate; status enum validation on PATCH
- **P2**: LinkedIn/news gallery, newsletter subscribe

## Next Tasks
- Confirm real contact details (email/phone/WhatsApp are placeholders: sudarshan@karweers.com, +91 99999 99999)
- Decide on paid vs free consultation model
- Provide news source APIs if live feeds desired

---

## Iteration 4 (Aug 31, 2026)
- **Logo**: Redesigned to an elegant text wordmark — white **S** + lime **K.** (serif, no box), matching favicon.
- **hCaptcha STRICT**: real secret key wired in (`HCAPTCHA_SECRET`); backend now rejects invalid tokens (403), missing (400). Applies to login/register/newsletter/consultation/checkout.
- **Google Login (Emergent-managed)**: "Continue with Google" on /login & /register. Backend `/api/auth/session` exchanges Emergent session → httpOnly `session_token` cookie (also accepted as Bearer); `/api/auth/logout`. `get_current_user` resolves Google session OR JWT. AuthCallback route handles `#session_id`.
- **Admin Allowlist (strict)**: ONLY `sudarshan@karweers.com` and `sudarshan.karweer@gmail.com` can ever be admin (`ADMIN_ALLOWLIST` env, case-insensitive). Enforced on register, login, Google session, and startup (promotes allowlisted, demotes all others). Everyone else = client.
- **Learning Hub** (`/learning` + home "The Curator's Watchlist" section + navbar link): curated YouTube videos via 14 reputable channels' public RSS feeds (NO API key), always fresh. Topic filters (9 topics), embedded click-to-play players with source credit. Home strip = daily rotation (max ~8-10). `curator.py` handles fetch/cache(6h)/rotation/interleave.
- **Recommendation engine**: `/api/track {kind, ref}` logs client browsing (service views, video plays, topic clicks). `/api/learning/recommended` weights by topic interest × recency (0.94^days). Personalised sections on ClientDashboard + LearningPage.
- Verified: backend 20/20 new tests pass (iteration_4.json); frontend 14/15 (1 flaky non-bug). Admin allowlist self-verified.

## Backlog / Remaining (updated)
- **P1**: Go-live Stripe keys + Gmail App Password (real payments & booking emails + weekly digest) — awaiting user. NOTE: Gmail needs a 16-char App Password (2FA), normal password is rejected.
- **P2**: Advisory hardening — split server.py (~1033 lines) into routers; set explicit CORS origins; remove dead hCaptcha lenient branch
- **P2**: Replace AI coaching hero with real transparent video when user provides asset
- **P2**: Object storage for admin image uploads

---

## Iteration 5 (Aug 31, 2026) — CRM, Service Desk, Personalisation, GDPR, SEO, Branding
- **Admin CRM**: `/admin/clients` + client drawer with interest profile, activity timeline, bookings, tickets. Every client has a unique `client_code` (SK-XXXXXX), auto-assigned + backfilled.
- **Service Desk**: clients raise tickets from dashboard (TK-XXXXXX); admin queue with status (open/in-progress/resolved/closed) + priority + threaded replies. Leads pipeline stages: new→contacted→qualified→paid→scheduled→won/lost/closed.
- **Personalisation**: interest capture at login (`/me/interests`), recommended videos + relevant blogs (`/me/blogs`) driven by declared interests × activity recency. Expanded tracking (`/track` with label incl. page views).
- **GDPR**: consent banner gates tracking; Privacy Policy rewritten (tracking/personalisation/rights); client data export (`/me/data`) + self-delete (`DELETE /me`); admins cannot self-delete.
- **Weekly digest**: `/admin/digest/run` + hourly Monday scheduler — INERT until GMAIL_APP_PASSWORD is set (send_digest_email ready).
- **Branding/Copy**: logo = elegant white **S** + lime **K.**; "Ask SK" AI widget global (client & admin dashboards); About Me + Ex-EY badge; hero/about credibility (EY Big-4 Advisory, $2B+ debt syndication across Maharashtra authorities, 60+ projects, strategy/supply chain/transformation/financial mgmt/scaling for corporates in India & globally).
- **SEO**: Seo component (canonical/OG/Twitter/JSON-LD), index.html favicons (svg+png+apple-touch) + og-cover.png, sitemap incl. /learning.
- Verified: backend 17/17, frontend 100% on 27 flows (iteration_5.json). Email/SMTP intentionally OFF.

## Iteration 5.1 (Aug 31, 2026) — Ticket Alerts + CRM Notes/Tags
- **Ticket alerts**: `send_ticket_alert_email` fires to BOOKING_ADMIN_EMAIL on every new ticket (fire-and-forget). INERT until GMAIL_APP_PASSWORD is set; ticket creation always succeeds regardless.
- **CRM notes & tags**: `PATCH /admin/clients/{id}` saves private `notes` + `tags`; editor in the client drawer; tags shown as pills in the CRM table. Verified via API + UI.

## Iteration 5.2 (Aug 31, 2026) — Tag Filter + Ticket SLA
- **CRM tag filter**: filter chips (All / per-tag with counts) above the CRM table filter clients by tag client-side. Testids: crm-tag-filters, crm-tag-all, crm-tag-<tag>.
- **Ticket SLA**: SLA thresholds (high 4h / medium 24h / low 72h) on open|in-progress tickets. Breached tickets get a red border + "SLA breached" badge (sla-breach-<id>), sort to top, show time-open; a summary banner (sla-summary) counts breaches. Frontend-only (uses created_at/updated_at). Verified via UI.

## Iteration 5.3 (Aug 31, 2026) — WhatsApp, Ask-SK Lead Bot, Consent Detail, Segments, Auto-Escalate
- **WhatsApp button**: green FAB (bottom-left) → wa.me/917208998944 with prefilled text. testid whatsapp-button.
- **Ask SK lead bot**: greet → capture name + phone (POST /chat/lead → inserted into consultations as source 'ask-sk-chatbot', status new, visible in CRM Leads) → ask what they're exploring → AI answer contextualised to services (existing /ai/chat) → each reply closes with "A member of Sudarshan's team will revert back to you shortly." testids lead-capture/lead-name/lead-phone/lead-start/ai-input.
- **GDPR consent detail**: banner "What we collect" panel lists Strictly necessary (always on) vs Analytics & personalisation (optional); Accept all / Essential only. Tracking gated on 'accepted'.
- **CRM saved segments**: save a tag filter as a one-click view (localStorage sk_crm_segments). testids save-segment/saved-segments/segment-<tag>.
- **Ticket auto-escalate**: backend _auto_escalate_tickets() bumps open|in-progress past SLA (low→medium, medium→high), sets auto_escalated; runs on GET /admin/tickets + hourly scheduler. Badge auto-escalated-<id>. Verified: 2d-old medium → high.

## Iteration 5.4 (Aug 31, 2026) — Lead Source View
- Every consultation now records a `source`: booking-form (create_consultation), consultation-checkout (create_checkout), ask-sk-chatbot (chat bot). WhatsApp is a direct link (no DB record) — mapped for future WA API capture.
- Admin Leads tab: source filter chips (All / per-source with counts, testid lead-source-filters, lead-source-<key>) + colour-coded Source column badge (lead-source-badge-<id>). Verified in UI.

## Iteration 5.5 (Aug 31, 2026) — Source Analytics chart
- Backend GET /admin/lead-analytics?weeks=8 → weekly buckets of lead counts per source + totals.
- Overview tab: recharts stacked bar chart "Lead volume by source" (last 8 weeks) with colour legend + totals. testid lead-source-chart. Verified in UI.

## Iteration 5.6 (Aug 31, 2026) — Date Range, Conversion, Security Audit
- **Date range toggle**: chart period 8 weeks / 3 months (13 weekly) / 12 months (monthly). GET /admin/lead-analytics?period=8w|3m|12m. testids chart-period-toggle, period-<v>.
- **Conversion view**: per-source paid-conversion (paid statuses: paid/won/scheduled) with % bars — testid conversion-view, conversion-<source>.

## Iteration 5.7 (Aug 31, 2026) — Revenue Ranking + CSV Export
- **Conversion by value**: analytics now sums `amount` for paid leads per source; conversion cards ranked by revenue with a "Most valuable channel" highlight (testid top-channel). Fixed projection to include `amount`.
- **Export report**: GET /admin/lead-analytics/export streams a CSV (Source, Total Leads, Paid, Conversion %, Revenue); admin "Export CSV" button (testid export-analytics) downloads it. Verified via API + UI.

## Iteration 5.8 (Aug 31, 2026) — Revenue Trend + Scheduled Report
- **Revenue trend**: analytics returns per-bucket `revenue` alongside `weeks`; chart has a Leads/Revenue metric toggle (testid chart-metric-toggle, metric-volume, metric-revenue) with $-scaled axis/tooltip. Verified.
- **Scheduled report**: POST /admin/report/run emails Sudarshan the analytics CSV (send_report_email, CSV attachment); scheduler sends on the 1st of each month. Admin "Email report" button (testid email-report). INERT until GMAIL_APP_PASSWORD set (returns skipped:email_not_configured; UI shows an informative toast).
- **Security audit** (deployment static scan + manual): PASS. No hardcoded secrets; URLs env-driven; admin routes gated by require_admin; auth (JWT + Google session cookie, HttpOnly/Secure/SameSite=None); admin allowlist strict; hCaptcha strict. Fixed: N+1 in /admin/clients → now MongoDB aggregations (4 queries total).
- Advisories (not fixed): tighten CORS to explicit origin; escape user input in outbound email HTML when SMTP is enabled; consider rate-limit/captcha on public /chat/lead.

## Iteration 5.9 (Jun 2026) — Revenue Goal + Best Package View
- **Revenue Goal card** (Admin Overview): current-month revenue vs a monthly target with progress bar + inline editor. Backend GET /admin/lead-analytics returns `revenue_goal`, `month_revenue`, `month_label`; POST /admin/revenue-goal {target} persists to app_meta (_id revenue_goal). testids revenue-goal-card, edit-revenue-goal, revenue-goal-input, save-revenue-goal, revenue-goal-bar.
- **Best Package card** (Admin Overview): ranked revenue breakdown by consultation package (Discovery/Strategy/Deep Dive/Custom) from `packages` in analytics (sums paid lead `amount` grouped by `package`). testids best-package-card, best-package-list, package-row-N.
- Verified: backend via curl (goal set → 5000, month_revenue 898, packages ranked); frontend via screenshot (both cards render on Overview).

## Iteration 5.10 (Jun 2026) — Revenue Goal pace badge
- Revenue Goal card shows a pace badge: "On track" / "Goal reached" (lime, up-trend) vs "Behind pace" (amber, down-trend), computed client-side from day-of-month vs monthly target (expected = goal × dayOfMonth / daysInMonth). Shows "pace target today $X" when behind. testid revenue-goal-pace. Verified via screenshot.

## Iteration 5.11 (Jun 2026) — hCaptcha gate on Google login
- Google login (both client & admin, /login + /register) is now gated by hCaptcha. The "Continue with Google" button is disabled until the captcha is solved; on click the frontend calls POST /api/auth/captcha-gate {captcha_token} which verifies the captcha and sets a short-lived (10 min) httpOnly `captcha_gate` cookie, then redirects to Emergent Google Auth (redirect URL unchanged).
- POST /api/auth/session now requires the captcha_gate cookie (403 otherwise) and clears it after a successful exchange. Emergent redirect/session-exchange flow untouched.
- Verified via curl (session 403 w/o gate, passes w/ valid gate JWT) + screenshot (Google button disabled until captcha, hint shown).

## Iteration 5.12 (Jun 2026) — Login brute-force protection
- POST /api/auth/login now rate-limits by ip+email: 5 failed attempts trigger a 15-min lockout (login_attempts collection, unique index on identifier). Locked requests return 429 with a friendly "Try again in N minute(s)." message + Retry-After header. Successful login clears the counter. Applies to email/password login (admin + client); captcha still runs first.
- Verified via direct function test: 5 fails → 429 lockout with Retry-After; clear on success releases the lock.

## Iteration 5.13 (Jun 2026) — Login Security visibility (admin)
- GET /api/admin/login-attempts returns recent failed-login records (ip, email, recent/total fails, locked flag + locked_until, last attempt) + locked_now count and policy (max_attempts, lockout_minutes). register_failed_login now stores ip/email + cumulative fail_total.
- Admin Overview: "Login Security" card (testid login-attempts-card) with a "N locked now" / "No active lockouts" badge and a table (login-attempts-table, rows login-attempt-row-N) showing each attacker's email/IP/fails/last-attempt/status (Locked vs Cleared). Verified via curl + screenshot.

## Iteration 5.14 (Jun 2026) — Manual unlock control
- POST /api/admin/login-attempts/unlock {ip, email} deletes the login_attempts record so a genuinely-stuck user can sign in immediately. Admin-only.
- Login Security card: added an Action column with an "Unlock" (locked) / "Clear" button per row (testid unlock-login-N); on click it clears the lockout and refreshes the list with a toast. Verified via curl (cleared:true, list empties) + screenshot (click removed the row → empty state).

## Iteration 5.15 (Jun 2026) — Site-wide attack detection & auto-mitigation
- **SecurityGuard middleware** (backend, all /api traffic): detects & INSTANTLY blocks attacks — (1) malicious signatures in path/query (SQLi, path traversal, /.env, /wp-admin, XSS, etc.), (2) request floods (>100 req/10s per IP), (3) credential stuffing (1 IP failing across 3+ accounts or 15+ total fails, triggered from login). Offending IP is auto-banned (60 min) → all further requests get 403. Uses X-Forwarded-For for the real client IP (critical behind ingress). In-memory ban cache + Mongo persistence (blocked_ips), warmed on startup.
- **Alerts**: every detection writes a security_alerts record (severity high/medium/info) + fires send_security_alert_email to BOOKING_ADMIN_EMAIL (INERT until GMAIL_APP_PASSWORD set). Login lockouts raise a medium alert too.
- **Admin API**: GET /admin/security (active bans + recent alerts + unseen count), POST /admin/security/seen, POST /admin/security/unban {ip} (lifts ban + clears that IP's failed-login records = false-positive control).
- **Admin UI** (Login Security card): toast on load for unseen alerts; "Auto-blocked IPs — attack stopped" list with Unblock buttons (testid blocked-ips, blocked-ip-N, unban-ip-N); "Recent security events" feed with severity dots (testid security-alerts). 
- Verified via curl: SQLi & path-traversal probes → 403 + ban; banned IP blocked everywhere; clean IPs unaffected; unban restores access. Screenshot confirms UI + toast.

## Iteration 5.16 (Jun 2026) — Threat trends chart
- GET /admin/security now returns a 14-day `trend` (per-day counts of high/critical + medium/lockout blocked events). Login Security card renders a small stacked recharts bar chart "Blocked attacks — last 14 days" (testid threat-trend; red=Critical, amber=Lockouts) so admins can see when the site is being probed. Verified via seeded data + screenshot.

## Iteration 5.17 (Jun 2026) — VPN/Proxy block + RSA-style TOTP bypass
- **VPN/Proxy Guard** (admin toggle, OFF by default): SecurityGuard middleware blocks ALL /api (browsing + login) for VPN/proxy/Tor IPs via vpnapi.io (cached 24h in ip_risk_cache; IPQS fallback if IPQS_API_KEY set; fail-open on provider error). Bypass if IP ∈ admin trusted allowlist OR valid `vpn_totp` cookie. /api/vpn/* exempt so the gate works.
- **TOTP trusted-token bypass** (pyotp, RSA SecurID-style): admin provisions named 6-digit rotating codes (QR + manual key, shown once) from the VPN Guard card; visitor enters code on a full-screen VpnGate (POST /api/vpn/verify) → signed 12h httpOnly `vpn_totp` cookie.
- **Admin UI** (Overview → VPN/Proxy Guard card): master toggle, trusted-IP allowlist editor, token create/list/remove + QR. **Frontend** VpnGate.jsx overlay gates the whole site when /api/vpn/status returns blocked.
- Keys: VPNAPI_KEY in .env (IPQS empty). Verified via curl: guard on → flagged VPN IP (45.83.91.1) blocked on content + login (403 vpn_block); clean IP 8.8.8.8 allowed; allowlist bypass 200; TOTP verify sets cookie (wrong code 401); toggle off restores. Admin UI + QR + gate verified via screenshot. Guard left OFF; test data cleaned.

## Iteration 5.18 (Jun 2026) — Country blocking + IPQS fallback + Phase 1 hardening
- **Country blocking**: hard geo-block independent of the VPN toggle. app_meta blocked_countries (ISO codes). SecurityGuard blocks any /api request from a blocked country (403 country_block) unless IP allowlisted; /api/vpn/* exempt. /api/vpn/status reports reason:"country"; VpnGate shows a "Region not available" message (no TOTP option). Admin: POST /admin/security/block-country|unblock-country; blocked_countries returned in /admin/security. Top Offenders rows now have a "Block <CC>" button + blocked-country chips with remove. Verified via curl (AU→1.1.1.1 blocked, US→8.8.8.8 allowed, unblock restores).
- **IPQS fallback**: detect_vpn now treats a vpnapi.io response lacking `security` (quota/error) as failure → falls back to IPQualityScore when IPQS_API_KEY is set (currently empty). vpnapi remains primary.
- **Phase 1 hardening**: (1) audit_log collection + audit() helper wired into sensitive admin actions (ban/unban IP & range, block/unblock country, VPN toggle); GET /admin/audit-log; "Admin audit trail" card on Overview. (2) Request-body size cap (>2MB → 413) in SecurityGuard. (3) Security headers already present (nosniff, X-Frame SAMEORIGIN, Referrer-Policy, Permissions-Policy, HSTS). Verified via curl (audit entries logged; 413 on oversized body; normal 200).
- NOTE: DB access is API-only (frontend never touches Mongo). Mongo least-privilege = infra (MONGO_URL protected), not changed.

## PENDING — Phase 2 (Super-Admin vault + MFA), agreed with user
- Reuse admin allowlist as super-admin. MFA layers: TOTP + WebAuthn passkey (device Face ID/Windows Hello); email OTP deferred (SMTP inert).
- Master vault of integration API keys (Stripe, vpnapi, LLM, etc.), revealed ONLY after passing all MFA layers. Encrypt secrets at rest (Fernet, add ENCRYPTION_KEY to .env).

## Iteration 5.19 (Jun 2026) — Hero background coaching video
- Added a subtle, semi-transparent (opacity 0.14) autoplay/muted/loop background coaching b-roll to the Hero section for a premium "in motion" feel; Sudarshan's photo card kept unchanged. Dark gradient overlay keeps copy readable.
- Sources self-hosted in /app/frontend/public: hero-coaching.webm (VP9, 4.5MB) + hero-coaching.mp4 (H.264, 12MB) [free-license Mixkit clip 4809]; poster = existing COACH image. Same-origin (served by frontend) to avoid Mixkit hotlink protection. testid hero-bg-video. Verified playing via screenshot (readyState 4). NOTE: automation Chromium lacks H.264, so WebM source is what makes it verifiable there; real browsers use either. Placeholder to be swapped for Sudarshan's own clip later.

## Iteration 5.20 (Jun 2026) — Super-Admin Vault + MFA + Audit retention
- **Vault** (admin "Vault" tab): Fernet-encrypted store of integration API keys. Two-factor unlock — TOTP authenticator code (step 1 → short-lived vault_totp cookie) + WebAuthn passkey (step 2 → 5-min vault_unlock cookie). Reuses admin allowlist as super-admin. Secrets encrypted at rest (ENCRYPTION_KEY); GET/POST/DELETE /admin/vault/keys require unlock. Reveal/hide + delete in UI. VaultPanel.jsx + lib/webauthn.js. WEBAUTHN_RP_ID/ORIGIN in .env (preview domain).
- **WebAuthn** endpoints: /admin/vault/enroll/totp(+/verify), /unlock/totp, /webauthn/register/options(+/verify), /webauthn/auth/options(+/verify), /vault/lock, /vault/status. py_webauthn 2.2.0, platform authenticator, user-verification required. Ceremony challenges stored in webauthn_ceremonies (5-min exp).
- **Audit retention**: audit_log entries now carry expire_at (BSON Date) + TTL index (auto-purge). POST /admin/audit-retention {days} (1–3650, default 90) re-bases existing entries; persisted in app_meta; loaded on startup.
- Verified: TOTP enroll/verify/unlock (curl); vault CRUD encrypted-at-rest (curl, plaintext absent in DB); FULL passkey flow end-to-end via Playwright CDP virtual authenticator (screenshot: enroll→register passkey→unlock→"Unlocked" + secrets panel); retention set to 30/90 (curl). Test MFA data cleared afterward.
- NOTE: IPQS fallback still needs the user's IPQualityScore key (IPQS_API_KEY empty). Email OTP deferred (SMTP inert).

## Iteration 5.21 (Jun 2026) — Vault auto-lock countdown
- vault_status now returns unlock_seconds_left (decoded from the vault_unlock JWT exp). VaultPanel shows a live "auto-locks in M:SS" countdown in the Unlocked badge (testid vault-countdown); at 0 it auto-locks the UI and refetches status. Verified via CDP full-flow screenshot (4:57 → 4:54 ticking).

## Iteration 5.22 (Jun 2026) — Vault access log line
- vault_status returns last_unlock (most recent audit_log "vault_unlocked": actor, ip, at). VaultPanel shows "Last unlocked {time} by {actor} · {ip}" (testid vault-last-unlock) so admins spot unexpected access. Verified via CDP screenshot.

## Iteration 5.23 (Jun 2026) — Failed vault-unlock alerts
- Wrong authenticator code OR rejected passkey at the vault now raises a high-severity security alert (type vault_unlock_failed, with email+IP) → shows in Login Security "Recent security events" feed + unseen toast + inert email; also audit-logged (vault_totp_fail / vault_passkey_fail). Verified via curl (wrong code → 401 + alert unseen=1).

## Iteration 5.24 (Jun 2026) — Login/Footer access + LinkedIn + brute-force IP fix verified
- **Admin login entry point**: added a labelled "Admin Login" link in the Navbar (desktop + mobile) and a new "Account" column in the Footer with Client Login, Admin Login and Create Account. Both logins point to the single secure /login page (admins auto-route to /admin by role). No security/bypass change — admins still solve hCaptcha and are recognised via ADMIN_ALLOWLIST. testids: nav-admin-login, mobile-admin-login, footer-client-login, footer-admin-login.
- **LinkedIn**: footer LinkedIn icon now links to https://www.linkedin.com/in/karweers (testid footer-linkedin).
- **Admin allowlist confirmed**: ADMIN_ALLOWLIST = exactly sudarshan@karweers.com, sudarshan.karweer@gmail.com; startup demotes any other admin to client.
- **Brute-force real-client-IP fix VERIFIED** (backend testing agent, 7/7 pass, iteration_6.json): login lockout identifier + register_failed_login now key on the real client IP via _client_ip(request) (X-Forwarded-For → X-Real-IP → socket peer), not the ingress proxy IP. Two IPs behind the same proxy stay isolated (no collateral lockout); lockout at 5 fails → 429 + Retry-After; clear releases lock.
- **Consistency fix**: verify_captcha now receives _client_ip(request) in /auth/register, /auth/captcha-gate, /consultations, /newsletter, /checkout (was request.client.host) for correct real-IP attribution. Backend health 200; no functional change to captcha verification.

## Iteration 5.25 (Jun 2026) — Stripe REMOVED + free booking-request flow + availability calendar
- **Stripe fully removed**: deleted emergentintegrations Stripe import, PACKAGES-Stripe checkout, /payments/checkout, /payments/status, /webhook/stripe, payment_transactions usage, the payment-gated /bookings/schedule, and the /payment/success & /payment/cancel pages/routes (files deleted).
- **Consultation → free booking request**: 3 package tiers stay visible with INDICATIVE pricing ("from $X" + "final fee shared on confirmation"). Button "Request this session" → POST /consultation/book creates a lead in CRM with status "pending_confirmation" (no payment). General enquiry (no package) still POSTs /consultations.
- **Availability calendar** (backend): Mon–Fri, 09:30–19:00, 30-min start slots. Package duration (30/60/90) blocks the covered range (occupied[]) so no overlaps. app_meta _id "availability" holds published_week_start (Monday) + blocked{date:[times]}. Endpoints: GET /consultation/availability (public, one published week, future/non-blocked/non-booked slots), GET /admin/availability?week_start (grid w/ available/blocked/booked state), POST /admin/availability/toggle, /block-day, /publish. Auto-rolls to next week every Saturday via _digest_scheduler.
- **Bookings queue** (admin): GET /admin/bookings; POST /admin/bookings/{id}/confirm|decline|reschedule. Confirm/reschedule triggers send_booking_email (INERT until GMAIL_APP_PASSWORD set → returns 'skipped'). Decline frees the slot.
- **Admin UI**: new "bookings" + "availability" tabs in AdminDashboard (week grid w/ prev/next, Publish/Published badge, block-day, click-to-block slots; bookings table w/ Confirm/Reschedule/Decline). Consultation.jsx rewritten with package pick → date/time picker.
- Verified: backend 18/18 (iteration_7.json, incl. slot-conflict for 60/90-min, publish, confirm/decline/reschedule, admin auth), frontend public + admin panels render (all testids). Test data cleaned.
- NOTE: Legal pages (Terms/Refund) still reference paid consultations — content not updated (optional follow-up). STRIPE_API_KEY still present in backend/.env but unused.

## Iteration 5.26 (Jun 2026) — Legal refresh + Vault Lockout + Google Calendar sync
- **Legal refresh**: Terms rewritten (Bookings & confirmation — free request + personal confirmation, indicative pricing, no payment); Refund page repurposed to "Booking & Cancellation Policy" (no refunds/Stripe); Privacy "Data we collect" + "How we use it" no longer mention Stripe/card/payments. Footer link relabelled "Booking & Cancellation" (route /refund unchanged). Verified via screenshot (no 'Stripe' anywhere).
- **Vault Lockout** (anti-brute-force on MFA): 5 failed vault-unlock attempts (wrong TOTP OR rejected passkey) freeze unlocking for 15 min (vault_lockouts collection). check_vault_lockout raises 429 + Retry-After; register_vault_fail freezes + raises a high security alert + audit; clear_vault_fails releases on successful unlock. Wired into /admin/vault/unlock/totp, /webauthn/auth/options, /webauthn/auth/verify. vault_status returns lock_frozen/lock_seconds_left/fails/max_fails. VaultPanel shows a red "frozen — try again in M:SS" countdown + "N attempts left" hint, disabling unlock while frozen. Verified via direct-function test (test_vault_lockout.py) + HTTP.
- **Google Calendar sync** (admin's own calendar): admin connects once via OAuth (GOOGLE_CALENDAR_CLIENT_ID/SECRET/REDIRECT_URI in .env). On booking Confirm → event created (client as attendee, Asia/Kolkata tz); Reschedule → event updated; Decline → event deleted. gcal_event_id stored on the booking. Tokens (access+refresh) Fernet-encrypted in app_meta _id 'google_calendar'; auto-refresh on expiry. Endpoints: GET /admin/calendar/status, GET /admin/calendar/oauth/start (returns Google consent URL, state=signed JWT), GET /admin/calendar/oauth/callback (verifies state ∈ allowlist, stores tokens, redirects /admin?calendar=connected|error), POST /admin/calendar/disconnect. All sync calls run in executor + wrapped so bookings never fail if calendar errors/not connected. Admin UI: "Connect Google Calendar" card in the Bookings tab. Verified endpoints via curl (minted JWT) + admin UI screenshot; full OAuth consent is a one-time manual step by the owner.
- **Deps added**: google-auth, google-auth-oauthlib, google-api-python-client, google-auth-httplib2 (requirements.txt).
- Verified: iteration_8.json — backend 13/13 + vault lockout, frontend 100%; test data cleaned.
- NOTE: GOOGLE_CALENDAR_REDIRECT_URI is set to the PREVIEW domain callback; on production deploy, register the prod callback in Google Cloud and update this env var. OAuth consent screen is in Testing mode with the owner as a Test user (fine for their own calendar).

## Iteration 5.27 (Jun 2026) — New-booking alert + client reminders + buffer times
- **New-booking alert**: the moment a visitor books, `send_new_booking_alert_email` fires to BOOKING_ADMIN_EMAIL (or ADMIN_EMAIL) with client + package + requested slot + "pending confirmation" + a Review link (fire-and-forget via BackgroundTasks). INERT until GMAIL_APP_PASSWORD set (returns 'skipped'); booking always succeeds. NOTE: WhatsApp ping NOT built (needs Twilio/WhatsApp Business API + credentials).
- **Client reminders**: hourly scheduler pass `_send_session_reminders()` (guarded by GMAIL_APP_PASSWORD) emails confirmed clients ~24h before their session (23–25h window in Asia/Kolkata), marks reminder_sent to avoid duplicates; reschedule resets reminder_sent. `send_session_reminder_email` in emailer.py. INERT until SMTP configured.
- **Buffer times**: admin sets a gap (0/15/30/45/60 min) between sessions from the Availability tab (POST /admin/availability/buffer; buffer_minutes in app_meta availability, default 0). `_booked_slots_for(dates, buffer_min)` expands each active booking's blocked range by the buffer on both sides so public + admin availability and the booking-conflict check all respect it. admin_availability returns buffer_minutes; UI select in Availability tab (testid buffer-control/buffer-select).
- Verified: direct-function tests (test_buffer_reminders.py — buffer 0/30/60 blocking, alert inert, reminder window selects ~24h only) + HTTP (buffer set/persist/reset, admin availability buffer_minutes) + UI screenshot (buffer control renders). Test data cleaned; buffer reset to 0.

## Iteration 5.28 (Jun 2026) — Meeting link on confirm + configurable reminder timing
- **Meeting link on confirm/reschedule**: BookingActionIn gains meeting_link. Confirm/Reschedule store it on the booking; it flows into the Google Calendar event (location + "Join:" in description), the confirmation email body, and the .ics invite (LOCATION + URL). Admin UI: Confirm now opens an inline "Meeting/video link (optional)" field (confirm-form/confirm-link) before confirming; Reschedule form also has a link field; the stored link shows as a "🔗 Meeting link" in the booking row (booking-link-<id>).
- **Configurable reminder timing**: reminder_leads in app_meta availability (default [24]). POST /admin/availability/reminders {leads:[2|24]}; admin_availability returns reminder_leads. Admin UI select in Availability tab (reminder-control/reminder-select): "1 day before" / "2 hours before" / "Both (1 day + 2 hours)" / "Off". Scheduler `_send_session_reminders` now fires per-lead (23–25h window for 24h, 1–3h for 2h), tracks reminders_sent[] to avoid duplicates, migrates legacy reminder_sent flag, uses friendly labels ("tomorrow" / "in about 2 hours") and includes the meeting link. INERT until GMAIL_APP_PASSWORD.
- Verified: test_buffer_reminders.py (updated for reminders_sent[]) + HTTP (confirm stores link, ICS contains LOCATION+URL, reminders 'both'→[2,24]) + UI screenshot (confirm-link field reveals, reminder-select + buffer-select render). Test data cleaned.

## Iteration 5.29 (Jun 2026) — Auto Google Meet links + "next 24–48h" agenda strip
- **Auto Meet links**: when confirming/rescheduling a booking with NO manual link and Google Calendar is connected, `_event_body(booking, want_meet=True)` attaches a conferenceData createRequest (hangoutsMeet) and the insert/update uses conferenceDataVersion=1. The generated Meet URL is extracted (hangoutLink / entryPoints) via `_extract_meet_link` and persisted back onto the booking's meeting_link (helper `_apply_calendar_sync`), so the confirmation email, .ics invite, reminders, agenda and booking row all use it. Calendar sync now runs BEFORE the email is scheduled so the email carries the auto link. Safe no-op when calendar not connected (verified: confirm w/o connection → meeting_link None, no error). Full auto-generation activates after the one-time admin Calendar connect.
- **Today agenda strip**: Bookings tab now shows a "Next 24–48 hours" strip (today-agenda) of upcoming CONFIRMED sessions, computed client-side from bookings using IST (`${slot_date}T${slot_time}:00+05:30`), sorted ascending, each card showing IST date/time (Asia/Kolkata), client, package and a Join link when a meeting link exists; empty state "No confirmed sessions in the next 48 hours." (agenda-empty).
- Verified: HTTP (confirm w/o calendar = safe no-op) + UI screenshot (agenda strip renders session card + Join, booking row shows Confirmed + meeting link). Test data cleaned. NOTE: auto-Meet generation itself requires a live Google Calendar connection to fully exercise.

## Iteration 5.30 (Jun 2026) — Calendar health check + agenda on Overview
- **Calendar health check**: GET /admin/calendar/status now proactively validates the connection — `_gcal_build_service_sync` force-refreshes the access token when expired/unknown (our stored creds carry no expiry), so a revoked/expired refresh token raises RefreshError → `_gcal_mark_unhealthy` sets needs_reconnect + last_error; a successful validation (calendars().get primary) calls `_gcal_mark_healthy`. sync_booking_to_calendar also flags unhealthy on RefreshError. Status returns `healthy`. Admin UI: the Google Calendar card turns amber with "⚠ Reconnect needed — Google access expired, so syncing is paused" + a Reconnect button (calendar-unhealthy / calendar-reconnect). Verified via HTTP (seeded bogus refresh token → healthy=false; cleaned up).
- **Agenda on Overview**: the "Next 24–48 hours" strip was extracted into `renderAgenda()` and now renders at the TOP of the Overview tab (first thing on login) in addition to the Bookings tab. Verified via UI screenshot (Overview shows the upcoming confirmed-session card + Join above the stat cards). Test data cleaned.

## Iteration 5.31 (Jun 2026) — Bookings badge + weekly agenda email
- **Bookings tab badge**: a "N in 48h" pill on the Bookings tab button shows the count of confirmed sessions in the next 48h (computed client-side, IST), so upcoming sessions are visible before opening the tab. testid bookings-badge. Verified via UI screenshot ("2 in 48h").
- **Weekly agenda email**: `_send_weekly_agenda()` emails the advisor (BOOKING_ADMIN_EMAIL/ADMIN_EMAIL) every Monday ~08:00 IST a table of the coming week's (today..+7d) confirmed sessions (date/time IST, client, package, Join link). Scheduler-guarded by GMAIL_APP_PASSWORD + last_weekly_agenda (once per Monday). `send_weekly_agenda_email` in emailer.py. INERT until SMTP configured. Verified via direct call (runs cleanly, email returns 'skipped'). Test data cleaned.

## Iteration 5.32 (Jun 2026) — Reconnect toast + client self-service cancel/reschedule
- **Reconnect toast**: AdminDashboard shows a one-time `toast.warning` on load when Google Calendar is connected but unhealthy (needs reconnect), so the amber card warning is never missed (calWarnedRef guards repeats).
- **Client self-service (cancel / request reschedule)**: signed booking-manage JWT (`_booking_token`, 60-day exp, purpose booking_manage) embedded as a "Manage your booking" link in the confirmation email. Public endpoints (no auth): GET /booking/manage?token (returns booking details), POST /booking/cancel (status→cancelled, frees slot, deletes calendar event, emails admin an inert note), POST /booking/reschedule-request (sets reschedule_requested + reschedule_note, emails admin). New public page /booking/manage (BookingManage.jsx) with Cancel + Request-reschedule (note) actions and success states. Admin bookings table now shows a red "cancelled" badge and an amber "↻ Reschedule requested" flag (with note tooltip). Invalid/expired token → 400.
- Verified: HTTP (manage GET, reschedule-request sets flag+note, cancel→cancelled, bad token→400) + UI screenshots (manage page renders with actions; reconnect-toast logic + badge/flag in admin table). Test data cleaned.

## Iteration 5.33 (Jun 2026) — Cancellation window + waitlist
- **Cancellation window**: admin sets a "no online cancellations within N hours" cutoff (0/12/24/48, default 24) in the Availability tab (POST /admin/availability/cancel-window; cancel_cutoff_hours in availability meta). GET /booking/manage returns can_cancel + cancel_cutoff_hours; the client manage page hides Cancel within the window and shows a "contact us / request reschedule" note (reschedule still allowed). POST /booking/cancel enforces the cutoff server-side (400 within window). Verified via HTTP (can_cancel=false + 400 within 24h; window 0 → cancel succeeds).
- **Waitlist**: public GET /consultation/availability now returns full_days (future weekdays in the published week with zero available slots). Consultation.jsx shows a "Fully booked days — join the waitlist" chip picker + "Notify me" (uses the form's name/email + captcha) → POST /consultation/waitlist (waitlist collection; dedupes per email+date). When a confirmed slot is cancelled, `_notify_waitlist(date)` emails everyone waitlisted for that day (send_waitlist_opening_email) and marks them notified — INERT-safe (stays unnotified while SMTP off, no error). Admin: GET /admin/waitlist. Verified via HTTP (block day → full_days includes it; notify inert-safe).

## Iteration 5.34 (Jun 2026) — Dynamic homepage content engine ("Market Signals") + no-AI wording
- **Daily homepage engine** (Claude Sonnet 4.6 via emergentintegrations / Emergent LLM key): `_generate_home_content()` produces a hero headline (with one *asterisk*-emphasised word), hero subtext, 3 short insight blurbs, and a 5-item feed ({title, take, tag}). Strictly guardrailed to verified facts (Ex-EY Big 4, $2B+ debt syndication, 23Y+/60+ projects, RE/BESS/hydrogen/climate-finance, MSRTC monetisation) — HOME_FACTS/HOME_FALLBACK. Cached in app_meta._id "home_content"; `_refresh_home_content(force)` self-guards on 24h staleness (HOME_REFRESH_HOURS) with an asyncio lock; warmed on startup + refreshed hourly-but-only-if-stale in `_digest_scheduler`. Endpoints: GET /api/home/content (public; serves cache instantly, kicks a background refresh if stale), POST /api/admin/home/regenerate (admin, force). Safe fallback keeps last-known-good if generation fails.
- **Frontend**: Home.jsx fetches /home/content once and passes to Hero (dynamic headline/subtext + "Today's takes" blurbs; falls back to static copy) and to a NEW standalone section AIInsights.jsx (renders as "Market Signals", 5 cards with tag chips + a "Refreshed daily · updated {date}" badge). Admin Overview has an "Homepage Content" card + "Regenerate now" button (regenerate-home).
- **No "AI" wording anywhere on the site** (user request): renamed "AI Insights"→"Market Signals", "AI-curated"→"Refreshed daily", removed "Karweer AI"/"AI Content Engine"/"Create + AI"/"AI draft" etc. Learning topic label "AI & Its Impact"→"Machine Intelligence" (VideoCard badge "Machine Intel"); chatbot identity in AI_SYSTEM →'Ask SK' advisory assistant. Verified via grep (no standalone visible "AI") + screenshot.
- Testids retained: ai-insights, ai-insights-updated, ai-insight-0..4, hero-headline, hero-insights, hero-insight-0..2, ai-home-card, regenerate-home (kept for stability; not user-visible).

## Iteration 5.35 (Jun 2026) — Mandatory Terms & Privacy consent on all auth + Consent Log
- **Strict consent gate** (ConsentGate.jsx) on /login and /register (email/password + Google): the "I agree" checkbox (consent-checkbox) stays DISABLED until BOTH the Terms & Conditions and Privacy Policy are opened in a new tab (consent-open-terms / consent-open-privacy → /terms, /privacy). Only then can the user tick and submit; Sign in / Create account / Google buttons are disabled until agreed. Hint (consent-hint) shown until both opened.
- **Backend enforcement**: RegisterIn/LoginIn/CaptchaGateIn gain `consent: bool`. POST /api/auth/register, /api/auth/login and /api/auth/captcha-gate reject with 400 when consent is false/omitted (captcha is verified first). Google flow: the captcha_gate JWT now carries a `consent` claim (read_captcha_gate); /api/auth/session requires it (400 otherwise). `record_consent()` writes to `consent_logs` (id, user_id, email, name, action=login|register|google, agreed, terms_version, privacy_version, ip, user_agent, created_at) and stamps `consent` on the user doc. CONSENT_POLICY_VERSION env-overridable (default 2026-06-01). Indexes on consent_logs (created_at, email).
- **Super-admin Consent Log**: Admin Dashboard "Consent Log" tab (admin-tab-consent → admin-consent) lists every agreement (when/name/email/method/agreed/version/IP) + "Export CSV" (export-consent) via GET /api/admin/consent-logs and /export (admin-only).
- Verified: iteration_9.json — backend 14/14 (test_iteration9.py); frontend UI (consent gate disable/enable logic, homepage Market Signals, regenerate button, Consent Log tab + CSV). Testing agent fixed one JSX wrapper regression in AdminDashboard (Consent Log block). hCaptcha strict → full real login not exercised headless (token bypass used).

## Iteration 5.36 (Jun 2026) — Consent receipt email + Market Signals archive
- **Consent receipt email**: `send_consent_receipt_email` (emailer.py) sends the user a copy of what they agreed to (policy version + date + method + Terms/Privacy links), BCC'd to BOOKING_ADMIN_EMAIL/ADMIN_EMAIL for the compliance trail. Fired fire-and-forget from `record_consent` on every login/register/google. INERT-safe until GMAIL_APP_PASSWORD is set (returns 'skipped', never blocks auth).
- **Market Signals archive**: every successful daily generation is snapshotted into `signals_archive` (one doc per calendar date: date, hero_headline, hero_subtext, insights, feed, generated_at; unique index on date). Startup backfills today's entry from the current cache. Public endpoints GET /api/signals/archive?limit (newest first, max 90) and GET /api/signals/archive/{date}. New page /signals (SignalsArchivePage.jsx) lists past daily reads (date header + blurbs + feed cards); "Browse past signals →" link (signals-archive-link) added to the Market Signals section footer. Route added in App.js.
- Verified: curl (archive lists today with 5 feed items; /{date} 200 for existing, 404 for missing) + screenshot (/signals renders "Market Signals · Archive" with the dated entry). Backend logs clean. Email Activation still pending the owner's 16-char Gmail App Password (all email — bookings, reminders, alerts, consent receipt — activates the moment it's set).

## Iteration 5.37 (Jun 2026) — Email ACTIVATED + Signals-on-this-day + Weekly Signals Digest + Consent Withdrawal
- **Email LIVE**: GMAIL_APP_PASSWORD set in backend/.env for GMAIL_USER=sudarshan@karweers.com (Google Workspace). Verified: SMTP starttls login OK + a real consent-receipt test email delivered ('sent'). All previously-inert email now sends: booking confirmations, new-booking alerts, session reminders, weekly agenda, monthly report, security alerts, waitlist openings, consent receipts, and the new weekly signals digest.
- **Signals on this day / shareable**: new route /signals/:date (SignalsArchivePage handles single-day mode via useParams) backed by GET /api/signals/archive/{date}. Single-day view shows that day's blurbs + feed, a "Copy share link" button (signals-share) and an "On this day" date picker (signals-date-jump) to jump to any date. The full archive list now gives each day a permalink (signals-permalink-<date>) + "Share" copy button (signals-copy-<date>). Missing dates show a friendly not-found (signals-notfound). Verified via screenshot + curl (404 for missing).
- **Weekly Signals Digest**: `_send_signals_digest()` gathers the last 7 days of signals_archive, de-dupes the best ~6 feed items (`_collect_top_signal_items`), and emails every newsletter subscriber (send_signals_digest_email). Scheduler sends once weekly on Friday ~09:00 IST (last_signals_digest guard). Admin manual trigger POST /api/admin/signals-digest/run (returns skipped:email_not_configured when off; now live).
- **Consent withdrawal + record export** (client dashboard "Your data & privacy" → new "Terms & Privacy consent" block): GET /api/me/consent (own status + full history), POST /api/me/consent/withdraw (logs a 'withdraw' consent_logs entry, agreed=false; sets user.consent.agreed=false; clears sk_consent so tracking stops; user re-agrees at next sign-in). UI: consent-status, download-consent (JSON), withdraw-consent. All endpoints require auth (verified 401 unauth).
- NOTE: client-dashboard consent UI compiles and mirrors the existing GDPR block; full logged-in visual pass is captcha-gated (owner to sanity-check). Backend fully self-tested via curl; live email confirmed by a delivered test message.

## Iteration 5.38 (Jun 2026) — Digest unsubscribe + shareable signals previews + consent renewal prompt
- **One-click unsubscribe**: signed JWT token (`_unsub_token`, purpose=unsubscribe) → public GET /api/newsletter/unsubscribe?token=... deletes the subscriber and returns a branded HTML confirmation ("You're unsubscribed" / "Link expired" for bad tokens). Weekly signals digest email now includes a footer "Unsubscribe" link (`_unsub_url`) + List-Unsubscribe / List-Unsubscribe-Post one-click headers for inbox compliance. Verified: valid token deletes + confirms; garbage token → expired.
- **Shareable signals previews**: SignalsArchivePage Seo now sets per-page og:title/og:description/og:image/og:type + canonical (twitter card = summary_large_image). Branded share image at /og-signals.png (generated, dark + lime "MARKET SIGNALS"). Single-day type=article. NOTE: tags are set client-side (SPA) — link unfurlers that execute JS + in-app shares get the rich preview; non-JS crawlers (some WhatsApp/LinkedIn cases) fall back to the branded default image + site title. Full per-date crawler unfurls would need SSR/prerender (not in this stack).
- **Consent renewal prompt**: GET /api/me/consent now returns `needs_renewal` (true when consent missing/withdrawn or version != CONSENT_POLICY_VERSION). New POST /api/me/consent/renew records a 're-agree' (action="renew"). Frontend ConsentRenewalPrompt.jsx is a modal (reuses ConsentGate strict open-both-docs → tick → I agree) shown on the client dashboard whenever needs_renewal; "Remind me later" dismisses for the session. Verified via minted client token + screenshot: modal renders with the correct policy version; consent panel (download/withdraw) renders in "Your data & privacy".
- All new endpoints auth-guarded (401 unauth verified). Test artefacts cleaned up.

## Iteration 5.39 (Jun 2026) — Resubscribe + policy version control + per-day social cards
- **Resubscribe flow**: `_resub_token` (purpose=resubscribe) + public GET /api/newsletter/resubscribe?token=... re-adds the subscriber with a branded confirmation. The unsubscribe confirmation page now shows a "Resubscribe with one click" button carrying a resubscribe token. Shared `_mail_page()` + `_decode_email()` helpers. Verified round-trip.
- **Policy version control**: CONSENT_POLICY_VERSION is now a runtime-mutable module global, seeded from env and overridden from app_meta._id "policy" on startup. Admin GET /api/admin/policy-version (version + users_on_current/users_total) and POST /api/admin/policy-version {version} (persists + reassigns global + audit log). Bumping it makes every user's needs_renewal=true (version mismatch) → they get the renewal prompt on next visit. Admin UI: "Policy version control" card in the Consent Log tab (policy-version-card / -input / -save). Verified via screenshot (0 of 6 users on 2026-06-01).
- **Per-day social cards**: Pillow-rendered branded OG image at GET /api/signals/og/{date}.png (dark bg + lime glow, "SK." monogram, "MARKET SIGNALS" eyebrow, that day's top feed headline wrapped, date + site URL). Fonts bundled at backend/assets/fonts (Vera/VeraBd.ttf). In-memory cache per date, Cache-Control 24h. SignalsArchivePage single-day Seo now points og:image at this endpoint (list page keeps the static og-signals.png). Verified: 200 image/png 80KB, headline renders correctly.
- **Deliverability (item 1 — DNS, owner action, NOT code)**: for karweers.com (Google Workspace) add — SPF TXT @ : `v=spf1 include:_spf.google.com ~all`; DKIM: enable in Google Admin → Apps → Gmail → Authenticate email (2048-bit), publish the given `google._domainkey` TXT; DMARC TXT @ _dmarc: `v=DMARC1; p=none; rua=mailto:dmarc@karweers.com; adkim=s; aspf=s` (tighten to p=quarantine→reject once clean).

## Iteration 5.40 (Jun 2026) — Admin email/share tooling: test email, version history, card accent picker, digest preview
- **Deliverability test tool**: POST /api/admin/email/test {to} → emailer.send_test_email (skips if email off). Admin Overview "Email & deliverability" card: input + "Send test" (fire a message to yourself/mail-tester to validate SPF/DKIM/DMARC once DNS is live).
- **Policy version history**: each bump appends {version, at, by} to app_meta.policy.history; GET /admin/policy-version now returns reversed history (max 50). Admin Consent Log tab shows a "Version history" list (policy-history) under the policy card.
- **Signals card accent picker**: app_meta.card_style.accent (hex). GET/POST /admin/card-style (validates hex; clears _og_cache on change). The OG renderer (_render_signal_card) now takes an accent RGB (from _card_accent/_hex_to_rgb) applied to the glow, monogram dot, eyebrow and URL. Admin Overview "Signals share card" card: 6 preset swatches + native colour picker + live preview <img> (accent-<hex>, accent-picker, card-preview). Verified end-to-end: switching to cyan re-rendered the live preview; reset to brand lime #C6F135.
- **Weekly digest preview**: emailer refactored — render_signals_digest_html() shared by the sender and GET /admin/signals-digest/preview (HTMLResponse, no send). Admin Overview "Weekly signals digest": "Preview" (opens rendered HTML in a new tab via blob) + "Send now" (existing broadcast). Verified preview renders the real items.
- IMPORTANT frontend gotcha fixed: img src must use `${API}/signals/...` (API already includes /api) — not `${API}/api/...`.
- Item "Deliverability Test" (SPF/DKIM/DMARC pass) still requires the owner to add DNS records (see Iteration 5.39) then run a mail-tester; the app-side test-send tool is now provided.
