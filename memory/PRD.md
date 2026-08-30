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
