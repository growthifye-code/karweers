import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import ArticleCard from "@/components/ArticleCard";
import api from "@/lib/api";

const FILTERS = [
  { key: "all", label: "All" },
  { key: "news", label: "News" },
  { key: "analysis", label: "Company Analysis" },
  { key: "blog", label: "Blogs" },
  { key: "rd", label: "R&D / Technology" },
  { key: "casestudy", label: "Case Studies" },
];

export default function InsightsPage() {
  const [articles, setArticles] = useState([]);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    api.get("/articles").then((r) => setArticles(r.data)).catch(() => {});
  }, []);

  const filtered = filter === "all" ? articles : articles.filter((a) => a.category === filter);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Navbar />
      <section className="grain relative overflow-hidden pt-32 lg:pt-40">
        <div className="pointer-events-none absolute -right-32 top-10 h-80 w-80 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[120px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Insights & Intelligence</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-black tracking-tight sm:text-5xl">
            Macro & micro economics, energy, climate & company analysis.
          </h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">
            Curated intelligence across renewable energy, storage, green hydrogen, climate & green financing,
            sustainability and business strategy — powered by the Karweer insight engine.
          </p>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 pb-24 lg:px-10">
        <div className="mb-10 flex flex-wrap gap-2 border-b border-border pb-6">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              onClick={() => setFilter(f.key)}
              data-testid={`filter-${f.key}`}
              className={`rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                filter === f.key ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border border-border text-muted-foreground hover:bg-secondary"
              }`}
            >
              {f.label}
            </button>
          ))}
        </div>

        {filtered.length === 0 ? (
          <p className="py-20 text-center text-muted-foreground">No articles in this category yet.</p>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {filtered.map((a) => <ArticleCard key={a.slug} article={a} testid={`article-${a.slug}`} />)}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
