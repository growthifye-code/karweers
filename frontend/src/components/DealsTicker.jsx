import { useEffect, useState } from "react";
import { ArrowUpRight, Newspaper } from "lucide-react";
import api from "@/lib/api";

export default function DealsTicker() {
  const [deals, setDeals] = useState([]);

  useEffect(() => {
    let timer;
    const load = () => api.get("/deals").then((r) => setDeals(r.data?.data || [])).catch(() => {});
    load();
    timer = setInterval(load, 6 * 60 * 60 * 1000);
    return () => clearInterval(timer);
  }, []);

  if (!deals.length) return null;
  const top = deals.slice(0, 8);

  return (
    <section id="deals" className="scroll-mt-28 border-t border-border bg-card py-24 lg:py-28" data-testid="deals">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="max-w-2xl">
            <div className="flex items-center gap-3">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Deals & Developments</p>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))]/15 px-2.5 py-1 text-xs font-semibold text-[hsl(var(--primary))]">
                <span className="relative flex h-2 w-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-[hsl(var(--primary))] opacity-75" /><span className="relative inline-flex h-2 w-2 rounded-full bg-[hsl(var(--primary))]" /></span>
                LIVE
              </span>
            </div>
            <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">Live renewables M&A, fundraises & developments.</h2>
          </div>
          <p className="text-xs text-muted-foreground">Auto-curated feed · refreshes daily</p>
        </div>

        <div className="mt-10 grid gap-4 md:grid-cols-2">
          {top.map((d, i) => (
            <a key={i} href={d.link} target="_blank" rel="noreferrer" data-testid={`deal-${i}`} className="group flex items-start gap-4 rounded-2xl border border-border bg-background p-5 transition-transform hover:-translate-y-1">
              <span className="mt-0.5 grid h-9 w-9 flex-shrink-0 place-items-center rounded-full bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]"><Newspaper className="h-4 w-4" /></span>
              <div className="flex-1">
                <p className="text-sm font-medium leading-snug group-hover:text-[hsl(var(--primary))]">{d.title}</p>
                <p className="mt-1 text-xs text-muted-foreground">{d.source}</p>
              </div>
              <ArrowUpRight className="h-4 w-4 flex-shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
