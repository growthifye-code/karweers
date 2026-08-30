export const SECTORS = [
  "M&A", "Aviation", "Metals & Mining", "Industrial & Consumer Products", "Cement",
  "Steel", "Telecom", "Agriculture", "Start-up Funding", "Renewable Energy",
  "Energy Storage / BESS", "Green Hydrogen", "Climate & Green Financing", "Asset Monetisation",
];

export default function Sectors() {
  const row = [...SECTORS, ...SECTORS];
  return (
    <section className="border-y border-border bg-card py-16" data-testid="sectors">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Sector Depth</p>
            <h2 className="mt-3 font-display text-2xl font-extrabold tracking-tight sm:text-3xl">Two decades. A dozen-plus industries.</h2>
          </div>
          <p className="max-w-sm text-sm text-muted-foreground">From heavy industry to high-growth start-ups — cross-sector pattern recognition that compounds into sharper advice.</p>
        </div>
      </div>
      <div className="mt-10 space-y-3 overflow-hidden">
        <div className="marquee whitespace-nowrap">
          {row.map((s, i) => (
            <span key={i} className="mx-2 inline-flex items-center rounded-full border border-border bg-background px-5 py-2 text-sm font-medium">
              <span className="mr-2 h-1.5 w-1.5 rounded-full bg-[hsl(var(--primary))]" />{s}
            </span>
          ))}
        </div>
      </div>
    </section>
  );
}
