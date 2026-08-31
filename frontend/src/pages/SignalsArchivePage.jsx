import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { TrendingUp, ArrowLeft } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";

const TAG_STYLES = {
  "Energy Transition": "border-[hsl(var(--primary))]/40 text-[hsl(var(--primary))]",
  "Climate Finance": "border-emerald-400/40 text-emerald-400",
  "Storage": "border-sky-400/40 text-sky-400",
  "Green Hydrogen": "border-teal-400/40 text-teal-400",
  "Strategy": "border-[hsl(var(--accent))]/50 text-[hsl(var(--accent))]",
  "Macro": "border-amber-400/40 text-amber-400",
};

function formatDate(iso) {
  if (!iso) return "";
  try {
    return new Date(iso).toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long", year: "numeric" });
  } catch {
    return iso;
  }
}

export default function SignalsArchivePage() {
  const [signals, setSignals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/signals/archive", { params: { limit: 60 } })
      .then((r) => setSignals(r.data.signals || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Market Signals — Archive | Sudarshan Karweer"
        description="Browse past daily Market Signals: sharp, timely reads on the energy transition, storage, green hydrogen, climate finance and strategy." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-32 lg:pt-40" data-testid="signals-archive">
        <div className="pointer-events-none absolute -right-32 top-10 h-80 w-80 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[120px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 lg:px-10">
          <Link to="/" data-testid="signals-back" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> Back to home
          </Link>
          <p className="mt-6 text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Market Signals · Archive</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-black tracking-tight sm:text-5xl">
            Every day's read, in one place.
          </h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">
            A running record of the daily takes on the energy transition, capital and strategy — refreshed each day and kept here so you can catch up on anything you missed.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 pb-24 lg:px-10">
        {loading && <p className="text-muted-foreground" data-testid="signals-loading">Loading the archive…</p>}
        {!loading && signals.length === 0 && (
          <p className="rounded-2xl border border-border bg-card p-8 text-center text-muted-foreground" data-testid="signals-empty">
            The archive is filling up — check back tomorrow for the first entries.
          </p>
        )}
        <div className="space-y-16">
          {signals.map((s) => (
            <article key={s.date} data-testid={`signals-day-${s.date}`} className="border-t border-border pt-10 first:border-t-0 first:pt-0">
              <div className="flex flex-wrap items-baseline justify-between gap-3">
                <h2 className="font-display text-2xl font-bold">{formatDate(s.generated_at || s.date)}</h2>
                <span className="text-xs font-medium uppercase tracking-widest text-muted-foreground">{s.date}</span>
              </div>
              {s.insights?.length > 0 && (
                <ul className="mt-5 space-y-2 border-l-2 border-[hsl(var(--primary))]/40 pl-5">
                  {s.insights.map((t, i) => (
                    <li key={i} className="text-sm leading-relaxed text-muted-foreground">{t}</li>
                  ))}
                </ul>
              )}
              <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {(s.feed || []).map((f, i) => (
                  <div key={i} className="flex flex-col rounded-3xl border border-border bg-card p-7">
                    <span className={`inline-flex w-fit items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-wide ${TAG_STYLES[f.tag] || "border-border text-muted-foreground"}`}>
                      <TrendingUp className="h-3 w-3" /> {f.tag}
                    </span>
                    <h3 className="mt-5 font-display text-xl font-bold leading-snug">{f.title}</h3>
                    <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{f.take}</p>
                  </div>
                ))}
              </div>
            </article>
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}
