import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowLeft } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ArticleCard from "@/components/ArticleCard";
import api from "@/lib/api";

export default function ArticleDetail() {
  const { slug } = useParams();
  const [article, setArticle] = useState(null);
  const [related, setRelated] = useState([]);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    setArticle(null);
    setNotFound(false);
    window.scrollTo(0, 0);
    api.get(`/articles/${slug}`)
      .then((r) => setArticle(r.data))
      .catch(() => setNotFound(true));
    api.get("/articles").then((r) => setRelated(r.data)).catch(() => {});
  }, [slug]);

  if (notFound) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <Navbar />
        <div className="mx-auto max-w-3xl px-6 py-40 text-center">
          <h1 className="font-display text-3xl font-bold">Article not found</h1>
          <Link to="/insights" className="mt-6 inline-block text-[hsl(var(--primary))]">← Back to insights</Link>
        </div>
        <Footer />
      </div>
    );
  }

  if (!article) {
    return <div className="min-h-screen grid place-items-center bg-background text-foreground animate-pulse font-display text-2xl">Loading…</div>;
  }

  const relatedItems = related.filter((a) => a.slug !== slug).slice(0, 3);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Navbar />
      <article className="mx-auto max-w-3xl px-6 pt-32 lg:pt-40" data-testid="article-detail">
        <Link to="/insights" className="inline-flex items-center gap-2 text-sm text-muted-foreground transition-colors hover:text-foreground">
          <ArrowLeft className="h-4 w-4" /> All insights
        </Link>
        <div className="mt-6 flex flex-wrap items-center gap-3">
          <span className="rounded-full bg-[hsl(var(--accent))] px-3 py-1 text-xs font-semibold text-[hsl(var(--accent-foreground))]">{article.category}</span>
          {article.sector && <span className="text-xs uppercase tracking-wide text-muted-foreground">{article.sector}</span>}
        </div>
        <h1 className="mt-4 font-display text-3xl font-black leading-tight tracking-tight sm:text-4xl lg:text-5xl">{article.title}</h1>
        <p className="mt-4 text-sm text-muted-foreground">By {article.author}</p>
        <img src={article.image} alt={article.title} className="mt-8 w-full rounded-2xl border border-border object-cover" />
        <div className="mt-8 space-y-6 text-base leading-relaxed text-muted-foreground">
          {article.content.split("\n\n").map((p, i) => <p key={i}>{p}</p>)}
        </div>
        <div className="mt-8 flex flex-wrap gap-2">
          {(article.tags || []).map((t) => <span key={t} className="rounded-full border border-border px-3 py-1 text-xs text-muted-foreground">{t}</span>)}
        </div>

        <div className="mt-12 rounded-2xl border border-border bg-card p-8 text-center">
          <h3 className="font-display text-xl font-bold">Want to act on this?</h3>
          <p className="mt-2 text-sm text-muted-foreground">Book a premium 1:1 consultation with Sudarshan Karweer.</p>
          <Link to="/#consult" className="mt-5 inline-block rounded-full bg-[hsl(var(--accent))] px-6 py-3 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5">
            Book Consultation
          </Link>
        </div>
      </article>

      {relatedItems.length > 0 && (
        <div className="mx-auto max-w-7xl px-6 py-24 lg:px-10">
          <h2 className="font-display text-2xl font-bold">More insights</h2>
          <div className="mt-8 grid gap-6 md:grid-cols-3">
            {relatedItems.map((a) => <ArticleCard key={a.slug} article={a} testid={`related-${a.slug}`} />)}
          </div>
        </div>
      )}
      <Footer />
    </div>
  );
}
