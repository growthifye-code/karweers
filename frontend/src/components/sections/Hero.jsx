import { motion } from "framer-motion";
import { ArrowUpRight, Sparkles } from "lucide-react";
import EYBadge from "@/components/EYBadge";

const COACH = "https://static.prod-images.emergentagent.com/jobs/69d54eb7-07e1-4ffd-ad08-8725f9f9829e/images/5b2f94a6fd021cc779249c997e2a7e9f42370d01aeb0897c98fa6f1010e0dcce.jpeg";
const BG_VIDEO = "/hero-coaching.mp4";

// Renders a headline where *asterisk-wrapped* text is highlighted in the brand accent.
function Headline({ text }) {
  const parts = text.split(/(\*[^*]+\*)/g).filter(Boolean);
  return (
    <>
      {parts.map((p, i) =>
        p.startsWith("*") && p.endsWith("*")
          ? <span key={i} className="text-[hsl(var(--primary))]">{p.slice(1, -1)}</span>
          : <span key={i}>{p}</span>
      )}
    </>
  );
}

const DEFAULT_HEADLINE = "Turning complexity into your *competitive advantage*.";
const DEFAULT_SUBTEXT = "I'm Sudarshan Karweer — a business coach and strategic advisor, and a former EY (Big 4) management consultant. Across 60+ projects with leading corporates in India and globally, I help founders and CXOs win at strategy, transformation, financial management, fundraising and scaling — including renewable energy, BESS, green hydrogen and climate finance.";

export default function Hero({ content }) {
  const headline = content?.hero_headline || DEFAULT_HEADLINE;
  const subtext = content?.hero_subtext || DEFAULT_SUBTEXT;
  return (
    <section className="grain relative overflow-hidden bg-background pt-40 lg:pt-48" data-testid="hero">
      <video autoPlay muted loop playsInline preload="auto" poster={COACH} aria-hidden="true"
        className="pointer-events-none absolute inset-0 h-full w-full object-cover opacity-[0.14]"
        data-testid="hero-bg-video">
        <source src="/hero-coaching.webm" type="video/webm" />
        <source src={BG_VIDEO} type="video/mp4" />
      </video>
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-b from-background/70 via-background/90 to-background" />
      <div className="pointer-events-none absolute -right-40 top-24 h-[30rem] w-[30rem] rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
      <div className="pointer-events-none absolute -left-40 bottom-0 h-96 w-96 rounded-full bg-[hsl(var(--accent))] opacity-10 blur-[120px]" />
      <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-6 pb-24 lg:grid-cols-[1.1fr_0.9fr] lg:px-10">
        <div>
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
            className="flex flex-wrap items-center gap-3">
            <span className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-1.5 text-xs font-medium text-muted-foreground">
              <Sparkles className="h-3.5 w-3.5 text-[hsl(var(--primary))]" />
              23Y+ · 60+ Projects · $2B+ Syndicated · CXOs
            </span>
            <EYBadge />
          </motion.div>
          <motion.h1 key={headline} initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.1 }}
            data-testid="hero-headline"
            className="mt-6 font-display text-4xl font-extrabold leading-[1.02] tracking-tight sm:text-5xl lg:text-[4.2rem]">
            <Headline text={headline} />
          </motion.h1>
          <motion.p key={subtext} initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.2 }}
            data-testid="hero-subtext"
            className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
            {subtext}
          </motion.p>
          <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.3 }}
            className="mt-9 flex flex-wrap items-center gap-4">
            <a href="#consult" data-testid="hero-consult-cta" className="group inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-7 py-3.5 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-1">
              Book a Premium 1:1 Consultation
              <ArrowUpRight className="h-5 w-5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
            <a href="/services" data-testid="hero-services-cta" className="inline-flex items-center gap-2 rounded-full border border-border px-7 py-3.5 font-semibold text-foreground transition-colors hover:bg-secondary">
              Explore Services
            </a>
          </motion.div>

          {content?.insights?.length > 0 && (
            <motion.ul initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.4 }}
              data-testid="hero-insights" className="mt-10 space-y-2.5 border-l-2 border-[hsl(var(--primary))]/40 pl-5">
              <li className="text-[11px] font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Today's takes</li>
              {content.insights.map((t, i) => (
                <li key={i} data-testid={`hero-insight-${i}`} className="text-sm leading-relaxed text-muted-foreground">
                  {t}
                </li>
              ))}
            </motion.ul>
          )}
        </div>

        <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8, delay: 0.2 }} className="relative">
          <div className="relative overflow-hidden rounded-[2rem] border border-border bg-[hsl(var(--primary))]/10">
            <div className="aspect-[4/5] overflow-hidden">
              <img src={COACH} alt="Sudarshan Karweer coaching a leadership team" data-testid="hero-video" className="kenburns h-full w-full object-cover" />
            </div>
            <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/20 to-transparent" />
            <div className="absolute right-5 top-5 inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-3 py-1.5 text-xs font-bold text-[hsl(var(--primary-foreground))]">
              <span className="relative flex h-2 w-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-current opacity-60" /><span className="relative inline-flex h-2 w-2 rounded-full bg-current" /></span>
              Coaching, in motion
            </div>
            <div className="absolute bottom-5 left-5 right-5">
              <p className="font-logo text-2xl font-bold text-white">Sudarshan Karweer</p>
              <p className="text-sm text-white/80">Coaching CXOs & senior leadership</p>
            </div>
          </div>
          <div className="absolute -left-6 -top-6 hidden rounded-2xl border border-border bg-card p-5 shadow-xl sm:block">
            <p className="font-display text-3xl font-extrabold text-[hsl(var(--primary))]">12+</p>
            <p className="text-xs text-muted-foreground">Sectors Covered</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
