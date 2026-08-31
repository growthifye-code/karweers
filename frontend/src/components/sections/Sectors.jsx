import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";

export const SECTORS = [
  "M&A", "Aviation", "Metals & Mining", "Industrial & Consumer Products", "Cement",
  "Steel", "Telecom", "Agriculture", "Start-up Funding", "Renewable Energy",
  "Energy Storage / BESS", "Green Hydrogen", "Climate & Green Financing", "Asset Monetisation",
];

// Sectors that have a dedicated deep-dive page; the rest link to the explore index.
const SECTOR_SLUGS = {
  "Renewable Energy": "renewable-energy",
  "Energy Storage / BESS": "storage",
  "Green Hydrogen": "green-hydrogen",
  "Climate & Green Financing": "climate-finance",
  "Asset Monetisation": "asset-monetisation",
  "Start-up Funding": "strategy",
};

function chipTo(name) {
  const slug = SECTOR_SLUGS[name];
  return slug ? `/sectors/${slug}` : "/explore";
}

export default function Sectors() {
  const row = [...SECTORS, ...SECTORS];
  return (
    <section className="border-y border-border bg-card py-16" data-testid="sectors">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Sector Depth</p>
            <h2 className="mt-3 font-display text-2xl font-extrabold tracking-tight sm:text-3xl">Two decades. A dozen-plus industries.</h2>
            <p className="mt-2 max-w-lg text-sm text-muted-foreground">Cross-sector pattern recognition that compounds into sharper advice — now with deep-dive pages on each sector, the agencies financing the transition, and the companies building it.</p>
          </div>
          <Link to="/explore" data-testid="sectors-explore-cta"
            className="group inline-flex flex-shrink-0 items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
            Explore Sectors &amp; Capital <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </Link>
        </div>
      </div>
      <div className="mt-10 space-y-3 overflow-hidden">
        <div className="marquee whitespace-nowrap">
          {row.map((s, i) => (
            <Link key={i} to={chipTo(s)} data-testid={`sector-chip-${i}`}
              className="mx-2 inline-flex items-center rounded-full border border-border bg-background px-5 py-2 text-sm font-medium transition-colors hover:border-[hsl(var(--primary))] hover:text-[hsl(var(--primary))]">
              <span className="mr-2 h-1.5 w-1.5 rounded-full bg-[hsl(var(--primary))]" />{s}
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
}
