import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Globe, Sparkles, Loader2, TrendingUp } from "lucide-react";
import api from "@/lib/api";

const PRIORITY = {
  P0: { cls: "bg-red-500/15 text-red-500 border-red-500/30", label: "P0 · Critical" },
  P1: { cls: "bg-amber-500/15 text-amber-500 border-amber-500/30", label: "P1 · High" },
  P2: { cls: "bg-sky-500/15 text-sky-500 border-sky-500/30", label: "P2 · Nice to have" },
};

const CATEGORY_COLORS = {
  "Conversion & Lead Gen": "text-emerald-500",
  "Content & Thought Leadership": "text-violet-500",
  "UX & Design": "text-pink-500",
  "Trust & Credibility": "text-sky-500",
  "SEO & Discoverability": "text-amber-500",
  "Performance": "text-orange-500",
  "Monetization": "text-[hsl(var(--primary))]",
  "Community & Engagement": "text-teal-500",
};

export const BenchmarkAdmin = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchOnce = () => api.get("/admin/benchmark").then((r) => r.data).catch(() => null);

  useEffect(() => {
    let timer;
    const poll = async () => {
      const d = await fetchOnce();
      if (d) setData(d);
      if (d?.status === "running") {
        setLoading(true);
        timer = setTimeout(poll, 4000);
      } else {
        setLoading(false);
      }
    };
    poll();
    return () => clearTimeout(timer);
  }, []);

  const generate = async () => {
    setLoading(true);
    try {
      await api.post("/admin/benchmark/generate");
      toast.success("Analysis started — this takes up to a minute.");
      // Poll until done.
      const poll = async () => {
        const d = await fetchOnce();
        if (d) setData(d);
        if (d?.status === "running") {
          setTimeout(poll, 4000);
        } else {
          setLoading(false);
          if (d?.status === "error") toast.error("AI analysis failed — please try again.");
          else if (d?.recommendations?.length) toast.success("Benchmark analysis updated");
        }
      };
      setTimeout(poll, 4000);
    } catch (e) {
      setLoading(false);
      toast.error(e?.response?.data?.detail || "Could not start analysis. Try again.");
    }
  };

  const recs = data?.recommendations || [];
  const counts = { P0: 0, P1: 0, P2: 0 };
  recs.forEach((r) => { counts[r.priority] = (counts[r.priority] || 0) + 1; });

  return (
    <div data-testid="benchmark-panel">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="flex items-center gap-2 font-display text-2xl font-bold">
            <Globe className="h-5 w-5 text-[hsl(var(--primary))]" /> Global Best-Practices Benchmark
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">AI-compared against world-class advisory, coaching & thought-leadership sites (McKinsey, a16z, HBR, Naval, Simon Sinek…).</p>
          {data?.generated_at && <p className="mt-1 text-xs text-muted-foreground">Last analysed {new Date(data.generated_at).toLocaleString()}</p>}
        </div>
        <button onClick={generate} disabled={loading} data-testid="benchmark-generate"
          className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--accent))] px-5 py-3 text-sm font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
          {loading ? <><Loader2 className="h-4 w-4 animate-spin" /> Analysing…</> : <><Sparkles className="h-4 w-4" /> {recs.length ? "Refresh analysis" : "Run analysis"}</>}
        </button>
      </div>

      {data?.summary && (
        <div className="mt-6 rounded-2xl border border-border bg-card p-6" data-testid="benchmark-summary">
          <p className="text-sm leading-relaxed text-foreground">{data.summary}</p>
          <div className="mt-4 flex flex-wrap gap-2">
            {["P0", "P1", "P2"].map((p) => counts[p] > 0 && (
              <span key={p} className={`rounded-full border px-3 py-1 text-xs font-semibold ${PRIORITY[p].cls}`}>{counts[p]} × {PRIORITY[p].label}</span>
            ))}
          </div>
        </div>
      )}

      {!recs.length && !loading && (
        <div className="mt-6 rounded-2xl border border-dashed border-border bg-card p-12 text-center" data-testid="benchmark-empty">
          <TrendingUp className="mx-auto h-10 w-10 text-muted-foreground" />
          <p className="mt-3 font-semibold">No analysis yet</p>
          <p className="mt-1 text-sm text-muted-foreground">Run the analysis to see prioritised improvements benchmarked against the best sites globally.</p>
        </div>
      )}

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {recs.map((r, i) => (
          <div key={i} className="rounded-2xl border border-border bg-card p-5" data-testid={`benchmark-rec-${i}`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className={`text-xs font-semibold ${CATEGORY_COLORS[r.category] || "text-muted-foreground"}`}>{r.category}</p>
                <h4 className="mt-1 font-display text-base font-bold">{r.title}</h4>
              </div>
              <span className={`shrink-0 rounded-full border px-2.5 py-1 text-[11px] font-bold ${PRIORITY[r.priority]?.cls || PRIORITY.P2.cls}`}>{r.priority}</span>
            </div>
            <p className="mt-2 text-sm text-foreground">{r.recommendation}</p>
            {r.benchmark && <p className="mt-2 text-xs text-muted-foreground"><span className="font-semibold text-foreground">Benchmark:</span> {r.benchmark}</p>}
            {r.impact && <p className="mt-1 text-xs text-muted-foreground"><span className="font-semibold text-foreground">Impact:</span> {r.impact}</p>}
          </div>
        ))}
      </div>
    </div>
  );
};

export default BenchmarkAdmin;
