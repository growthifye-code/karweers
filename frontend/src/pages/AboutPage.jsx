import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowUpRight, Quote } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import EYBadge from "@/components/EYBadge";
import { SECTORS } from "@/components/sections/Sectors";
import { SK_PORTRAITS } from "@/lib/assets";

const JOURNEY = [
  { year: "EY · Big 4", title: "Management Consultant, EY Advisory", text: "Began at the sharpest end of consulting as a Management Consultant with Ernst & Young (EY) Advisory — learning how strategy, capital and execution connect inside large, complex organisations, and delivering for leading corporates in India and globally." },
  { year: "Corporate & Public", title: "Consulting, Fintech & Fundraising", text: "Led public-sector consulting, fintech and large-scale fundraising initiatives — including debt syndication programmes exceeding $2B across key development authorities in Maharashtra, and asset-monetisation mandates." },
  { year: "Energy Transition", title: "RE, Storage & Hydrogen", text: "Moved to the frontier of the energy transition — advising on renewables, battery storage (BESS) and green hydrogen from feasibility through to financial close and green & climate financing." },
  { year: "Today", title: "Coach & Advisor", text: "Works 1:1 with founders and CXOs across strategy, supply chain & cost optimisation, business & digital transformation, financial management and scaling — turning founder-led hustle into system-led, bankable businesses." },
];

const PHILOSOPHY = [
  { t: "Decisions, not decks", d: "Every engagement is anchored to a real decision and a metric — never abstract advice." },
  { t: "Bankability by design", d: "Recommendations are built to survive both an engineer's and a lender's scrutiny." },
  { t: "Candour over comfort", d: "You get the honest read you can't get from inside your own organisation." },
];

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="About Sudarshan Karweer — Business Coach & Advisor"
        description="The story, philosophy and track record of Sudarshan Karweer — 23Y+ business coach and strategic advisor across the energy transition."
        jsonLd={{ "@context": "https://schema.org", "@type": "Person", name: "Sudarshan Karweer", jobTitle: "Business Coach & Strategic Advisor", email: "sudarshan@karweers.com" }} />
      <Navbar />

      <section className="grain relative overflow-hidden pt-40 lg:pt-48">
        <div className="pointer-events-none absolute -right-40 top-24 h-[28rem] w-[28rem] rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-6 pb-16 lg:grid-cols-[1.05fr_0.95fr] lg:px-10">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">About Me</p>
              <EYBadge />
            </div>
            <h1 className="mt-4 font-display text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
              I help founders build businesses that <span className="text-[hsl(var(--primary))]">last</span>.
            </h1>
            <p className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg">
              For over 23 years I've sat at the intersection of engineering, capital and leadership — starting as a
              Management Consultant with <span className="font-semibold text-foreground">EY (Ernst &amp; Young, Big 4)</span> Advisory,
              then leading debt syndication programmes exceeding <span className="font-semibold text-foreground">$2B</span> across key
              development authorities in Maharashtra. My work spans strategy, supply chain &amp; cost optimisation, business &amp; digital
              transformation, financial management, business scaling and the energy transition — for leading corporates in India and globally.
            </p>
            <div className="mt-8 flex flex-wrap gap-4">
              <Link to="/#consult" className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-7 py-3.5 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-1">Work with me <ArrowUpRight className="h-5 w-5" /></Link>
              <Link to="/services" className="inline-flex items-center gap-2 rounded-full border border-border px-7 py-3.5 font-semibold transition-colors hover:bg-secondary">See services</Link>
            </div>
          </div>
          <div className="relative">
            <div className="overflow-hidden rounded-[2rem] border border-border">
              <div className="aspect-[4/5] overflow-hidden">
                <img src={SK_PORTRAITS.advisory} alt="Sudarshan Karweer" data-testid="about-portrait" className="h-full w-full object-cover object-top" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-border py-24">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">The journey</h2>
          <div className="mt-12 space-y-8">
            {JOURNEY.map((j, i) => (
              <motion.div key={j.title} initial={{ opacity: 0, x: -16 }} whileInView={{ opacity: 1, x: 0 }} viewport={{ once: true }} transition={{ duration: 0.5, delay: i * 0.05 }}
                className="grid gap-4 border-l-2 border-[hsl(var(--primary))] pl-6 sm:grid-cols-[160px_1fr]">
                <p className="text-sm font-semibold uppercase tracking-wide text-[hsl(var(--primary))]">{j.year}</p>
                <div><h3 className="font-display text-xl font-bold">{j.title}</h3><p className="mt-2 text-muted-foreground">{j.text}</p></div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-border bg-card py-24">
        <div className="mx-auto max-w-6xl px-6">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">How I think</h2>
          <div className="mt-10 grid gap-5 md:grid-cols-3">
            {PHILOSOPHY.map((p, i) => (
              <motion.div key={p.t} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5, delay: i * 0.06 }}
                className="rounded-2xl border border-border bg-background p-7">
                <Quote className="h-6 w-6 text-[hsl(var(--primary))]" />
                <h3 className="mt-4 font-display text-lg font-bold">{p.t}</h3>
                <p className="mt-2 text-sm text-muted-foreground">{p.d}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-border py-24">
        <div className="mx-auto max-w-5xl px-6">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">Sectors I've worked across</h2>
          <p className="mt-3 max-w-2xl text-muted-foreground">From heavy industry to high-growth start-ups — a breadth that compounds into sharper, cross-pollinated advice.</p>
          <div className="mt-8 flex flex-wrap gap-2">
            {SECTORS.map((s) => (
              <span key={s} className="inline-flex items-center rounded-full border border-border bg-card px-4 py-2 text-sm font-medium">
                <span className="mr-2 h-1.5 w-1.5 rounded-full bg-[hsl(var(--primary))]" />{s}
              </span>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
