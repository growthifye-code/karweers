import { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowLeft, ArrowUpRight, Sparkles, CheckCircle2, History, Quote } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import ShareBar from "@/components/ShareBar";
import { toast } from "sonner";
import api from "@/lib/api";

const CAT_COLORS = {
  "Current Practice": "text-[hsl(var(--primary))]",
  "Case Study": "text-sky-400",
  "Deal Learning": "text-amber-400",
  "AI & Technology": "text-[hsl(var(--primary))]",
  "Strategy Success": "text-emerald-400",
  "Strategy Failure": "text-rose-400",
};

export default function ServiceInsightPage({ archived = false }) {
  const { slug, id } = useParams();
  const [a, setA] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const viewed = useRef(null);
  useEffect(() => {
    window.scrollTo(0, 0);
    setA(null); setNotFound(false);
    const path = archived ? `/service-insights/archive/${id}` : `/service-insights/${slug}`;
    api.get(path).then((r) => setA(r.data)).catch(() => setNotFound(true));
    if (!archived && slug && viewed.current !== slug) {
      viewed.current = slug;
      api.post("/insights/track", { slug, event: "view" }).catch(() => {});
    }
  }, [slug, id, archived]);

  const recordShare = (platform) => {
    if (!archived && a?.slug) api.post("/insights/track", { slug: a.slug, event: "share", platform }).catch(() => {});
  };

  const shareTake = async () => {
    const url = window.location.href;
    const quote = `"${a.sk_insight.take}"\n\n— Sudarshan Karweer, on ${a.title}\n\n${url}`;
    try { await navigator.clipboard.writeText(quote); toast.success("SK's take copied — ready to paste on LinkedIn"); }
    catch { /* clipboard blocked */ }
    recordShare("quote");
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(url)}`, "_blank", "noopener");
  };

  if (notFound) return (
    <div className="min-h-screen bg-background text-foreground"><Navbar />
      <div className="mx-auto max-w-3xl px-6 py-40 text-center"><h1 className="font-display text-3xl font-bold">Insight not found</h1><Link to="/insights-hub" className="mt-6 inline-block text-[hsl(var(--primary))]">← All insights</Link></div><Footer /></div>
  );
  if (!a) return <div className="min-h-screen bg-background" />;

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title={`${a.title} — SK Insights`} description={a.dek} image={a.hero_image} type="article"
        jsonLd={{ "@context": "https://schema.org", "@type": "Article", headline: a.title, description: a.dek, image: a.hero_image, author: { "@type": "Person", name: "Sudarshan Karweer" } }} />
      <Navbar />

      <div className="relative h-[46vh] min-h-[340px] w-full overflow-hidden">
        <img src={a.hero_image} alt={a.title} className="h-full w-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-background/70 to-background/20" />
        <div className="absolute inset-x-0 bottom-0">
          <div className="mx-auto max-w-3xl px-6 pb-8">
            <Link to={`/services/${a.service_slug}`} className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="h-4 w-4" /> {a.service_title}</Link>
            <p className={`mt-4 text-xs font-semibold uppercase tracking-[0.2em] ${CAT_COLORS[a.category] || "text-[hsl(var(--primary))]"}`}>{a.category} · {a.read_time}</p>
            <h1 className="mt-3 font-display text-3xl font-black leading-[1.1] tracking-tight sm:text-4xl lg:text-5xl">{a.title}</h1>
          </div>
        </div>
      </div>

      <article className="mx-auto max-w-3xl px-6 pb-24 pt-8">
        {archived && (
          <div className="mb-6 rounded-xl border border-amber-400/40 bg-amber-400/10 px-5 py-3 text-sm" data-testid="archived-banner">
            You're reading an <strong>archived edition</strong> from {a.archived_at ? new Date(a.archived_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" }) : "an earlier date"}. <Link to={`/insight/${a.slug}`} className="font-semibold text-[hsl(var(--primary))]">Read the current edition →</Link>
          </div>
        )}
        <p className="text-lg font-medium leading-relaxed text-muted-foreground">{a.dek}</p>
        <div className="mt-6 flex items-center justify-between gap-4 border-y border-border py-4">
          <span className="text-xs uppercase tracking-[0.15em] text-muted-foreground">By Sudarshan Karweer</span>
          <ShareBar title={a.title} text={a.dek} compact onShare={recordShare} />
        </div>

        <div className="mt-10 space-y-10">
          {(a.sections || []).map((s, i) => (
            <section key={i} data-testid={`insight-section-${i}`}>
              <h2 className="font-display text-2xl font-bold tracking-tight">{s.h}</h2>
              <p className="mt-3 leading-relaxed text-muted-foreground">{s.p}</p>
            </section>
          ))}
        </div>

        {Array.isArray(a.key_takeaways) && a.key_takeaways.length > 0 && (
          <div className="mt-14 rounded-2xl border border-border bg-card p-7" data-testid="key-takeaways">
            <h3 className="font-display text-lg font-bold">Key takeaways</h3>
            <ul className="mt-4 space-y-3">
              {a.key_takeaways.map((k, i) => (
                <li key={i} className="flex items-start gap-3"><CheckCircle2 className="mt-0.5 h-5 w-5 flex-shrink-0 text-[hsl(var(--primary))]" /><span className="text-sm text-muted-foreground">{k}</span></li>
              ))}
            </ul>
          </div>
        )}

        {a.sk_insight && (a.sk_insight.take || a.sk_insight.corporate_relevance) && (
          <div className="mt-8 overflow-hidden rounded-2xl border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/[0.06]" data-testid="sk-insight">
            <div className="flex items-center gap-2 border-b border-[hsl(var(--primary))]/20 px-7 py-4">
              <Sparkles className="h-5 w-5 text-[hsl(var(--primary))]" />
              <span className="font-display text-sm font-bold uppercase tracking-[0.15em] text-[hsl(var(--primary))]">SK Insights</span>
            </div>
            <div className="space-y-5 px-7 py-6">
              {a.sk_insight.take && <p className="text-base leading-relaxed">{a.sk_insight.take}</p>}
              {a.sk_insight.corporate_relevance && (
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.15em] text-muted-foreground">What this means for corporates</p>
                  <p className="mt-2 leading-relaxed text-muted-foreground">{a.sk_insight.corporate_relevance}</p>
                </div>
              )}
              {a.sk_insight.take && (
                <button onClick={shareTake} data-testid="share-sk-take"
                  className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                  <Quote className="h-4 w-4" /> Share SK's take
                </button>
              )}
            </div>
          </div>
        )}

        <p className="mt-6 text-xs text-muted-foreground">Analysis based on public-domain reporting; views are Sudarshan's own.
          {a.earlier_editions > 0 && <> · <Link to="/insights-hub/archive" className="inline-flex items-center gap-1 text-[hsl(var(--primary))]"><History className="h-3.5 w-3.5" /> {a.earlier_editions} earlier edition{a.earlier_editions > 1 ? "s" : ""} archived</Link></>}
        </p>

        <div className="mt-12 flex items-center justify-between border-t border-border pt-6">
          <ShareBar title={a.title} text={a.dek} onShare={recordShare} />
        </div>

        <div className="mt-14 rounded-2xl border border-border bg-secondary/40 p-7">
          <h3 className="font-display text-xl font-bold">Turn this into a plan with Sudarshan.</h3>
          <p className="mt-2 text-sm text-muted-foreground">Bring this thinking to a focused 1:1 strategy session.</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link to={`/services/${a.service_slug}`} className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))]">Explore {a.service_title} <ArrowUpRight className="h-4 w-4" /></Link>
            <a href="/#consult" className="inline-flex items-center gap-1.5 rounded-full border border-border px-6 py-3 text-sm font-semibold hover:bg-secondary">Book a consultation</a>
          </div>
        </div>

        {Array.isArray(a.related) && a.related.length > 0 && (
          <div className="mt-16">
            <h3 className="font-display text-2xl font-bold">More {a.service_title} insights</h3>
            <div className="mt-6 grid gap-5 sm:grid-cols-3">
              {a.related.map((r) => (
                <Link key={r.slug} to={`/insight/${r.slug}`} className="group overflow-hidden rounded-2xl border border-border bg-card transition-transform hover:-translate-y-1" data-testid={`related-${r.slug}`}>
                  <div className="aspect-[16/10] overflow-hidden"><img src={r.hero_image} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" /></div>
                  <div className="p-4"><p className="text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--primary))]">{r.category}</p><h4 className="mt-1.5 line-clamp-2 text-sm font-semibold leading-snug">{r.title}</h4></div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </article>
      <Footer />
    </div>
  );
}
