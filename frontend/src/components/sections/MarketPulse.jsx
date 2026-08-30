import { useEffect, useState } from "react";
import { TrendingUp, TrendingDown } from "lucide-react";
import api from "@/lib/api";

export default function MarketPulse({ pulse = [] }) {
  const [live, setLive] = useState([]);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    let timer;
    const fetchLive = () => {
      api.get("/market/live")
        .then((r) => {
          if (r.data?.data?.length) { setLive(r.data.data); setIsLive(true); }
        })
        .catch(() => {});
    };
    fetchLive();
    timer = setInterval(fetchLive, 120000);
    return () => clearInterval(timer);
  }, []);

  const data = live.length ? live : pulse;
  const ticker = [...data, ...data];

  return (
    <section id="market" className="scroll-mt-24 py-24 lg:py-32" data-testid="market">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="max-w-2xl">
            <div className="flex items-center gap-3">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Market Pulse</p>
              {isLive && (
                <span className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))]/15 px-2.5 py-1 text-xs font-semibold text-[hsl(var(--primary))]" data-testid="live-badge">
                  <span className="relative flex h-2 w-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[hsl(var(--primary))] opacity-75" /><span className="relative inline-flex h-2 w-2 rounded-full bg-[hsl(var(--primary))]" /></span>
                  LIVE
                </span>
              )}
            </div>
            <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">The numbers that move the energy transition.</h2>
          </div>
          <p className="text-xs text-muted-foreground">{isLive ? "Live market data · auto-refreshes every 2 min" : "Indicative benchmarks"}</p>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {data.map((p) => (
            <div key={p.name} className="rounded-2xl border border-border bg-card p-6" data-testid={`pulse-${p.name}`}>
              <div className="flex items-center justify-between">
                <p className="text-sm text-muted-foreground">{p.name}</p>
                <span className={`inline-flex items-center gap-1 text-xs font-semibold ${p.up ? "text-[hsl(var(--primary))]" : "text-[hsl(var(--destructive))]"}`}>
                  {p.up ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
                  {p.change}
                </span>
              </div>
              <p className="mt-3 font-display text-2xl font-bold text-foreground">{p.value}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="mt-12 overflow-hidden border-y border-border bg-card py-4">
        <div className="marquee whitespace-nowrap">
          {ticker.map((p, i) => (
            <span key={i} className="mx-6 inline-flex items-center gap-2 text-sm">
              <span className="font-semibold text-foreground">{p.name}</span>
              <span className="text-muted-foreground">{p.value}</span>
              <span className={p.up ? "text-[hsl(var(--primary))]" : "text-[hsl(var(--destructive))]"}>{p.change}</span>
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
