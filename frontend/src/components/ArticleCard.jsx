import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";

const CATEGORY_LABEL = {
  news: "News", blog: "Blog", analysis: "Analysis", rd: "R&D", casestudy: "Case Study",
};

export default function ArticleCard({ article, testid }) {
  return (
    <Link
      to={`/insights/${article.slug}`}
      data-testid={testid}
      className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card transition-transform hover:-translate-y-1"
    >
      <div className="relative h-48 overflow-hidden">
        <img src={article.image} alt={article.title} className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
        <span className="absolute left-4 top-4 rounded-full bg-[hsl(var(--accent))] px-3 py-1 text-xs font-semibold text-[hsl(var(--accent-foreground))]">
          {CATEGORY_LABEL[article.category] || article.category}
        </span>
      </div>
      <div className="flex flex-1 flex-col p-6">
        {article.sector && <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">{article.sector}</p>}
        <h3 className="mt-2 font-display text-lg font-bold leading-snug text-foreground group-hover:text-[hsl(var(--primary))]">
          {article.title}
        </h3>
        <p className="mt-3 flex-1 text-sm leading-relaxed text-muted-foreground line-clamp-3">{article.summary}</p>
        <span className="mt-5 inline-flex items-center gap-1 text-sm font-semibold text-[hsl(var(--primary))]">
          Read <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
        </span>
      </div>
    </Link>
  );
}
