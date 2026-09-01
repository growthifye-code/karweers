import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowUpRight, Flame } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import ShareBar from "@/components/ShareBar";
import api from "@/lib/api";

export default function ThemePage() {
  const { themeSlug } = useParams();
  const [data, setData] = useState(null);
  const [trendSet, setTrendSet] = useState(new Set());
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    window.scrollTo(0, 0);
    setData(null); setNotFound(false);
    api.get(`/service-insights-theme/${themeSlug}`).then((r) => setData(r.data)).catch(() => setNotFound(true));
    api.get("/service-insights-trending-slugs").then((r) => setTrendSet(new Set(r.data || []))).catch(() => {});
  }, [themeSlug]);

  if (notFound) return (
    <div className="min-h-screen bg-background text-foreground"><Navbar />
      <div className="mx-auto max-w-3xl px-6 py-40 text-center"><h1 className="font-display text-3xl font-bold">Theme not found</h1><Link to="/insights-hub" className="mt-6 inline-block text-[hsl(var(--primary))]">← All insights</Link></div><Footer /></div>
  );
  if (!data) return <div className="min-h-screen bg-background" />;

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title={`${data.theme} — SK Insights`} description={data.blurb} type="website" />
      <Navbar />
      <section className="grain relative overflow-hidden pt-36 lg:pt-44">
        <div className="pointer-events-none absolute -right-40 top-24 h-[26rem] w-[26rem] rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-10 lg:px-10">
          <Link to="/insights-hub" className="text-sm text-muted-foreground hover:text-foreground">← All insights</Link>
          <p className="mt-4 text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">SK Insights · Theme</p>
          <h1 className="mt-3 font-display text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">{data.theme}</h1>
          <p className="mt-5 max-w-2xl text-lg text-muted-foreground">{data.blurb}</p>
          <div className="mt-6 flex items-center gap-4">
            <span className="text-sm text-muted-foreground">{data.count} insight{data.count === 1 ? "" : "s"}</span>
            <ShareBar title={`${data.theme} — SK Insights`} text={data.blurb} compact />
          </div>
        </div>
      </section>

      <section className="border-t border-border py-12">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3" data-testid="theme-grid">
            {data.items.map((b, i) => (
              <motion.div key={b.slug} initial={{ opacity: 0, y: 18 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.4, delay: (i % 6) * 0.05 }}>
                <Link to={`/insight/${b.slug}`} data-testid={`theme-blog-${b.slug}`} className="group flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-card transition-transform hover:-translate-y-1 hover:border-[hsl(var(--primary))]/50">
                  <div className="relative aspect-[16/10] overflow-hidden">
                    <img src={b.hero_image} alt="" loading="lazy" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
                    {trendSet.has(b.slug) && <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-[hsl(var(--primary-foreground))]"><Flame className="h-3 w-3" /> Trending</span>}
                  </div>
                  <div className="flex flex-1 flex-col p-5">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--primary))]">{b.category} · {b.read_time}</p>
                    <h3 className="mt-2 font-display text-lg font-bold leading-snug group-hover:text-[hsl(var(--primary))]">{b.title}</h3>
                    <p className="mt-2 line-clamp-2 flex-1 text-sm text-muted-foreground">{b.dek}</p>
                    <span className="mt-4 inline-flex items-center gap-1 text-xs font-semibold text-[hsl(var(--primary))]">{b.service_title} <ArrowUpRight className="h-3.5 w-3.5" /></span>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
      <Footer />
    </div>
  );
}
