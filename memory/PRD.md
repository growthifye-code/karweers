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
