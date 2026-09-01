import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowUpRight, History, Search, Sparkles, TrendingUp, Flame } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";

const CAT_DOT = {
  "Current Practice": "bg-[hsl(var(--primary))]",
  "Case Study": "bg-sky-400",
  "Deal Learning": "bg-amber-400",
  "AI & Technology": "bg-[hsl(var(--primary))]",
  "Strategy Success": "bg-emerald-400",
  "Strategy Failure": "bg-rose-400",
};

function BlogCard({ b, i, trending }) {
  return (
    <motion.div initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.4, delay: (i % 6) * 0.05 }}>
      <Link to={`/insight/${b.slug}`} data-testid={`hub-blog-${b.slug}`} className="group flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-card transition-transform hover:-translate-y-1 hover:border-[hsl(var(--primary))]/50">
        <div className="relative aspect-[16/10] overflow-hidden">
          <img src={b.hero_image} alt="" loading="lazy" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
          {trending && <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-[hsl(var(--primary-foreground))]" data-testid="flame-badge"><Flame className="h-3 w-3" /> Trending</span>}
        </div>
        <div className="flex flex-1 flex-col p-5">
          <p className="flex items-center gap-2 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground"><span className={`h-2 w-2 rounded-full ${CAT_DOT[b.category] || "bg-[hsl(var(--primary))]"}`} />{b.category} · {b.read_time}</p>
          <h3 className="mt-2.5 font-display text-lg font-bold leading-snug group-hover:text-[hsl(var(--primary))]">{b.title}</h3>
          <p className="mt-2 line-clamp-2 flex-1 text-sm text-muted-foreground">{b.dek}</p>
          <span className="mt-4 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--primary))]">{b.service_title}</span>
        </div>
      </Link>
    </motion.div>
  );
}

export default function InsightsHubPage() {
  const [blogs, setBlogs] = useState([]);
  const [services, setServices] = useState([]);
  const [featured, setFeatured] = useState(null);
  const [trending, setTrending] = useState([]);
  const [trendSet, setTrendSet] = useState(new Set());
  const [themes, setThemes] = useState([]);
  const [svc, setSvc] = useState("all");
  const [cat, setCat] = useState("all");
  const [q, setQ] = useState("");

  useEffect(() => {
    window.scrollTo(0, 0);
    api.get("/service-insights?limit=200").then((r) => setBlogs(r.data)).catch(() => {});
    api.get("/service-insights/services").then((r) => setServices(r.data)).catch(() => {});
    api.get("/service-insights-featured").then((r) => setFeatured(r.data && r.data.slug ? r.data : null)).catch(() => {});
    api.get("/service-insights-trending?limit=6").then((r) => setTrending(r.data)).catch(() => {});
    api.get("/service-insights-trending-slugs").then((r) => setTrendSet(new Set(r.data || []))).catch(() => {});
    api.get("/service-insights-themes").then((r) => setThemes(r.data)).catch(() => {});
  }, []);

  const cats = useMemo(() => Array.from(new Set(blogs.map((b) => b.category))), [blogs]);
  const shown = useMemo(() => {
    const term = q.trim().toLowerCase();
    return blogs.filter((b) =>
      (svc === "all" || b.service_slug === svc) &&
      (cat === "all" || b.category === cat) &&
      (!term || [b.title, b.dek, b.service_title].some((v) => String(v || "").toLowerCase().includes(term))));
  }, [blogs, svc, cat, q]);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Insights — SK Insights by Sudarshan Karweer" description="World-class strategy, M&A, capital and leadership insights — case studies, deal learnings and practical playbooks, refreshed continuously." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-36 lg:pt-44">
        <div className="pointer-events-none absolute -right-40 top-24 h-[26rem] w-[26rem] rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-10 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">SK Insights</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">Consulting-grade insights, refreshed continuously</h1>
          <p className="mt-5 max-w-2xl text-lg text-muted-foreground">Case studies, deal learnings and practical playbooks across strategy, M&A, capital, energy and leadership — the thinking that separates decisions that compound from ones that quietly leak value.</p>
          <Link to="/archive" className="mt-6 inline-flex items-center gap-2 rounded-full border border-border px-5 py-2.5 text-sm font-semibold hover:border-[hsl(var(--primary))]" data-testid="hub-archive-link"><History className="h-4 w-4" /> Browse the full archive</Link>
          {themes.length > 0 && (
            <div className="mt-8 flex flex-wrap gap-2" data-testid="hub-theme-chips">
              <span className="mr-1 self-center text-xs font-semibold uppercase tracking-[0.15em] text-muted-foreground">Explore by theme</span>
              {themes.map((t) => (
                <Link key={t.slug} to={`/insights/theme/${t.slug}`} data-testid={`hub-theme-${t.slug}`}
                  className="rounded-full border border-border bg-card/60 px-3.5 py-1.5 text-sm font-medium transition-colors hover:border-[hsl(var(--primary))] hover:text-[hsl(var(--primary))]">
                  {t.theme} <span className="opacity-50">{t.count}</span>
                </Link>
              ))}
            </div>
          )}
        </div>
      </section>

      <section className="border-t border-border py-10">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          {trending.length > 0 && (
            <div className="mb-12" data-testid="trending-strip">
              <div className="flex items-center gap-2"><TrendingUp className="h-5 w-5 text-[hsl(var(--primary))]" /><h2 className="font-display text-xl font-bold">Most read this week</h2></div>
              <div className="mt-5 flex snap-x gap-4 overflow-x-auto pb-3 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
                {trending.map((b, i) => (
                  <Link key={b.slug} to={`/insight/${b.slug}`} data-testid={`trending-${b.slug}`}
                    className="group relative w-64 flex-shrink-0 snap-start overflow-hidden rounded-2xl border border-border bg-card transition-transform hover:-translate-y-1">
                    <div className="aspect-[16/10] overflow-hidden"><img src={b.hero_image} alt="" loading="lazy" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" /></div>
                    <span className="absolute left-3 top-3 grid h-7 w-7 place-items-center rounded-full bg-[hsl(var(--primary))] text-sm font-bold text-[hsl(var(--primary-foreground))]">{i + 1}</span>
                    <div className="p-4"><p className="text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--primary))]">{b.category}</p><h3 className="mt-1.5 line-clamp-2 text-sm font-semibold leading-snug">{b.title}</h3></div>
                  </Link>
                ))}
              </div>
            </div>
          )}
          {featured && (
            <Link to={`/insight/${featured.slug}`} data-testid="featured-insight"
              className="group mb-10 grid overflow-hidden rounded-3xl border border-[hsl(var(--primary))]/30 bg-card lg:grid-cols-2">
              <div className="aspect-[16/10] overflow-hidden lg:aspect-auto"><img src={featured.hero_image} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" /></div>
              <div className="flex flex-col justify-center p-8 lg:p-12">
                <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-[hsl(var(--primary))]/15 px-3 py-1 text-xs font-bold uppercase tracking-[0.15em] text-[hsl(var(--primary))]"><Sparkles className="h-3.5 w-3.5" /> Featured this week</span>
                <p className="mt-4 text-xs font-semibold uppercase tracking-wider text-muted-foreground">{featured.category} · {featured.service_title}</p>
                <h2 className="mt-2 font-display text-2xl font-black leading-tight tracking-tight group-hover:text-[hsl(var(--primary))] sm:text-3xl lg:text-4xl">{featured.title}</h2>
                <p className="mt-4 line-clamp-3 text-muted-foreground">{featured.dek}</p>
                <span className="mt-6 inline-flex items-center gap-1.5 text-sm font-semibold text-[hsl(var(--primary))]">Read the insight <ArrowUpRight className="h-4 w-4" /></span>
              </div>
            </Link>
          )}
          <div className="relative mb-5 max-w-md">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search insights…" data-testid="hub-search"
              className="w-full rounded-full border border-border bg-card pl-10 pr-4 py-2.5 text-sm outline-none focus:border-[hsl(var(--primary))]" />
          </div>
          <div className="flex flex-wrap gap-2" data-testid="hub-service-filters">
            <button onClick={() => setSvc("all")} className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${svc === "all" ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border border-border hover:bg-secondary"}`}>All services</button>
            {services.map((s) => (
              <button key={s.slug} onClick={() => setSvc(s.slug)} data-testid={`hub-svc-${s.slug}`} className={`rounded-full px-4 py-1.5 text-sm font-medium transition-colors ${svc === s.slug ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border border-border hover:bg-secondary"}`}>{s.title} <span className="opacity-60">{s.count}</span></button>
            ))}
          </div>
          <div className="mt-3 flex flex-wrap gap-2" data-testid="hub-cat-filters">
            <button onClick={() => setCat("all")} className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${cat === "all" ? "bg-foreground text-background" : "border border-border hover:bg-secondary"}`}>All types</button>
            {cats.map((c) => (
              <button key={c} onClick={() => setCat(c)} data-testid={`hub-cat-${c}`} className={`rounded-full px-3 py-1 text-xs font-medium transition-colors ${cat === c ? "bg-foreground text-background" : "border border-border hover:bg-secondary"}`}>{c}</button>
            ))}
          </div>

          <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-3" data-testid="hub-grid">
            {shown.map((b, i) => <BlogCard key={b.slug} b={b} i={i} trending={trendSet.has(b.slug)} />)}
          </div>
          {shown.length === 0 && <p className="py-16 text-center text-muted-foreground">No insights match your filters yet.</p>}
        </div>
      </section>
      <Footer />
    </div>
  );
}
