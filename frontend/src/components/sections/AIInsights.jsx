import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { Sparkles, TrendingUp, ArrowUpRight } from "lucide-react";

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
    return new Date(iso).toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
  } catch {
    return "";
  }
}

export default function AIInsights({ content }) {
  const feed = content?.feed || [];
  if (!feed.length) return null;

  return (
    <section id="ai-insights" className="scroll-mt-24 border-t border-border bg-background py-24 lg:py-32" data-testid="ai-insights">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="max-w-2xl">
            <p className="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">
              <Sparkles className="h-4 w-4" /> Market Signals
            </p>
            <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">
              Today's read on the energy transition & capital.
            </h2>
          </div>
          <span data-testid="ai-insights-updated"
            className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-1.5 text-xs font-medium text-muted-foreground">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[hsl(var(--primary))] opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-[hsl(var(--primary))]" />
            </span>
            Refreshed daily · updated {formatDate(content?.generated_at)}
          </span>
        </div>

        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {feed.map((f, i) => (
            <motion.article
              key={i}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-60px" }}
              transition={{ duration: 0.5, delay: i * 0.06 }}
              data-testid={`ai-insight-${i}`}
              className="group flex flex-col rounded-3xl border border-border bg-card p-7 transition-colors hover:border-[hsl(var(--primary))]/50">
              <span className={`inline-flex w-fit items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-semibold uppercase tracking-wide ${TAG_STYLES[f.tag] || "border-border text-muted-foreground"}`}>
                <TrendingUp className="h-3 w-3" /> {f.tag}
              </span>
              <h3 className="mt-5 font-display text-xl font-bold leading-snug">{f.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{f.take}</p>
            </motion.article>
          ))}
        </div>

        <p className="mt-8 flex flex-wrap items-center justify-between gap-3 text-xs text-muted-foreground">
          <span>Refreshed daily and grounded in Sudarshan's advisory expertise. For decision-grade advice, book a 1:1 consultation.</span>
          <Link to="/signals" data-testid="signals-archive-link" className="inline-flex shrink-0 items-center gap-1 rounded-full border border-border px-4 py-2 text-xs font-semibold text-foreground transition-colors hover:bg-secondary">
            Browse past signals <ArrowUpRight className="h-3.5 w-3.5" />
          </Link>
        </p>
      </div>
    </section>
  );
}
