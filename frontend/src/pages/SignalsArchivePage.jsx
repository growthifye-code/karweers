import { useEffect, useState } from "react";
import { Link, useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { TrendingUp, ArrowLeft, Link2, CalendarDays } from "lucide-react";
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

function copyLink(date) {
  const url = `${window.location.origin}/signals/${date}`;
  navigator.clipboard?.writeText(url).then(
    () => toast.success("Link copied — share this day's signals."),
    () => toast.error("Could not copy the link.")
  );
}

function FeedCards({ feed = [] }) {
  return (
    <div className="mt-8 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {feed.map((f, i) => (
        <div key={i} className="flex flex-col rounded-3xl border border-border bg-card p-7">
          <span className={`inline-flex w-fit items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-wide ${TAG_STYLES[f.tag] || "border-border text-muted-foreground"}`}>
            <TrendingUp className="h-3 w-3" /> {f.tag}
          </span>
          <h3 className="mt-5 font-display text-xl font-bold leading-snug">{f.title}</h3>
          <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{f.take}</p>
        </div>
      ))}
    </div>
  );
}

function Blurbs({ insights = [] }) {
  if (!insights.length) return null;
  return (
    <ul className="mt-5 space-y-2 border-l-2 border-[hsl(var(--primary))]/40 pl-5">
      {insights.map((t, i) => <li key={i} className="text-sm leading-relaxed text-muted-foreground">{t}</li>)}
    </ul>
  );
}

export default function SignalsArchivePage() {
  const { date } = useParams();
  const navigate = useNavigate();
  const [signals, setSignals] = useState([]);
  const [single, setSingle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    setLoading(true); setNotFound(false); setSingle(null);
    if (date) {
      api.get(`/signals/archive/${date}`)
        .then((r) => setSingle(r.data))
        .catch(() => setNotFound(true))
        .finally(() => setLoading(false));
    } else {
      api.get("/signals/archive", { params: { limit: 60 } })
        .then((r) => setSignals(r.data.signals || []))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [date]);

  const jumpTo = (v) => { if (v) navigate(`/signals/${v}`); };

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo
        title={date ? `Market Signals — ${formatDate(single?.generated_at || date)} | Sudarshan Karweer` : "Market Signals — Archive | Sudarshan Karweer"}
        description={date
          ? (single?.insights?.[0] || "A daily read on the energy transition, capital and strategy from Sudarshan Karweer.")
          : "Browse past daily Market Signals: sharp, timely reads on the energy transition, storage, green hydrogen, climate finance and strategy."}
        image="https://www.sudarshankarweer.com/og-signals.png"
        type={date ? "article" : "website"}
        path={date ? `/signals/${date}` : "/signals"} />
      <Navbar />
      <section className="grain relative overflow-hidden pt-32 lg:pt-40" data-testid="signals-archive">
        <div className="pointer-events-none absolute -right-32 top-10 h-80 w-80 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[120px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 lg:px-10">
          <Link to={date ? "/signals" : "/"} data-testid="signals-back" className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground">
            <ArrowLeft className="h-4 w-4" /> {date ? "Back to full archive" : "Back to home"}
          </Link>
          <p className="mt-6 text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Market Signals · Archive</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-black tracking-tight sm:text-5xl">
            {date ? formatDate(single?.generated_at || date) : "Every day's read, in one place."}
          </h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">
            {date
              ? "A single day's take on the energy transition, capital and strategy. Share it with the link below."
              : "A running record of the daily takes on the energy transition, capital and strategy — refreshed each day and kept here so you can catch up on anything you missed."}
          </p>
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <label className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-sm text-muted-foreground">
              <CalendarDays className="h-4 w-4 text-[hsl(var(--primary))]" /> On this day
              <input type="date" data-testid="signals-date-jump" defaultValue={date || ""} max={new Date().toISOString().slice(0, 10)}
                onChange={(e) => jumpTo(e.target.value)}
                className="bg-transparent text-foreground outline-none" />
            </label>
            {date && (
              <button onClick={() => copyLink(date)} data-testid="signals-share"
                className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                <Link2 className="h-4 w-4" /> Copy share link
              </button>
            )}
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 pb-24 lg:px-10">
        {loading && <p className="text-muted-foreground" data-testid="signals-loading">Loading…</p>}

        {/* Single-day view */}
        {!loading && date && notFound && (
          <p className="rounded-2xl border border-border bg-card p-8 text-center text-muted-foreground" data-testid="signals-notfound">
            No Market Signals were published on {date}. <Link to="/signals" className="font-semibold text-[hsl(var(--primary))]">Browse the full archive →</Link>
          </p>
        )}
        {!loading && date && single && (
          <article data-testid={`signals-day-${single.date}`}>
            <Blurbs insights={single.insights} />
            <FeedCards feed={single.feed} />
          </article>
        )}

        {/* Full archive list */}
        {!loading && !date && signals.length === 0 && (
          <p className="rounded-2xl border border-border bg-card p-8 text-center text-muted-foreground" data-testid="signals-empty">
            The archive is filling up — check back tomorrow for the first entries.
          </p>
        )}
        {!loading && !date && (
          <div className="space-y-16">
            {signals.map((s) => (
              <article key={s.date} data-testid={`signals-day-${s.date}`} className="border-t border-border pt-10 first:border-t-0 first:pt-0">
                <div className="flex flex-wrap items-baseline justify-between gap-3">
                  <Link to={`/signals/${s.date}`} data-testid={`signals-permalink-${s.date}`} className="font-display text-2xl font-bold transition-colors hover:text-[hsl(var(--primary))]">
                    {formatDate(s.generated_at || s.date)}
                  </Link>
                  <button onClick={() => copyLink(s.date)} data-testid={`signals-copy-${s.date}`}
                    className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
                    <Link2 className="h-3.5 w-3.5" /> Share
                  </button>
                </div>
                <Blurbs insights={s.insights} />
                <FeedCards feed={s.feed} />
              </article>
            ))}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
