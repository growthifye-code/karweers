import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft, ArrowUpRight } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import ShareBar from "@/components/ShareBar";
import api from "@/lib/api";

export default function StrategyInsightPage() {
  const { slug } = useParams();
  const [a, setA] = useState(null);
  const [notFound, setNotFound] = useState(false);
  useEffect(() => {
    window.scrollTo(0, 0);
    api.get(`/strategy-insights/${slug}`).then((r) => setA(r.data)).catch(() => setNotFound(true));
  }, [slug]);

  if (notFound) return (
    <div className="min-h-screen bg-background text-foreground"><Navbar />
      <div className="mx-auto max-w-3xl px-6 py-40 text-center"><h1 className="font-display text-3xl font-bold">Article not found</h1><Link to="/strategy-tools" className="mt-6 inline-block text-[hsl(var(--primary))]">← Strategy Toolkit</Link></div><Footer /></div>
  );
  if (!a) return <div className="min-h-screen bg-background" />;

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title={`${a.title} — Sudarshan Karweer`} description={a.dek}
        jsonLd={{ "@context": "https://schema.org", "@type": "Article", headline: a.title, description: a.dek, author: { "@type": "Person", name: "Sudarshan Karweer" } }} />
      <Navbar />
      <article className="mx-auto max-w-3xl px-6 pt-36 pb-24 lg:pt-44">
        <Link to="/strategy-tools" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground"><ArrowLeft className="h-4 w-4" /> Strategy Toolkit</Link>
        <p className="mt-8 text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">{a.category} · {a.read_time}</p>
        <h1 className="mt-4 font-display text-4xl font-black leading-[1.1] tracking-tight sm:text-5xl">{a.title}</h1>
        <p className="mt-5 text-lg font-medium text-muted-foreground">{a.dek}</p>
        <div className="mt-6 border-y border-border py-4"><ShareBar title={a.title} text={a.dek} /></div>
        <div className="mt-10 space-y-10">
          {a.sections.map((s, i) => (
            <section key={i} data-testid={`insight-section-${i}`}>
              <h2 className="font-display text-2xl font-bold tracking-tight">{s.h}</h2>
              <p className="mt-3 leading-relaxed text-muted-foreground">{s.p}</p>
            </section>
          ))}
        </div>
        <div className="mt-14 rounded-2xl border border-border bg-secondary/40 p-7">
          <h3 className="font-display text-xl font-bold">Work through this with Sudarshan.</h3>
          <p className="mt-2 text-sm text-muted-foreground">Turn the thinking into a plan in a focused 1:1 strategy session.</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <Link to="/services/business-strategy" className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))]">Explore strategy services <ArrowUpRight className="h-4 w-4" /></Link>
            <a href="/#consult" className="inline-flex items-center gap-1.5 rounded-full border border-border px-6 py-3 text-sm font-semibold hover:bg-secondary">Book a consultation</a>
          </div>
        </div>
      </article>
      <Footer />
    </div>
  );
}
