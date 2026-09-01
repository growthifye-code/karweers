import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Quote, TrendingUp, ArrowUpRight } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";

export default function CaseStudiesPage() {
  const [items, setItems] = useState([]);
  const [testimonials, setTestimonials] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/case-studies").then((r) => setItems(r.data)).catch(() => {}),
      api.get("/testimonials").then((r) => setTestimonials(r.data)).catch(() => {}),
    ]).finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Case Studies & Testimonials — Sudarshan Karweer" description="Proof-point case studies and client testimonials across renewable energy, manufacturing, capital and government asset monetisation." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-40 lg:pt-48">
        <div className="pointer-events-none absolute -right-40 top-20 h-96 w-96 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Proof of Delivery</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-extrabold tracking-tight sm:text-5xl">Outcomes, not adjectives.</h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">A selection of engagements — from bankable renewable pipelines to surgical cost transformations — with the results that mattered.</p>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 pb-16 lg:px-10">
        {loading ? (
          <p className="py-16 text-center text-muted-foreground">Loading…</p>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2" data-testid="case-studies-grid">
            {items.map((c) => (
              <div key={c.slug} data-testid={`case-${c.slug}`} className="flex flex-col rounded-3xl border border-border bg-card p-7">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-[hsl(var(--primary))]">
                  <span>{c.sector}</span><span className="text-muted-foreground">·</span><span className="text-muted-foreground normal-case">{c.client}</span>
                </div>
                <h3 className="mt-3 font-display text-2xl font-bold leading-tight">{c.headline}</h3>
                <div className="mt-4 space-y-3 text-sm leading-relaxed text-muted-foreground">
                  {c.challenge && <p><span className="font-semibold text-foreground">Challenge · </span>{c.challenge}</p>}
                  {c.approach && <p><span className="font-semibold text-foreground">Approach · </span>{c.approach}</p>}
                  {c.result && <p><span className="font-semibold text-foreground">Result · </span>{c.result}</p>}
                </div>
                {Array.isArray(c.metrics) && c.metrics.length > 0 && (
                  <div className="mt-6 grid grid-cols-2 gap-3">
                    {c.metrics.map((m, i) => (
                      <div key={i} className="rounded-2xl bg-secondary p-4">
                        <p className="flex items-center gap-1.5 font-display text-xl font-extrabold text-[hsl(var(--primary))]"><TrendingUp className="h-4 w-4" /> {m.value}</p>
                        <p className="mt-1 text-xs text-muted-foreground">{m.label}</p>
                      </div>
                    ))}
                  </div>
                )}
                {c.quote && <p className="mt-6 border-l-2 border-[hsl(var(--primary))] pl-4 text-sm italic text-foreground">“{c.quote}”</p>}
              </div>
            ))}
          </div>
        )}
      </div>

      {testimonials.length > 0 && (
        <section className="border-t border-border bg-secondary/30 py-20" data-testid="testimonials-section">
          <div className="mx-auto max-w-7xl px-6 lg:px-10">
            <h2 className="font-display text-3xl font-bold tracking-tight">In their words.</h2>
            <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {testimonials.map((t) => (
                <figure key={t.id} data-testid={`testimonial-${t.id}`} className="flex flex-col rounded-3xl border border-border bg-card p-7">
                  <Quote className="h-7 w-7 text-[hsl(var(--primary))]" />
                  <blockquote className="mt-4 flex-1 text-sm leading-relaxed text-foreground">“{t.quote}”</blockquote>
                  <figcaption className="mt-5 border-t border-border pt-4">
                    <p className="text-sm font-bold">{t.name}</p>
                    <p className="text-xs text-muted-foreground">{[t.role, t.company].filter(Boolean).join(" · ")}</p>
                  </figcaption>
                </figure>
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="py-20">
        <div className="mx-auto max-w-3xl px-6 text-center">
          <h2 className="font-display text-3xl font-bold tracking-tight">Want an outcome like these?</h2>
          <p className="mt-4 text-muted-foreground">Start with a 1:1 session, or bring Sudarshan into your organisation.</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <a href="/#consult" className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">Book a consultation <ArrowUpRight className="h-4 w-4" /></a>
            <Link to="/corporate" className="inline-flex items-center gap-1.5 rounded-full border border-border px-6 py-3 text-sm font-semibold hover:bg-secondary">Enterprise enquiry</Link>
          </div>
        </div>
      </section>
      <Footer />
    </div>
  );
}
