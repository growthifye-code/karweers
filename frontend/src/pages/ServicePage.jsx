import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowUpRight, ArrowLeft, Check, Target, Trophy } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";
import { SK_PORTRAITS } from "@/lib/assets";

export default function ServicePage() {
  const { slug, phase } = useParams();
  const [svc, setSvc] = useState(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
    setSvc(null); setNotFound(false);
    api.get(`/services/${slug}`).then((r) => setSvc(r.data)).catch(() => setNotFound(true));
    import("@/lib/api").then((m) => m.track("service", slug));
  }, [slug]);

  if (notFound) return (
    <div className="min-h-screen bg-background text-foreground"><Navbar />
      <div className="mx-auto max-w-3xl px-6 py-40 text-center"><h1 className="font-display text-3xl font-bold">Service not found</h1><Link to="/services" className="mt-6 inline-block text-[hsl(var(--primary))]">← All services</Link></div><Footer /></div>
  );
  if (!svc) return <div className="min-h-screen grid place-items-center bg-background text-foreground animate-pulse font-display text-2xl">Loading…</div>;

  const isConsult = svc.slug === "premium-consultation";
  const heroImg = isConsult ? (SK_PORTRAITS[svc.portrait] || SK_PORTRAITS.advisory) : svc.hero_image;
  const currentPhase = phase ? svc.workflow.find((w) => w.key === phase) : null;

  // Phase detail view
  if (phase) {
    if (!currentPhase) return (
      <div className="min-h-screen bg-background text-foreground"><Navbar />
        <div className="mx-auto max-w-3xl px-6 py-40 text-center"><h1 className="font-display text-3xl font-bold">Phase not found</h1><Link to={`/services/${slug}`} className="mt-6 inline-block text-[hsl(var(--primary))]">← Back to service</Link></div><Footer /></div>
    );
    const idx = svc.workflow.findIndex((w) => w.key === phase);
    return (
      <div className="min-h-screen bg-background text-left text-foreground">
        <Seo title={`${currentPhase.title} — ${svc.title}`} description={currentPhase.summary} />
        <Navbar />
        <div className="mx-auto max-w-3xl px-6 pt-40 lg:pt-48" data-testid="phase-detail">
          <Link to={`/services/${slug}`} className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="h-4 w-4" /> {svc.title}</Link>
          <p className="mt-6 text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Phase 0{idx + 1}</p>
          <h1 className="mt-3 font-display text-4xl font-black tracking-tight sm:text-5xl">{currentPhase.title}</h1>
          <p className="mt-4 text-lg text-muted-foreground">{currentPhase.summary}</p>
          <p className="mt-8 text-base leading-relaxed text-muted-foreground">{currentPhase.detail}</p>
          <h3 className="mt-10 font-display text-xl font-bold">What happens in this phase</h3>
          <ul className="mt-4 space-y-3">
            {currentPhase.steps.map((s) => (<li key={s} className="flex items-start gap-3 rounded-xl border border-border bg-card p-4"><Check className="mt-0.5 h-5 w-5 flex-shrink-0 text-[hsl(var(--primary))]" /><span>{s}</span></li>))}
          </ul>
          <div className="mt-10 flex flex-wrap gap-3">
            {idx > 0 && <Link to={`/services/${slug}/${svc.workflow[idx - 1].key}`} className="rounded-full border border-border px-5 py-2.5 text-sm font-semibold hover:bg-secondary">← {svc.workflow[idx - 1].title}</Link>}
            {idx < svc.workflow.length - 1 && <Link to={`/services/${slug}/${svc.workflow[idx + 1].key}`} className="rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))]">{svc.workflow[idx + 1].title} →</Link>}
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  // Service overview view
  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title={`${svc.title} — Sudarshan Karweer`} description={svc.tagline + " " + svc.overview.slice(0, 120)}
        jsonLd={{ "@context": "https://schema.org", "@type": "Service", name: svc.title, description: svc.overview, provider: { "@type": "Person", name: "Sudarshan Karweer" } }} />
      <Navbar />

      <section className="grain relative overflow-hidden pt-40 lg:pt-48">
        <div className="pointer-events-none absolute -right-40 top-24 h-[26rem] w-[26rem] rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-6 pb-16 lg:grid-cols-[1.1fr_0.9fr] lg:px-10">
          <div>
            <Link to="/services" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="h-4 w-4" /> All services</Link>
            <h1 className="mt-5 font-display text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl">{svc.title}</h1>
            <p className="mt-4 text-lg font-medium text-[hsl(var(--primary))]">{svc.tagline}</p>
            <p className="mt-5 max-w-xl leading-relaxed text-muted-foreground">{svc.overview}</p>
            <a href="/#consult" className="mt-8 inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-7 py-3.5 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-1">Book this engagement <ArrowUpRight className="h-5 w-5" /></a>
          </div>
          <div className="relative overflow-hidden rounded-[2rem] border border-border">
            <div className="aspect-[4/5] overflow-hidden"><img src={heroImg} alt={svc.title} className={`h-full w-full object-cover ${isConsult ? "object-top" : "object-center"}`} /></div>
          </div>
        </div>
      </section>

      <section className="border-t border-border py-24">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <h2 className="font-display text-3xl font-bold tracking-tight sm:text-4xl">The workflow</h2>
          <p className="mt-3 max-w-2xl text-muted-foreground">A clear, sequenced engagement. Click any phase for the detailed approach.</p>
          <div className="mt-12 grid gap-5 md:grid-cols-2 lg:grid-cols-4">
            {svc.workflow.map((w, i) => (
              <motion.div key={w.key} initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.45, delay: i * 0.06 }}>
                <Link to={`/services/${slug}/${w.key}`} data-testid={`phase-${w.key}`} className="group flex h-full flex-col rounded-2xl border border-border bg-card p-6 transition-transform hover:-translate-y-1">
                  <span className="font-display text-3xl font-black text-[hsl(var(--primary))]">0{i + 1}</span>
                  <h3 className="mt-3 font-display text-lg font-bold group-hover:text-[hsl(var(--primary))]">{w.title}</h3>
                  <p className="mt-2 flex-1 text-sm text-muted-foreground">{w.summary}</p>
                  <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-[hsl(var(--primary))]">Detail <ArrowUpRight className="h-4 w-4" /></span>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-border bg-card py-24">
        <div className="mx-auto grid max-w-7xl gap-12 px-6 md:grid-cols-2 lg:px-10">
          <div>
            <div className="flex items-center gap-3"><Target className="h-6 w-6 text-[hsl(var(--primary))]" /><h2 className="font-display text-2xl font-bold">The approach</h2></div>
            <ul className="mt-6 space-y-4">{svc.approach.map((a) => (<li key={a} className="flex items-start gap-3"><Check className="mt-1 h-5 w-5 flex-shrink-0 text-[hsl(var(--primary))]" /><span className="text-muted-foreground">{a}</span></li>))}</ul>
          </div>
          <div>
            <div className="flex items-center gap-3"><Trophy className="h-6 w-6 text-[hsl(var(--accent))]" /><h2 className="font-display text-2xl font-bold">Key outcomes</h2></div>
            <ul className="mt-6 space-y-4">{svc.outcomes.map((o) => (<li key={o} className="flex items-start gap-3 rounded-xl border border-border bg-background p-4"><Trophy className="mt-0.5 h-5 w-5 flex-shrink-0 text-[hsl(var(--accent))]" /><span>{o}</span></li>))}</ul>
          </div>
        </div>
      </section>

      <section className="border-t border-border py-20 text-center">
        <div className="mx-auto max-w-2xl px-6">
          <h2 className="font-display text-3xl font-bold">Ready to begin?</h2>
          <p className="mt-3 text-muted-foreground">Book a premium 1:1 consultation and let's map your next move.</p>
          <a href="/#consult" className="mt-6 inline-flex items-center gap-2 rounded-full bg-[hsl(var(--accent))] px-7 py-3.5 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-1">Book Consultation <ArrowUpRight className="h-5 w-5" /></a>
        </div>
      </section>
      <Footer />
    </div>
  );
}
