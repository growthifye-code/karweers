import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import ArticleCard from "@/components/ArticleCard";

export default function InsightsPreview({ articles = [] }) {
  const items = articles.filter((a) => a.category !== "casestudy").slice(0, 6);
  return (
    <section id="insights" className="scroll-mt-24 border-t border-border bg-card py-24 lg:py-32" data-testid="insights-preview">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Insights</p>
            <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">
              Fresh thinking on economics, energy & the transition.
            </h2>
          </div>
          <Link to="/insights" data-testid="all-insights-link" className="inline-flex items-center gap-1 rounded-full border border-border px-5 py-2.5 text-sm font-semibold transition-colors hover:bg-secondary">
            All insights <ArrowUpRight className="h-4 w-4" />
          </Link>
        </div>
        <div className="mt-12 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {items.map((a) => <ArticleCard key={a.slug} article={a} testid={`insight-${a.slug}`} />)}
        </div>
      </div>
    </section>
  );
}
