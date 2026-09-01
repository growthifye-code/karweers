import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { FileText, Video, Headphones, Radio, Newspaper, Search, ArrowUpRight, ExternalLink } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";

const TYPES = [
  { key: "all", label: "Everything", icon: null },
  { key: "blog", label: "Blogs", icon: FileText },
  { key: "article", label: "Articles", icon: Newspaper },
  { key: "video", label: "Videos", icon: Video },
  { key: "audio", label: "Audio", icon: Headphones },
  { key: "signal", label: "Market Signals", icon: Radio },
];
const TYPE_ICON = { blog: FileText, article: Newspaper, video: Video, audio: Headphones, signal: Radio };

function fmt(d) { if (!d) return ""; try { return new Date(d).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }); } catch { return d; } }

function Card({ it, i }) {
  const Icon = TYPE_ICON[it.type] || FileText;
  const inner = (
    <>
      {it.image ? (
        <div className="aspect-[16/10] overflow-hidden"><img src={it.image} alt="" loading="lazy" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" /></div>
      ) : (
        <div className="grid aspect-[16/10] place-items-center bg-secondary/40"><Icon className="h-10 w-10 text-[hsl(var(--primary))]/70" /></div>
      )}
      <div className="flex flex-1 flex-col p-5">
        <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--primary))]"><Icon className="h-3.5 w-3.5" /> {it.tag || it.type}{it.date && <span className="text-muted-foreground">· {fmt(it.date)}</span>}</p>
        <h3 className="mt-2.5 line-clamp-2 font-display text-base font-bold leading-snug group-hover:text-[hsl(var(--primary))]">{it.title}</h3>
        {it.subtitle && <p className="mt-1.5 line-clamp-1 flex-1 text-xs text-muted-foreground">{it.subtitle}</p>}
        <span className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[hsl(var(--primary))]">{it.external ? <>Watch/Listen <ExternalLink className="h-3.5 w-3.5" /></> : <>Open <ArrowUpRight className="h-3.5 w-3.5" /></>}</span>
      </div>
    </>
  );
  const cls = "group flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-card transition-transform hover:-translate-y-1 hover:border-[hsl(var(--primary))]/50";
  return (
    <motion.div initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.35, delay: (i % 8) * 0.04 }}>
      {it.external
        ? <a href={it.url} target="_blank" rel="noopener noreferrer" className={cls} data-testid={`archive-item-${i}`}>{inner}</a>
        : <Link to={it.url} className={cls} data-testid={`archive-item-${i}`}>{inner}</Link>}
    </motion.div>
  );
}

export default function ArchivePage() {
  const [data, setData] = useState({ items: [], counts: {}, themes: [], theme_counts: {}, total: 0 });
  const [type, setType] = useState("all");
  const [theme, setTheme] = useState("all");
  const [q, setQ] = useState("");

  useEffect(() => {
    window.scrollTo(0, 0);
    api.get("/archive?limit=400").then((r) => setData(r.data)).catch(() => {});
  }, []);

  const shown = useMemo(() => {
    const term = q.trim().toLowerCase();
    return data.items.filter((it) =>
      (type === "all" || it.type === type) &&
      (theme === "all" || it.theme === theme) &&
      (!term || [it.title, it.subtitle, it.tag, it.theme].some((v) => String(v || "").toLowerCase().includes(term))));
  }, [data.items, type, theme, q]);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Archive — Sudarshan Karweer" description="The full archive of insights, blogs, videos, audio and market signals — everything Sudarshan Karweer has published, in one place." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-36 lg:pt-44">
        <div className="pointer-events-none absolute -left-40 top-24 h-[26rem] w-[26rem] rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-8 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">The Archive</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">Everything, in one place</h1>
          <p className="mt-5 max-w-2xl text-lg text-muted-foreground">Blogs, articles, videos, audiobooks and market signals — the full body of work, tagged by theme. Blogs refresh on a rolling 7-day cadence; earlier editions are preserved here.</p>
        </div>
      </section>

      <section className="border-t border-border py-10">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="flex flex-wrap items-end gap-4">
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Content type</span>
                <select value={type} onChange={(e) => setType(e.target.value)} data-testid="archive-type-select"
                  className="min-w-[180px] rounded-full border border-border bg-card px-4 py-2.5 text-sm font-medium outline-none focus:border-[hsl(var(--primary))]">
                  {TYPES.map((t) => (
                    <option key={t.key} value={t.key}>{t.label}{t.key !== "all" && data.counts[t.key] ? ` (${data.counts[t.key]})` : ""}</option>
                  ))}
                </select>
              </label>
              <label className="flex flex-col gap-1.5">
                <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Theme</span>
                <select value={theme} onChange={(e) => setTheme(e.target.value)} data-testid="archive-theme-select"
                  className="min-w-[180px] rounded-full border border-border bg-card px-4 py-2.5 text-sm font-medium outline-none focus:border-[hsl(var(--primary))]">
                  <option value="all">All themes</option>
                  {(data.themes || []).map((th) => (
                    <option key={th} value={th}>{th}{data.theme_counts[th] ? ` (${data.theme_counts[th]})` : ""}</option>
                  ))}
                </select>
              </label>
            </div>
            <div className="relative max-w-xs flex-1 lg:max-w-xs">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search the archive…" data-testid="archive-search"
                className="w-full rounded-full border border-border bg-card pl-10 pr-4 py-2.5 text-sm outline-none focus:border-[hsl(var(--primary))]" />
            </div>
          </div>

          <p className="mt-5 text-sm text-muted-foreground" data-testid="archive-count">{shown.length} item{shown.length === 1 ? "" : "s"}</p>
          <div className="mt-4 grid gap-5 sm:grid-cols-2 lg:grid-cols-4" data-testid="archive-grid">
            {shown.map((it, i) => <Card key={`${it.type}-${i}-${it.title}`} it={it} i={i} />)}
          </div>
          {shown.length === 0 && <p className="py-16 text-center text-muted-foreground">Nothing here yet for this filter.</p>}
        </div>
      </section>
      <Footer />
    </div>
  );
}
