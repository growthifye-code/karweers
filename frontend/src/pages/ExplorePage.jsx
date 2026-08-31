import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Layers, Landmark, Factory, ArrowUpRight } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";

function LogoImg({ src, alt }) {
  const [ok, setOk] = useState(true);
  if (!ok) return <div className="grid h-10 w-10 flex-shrink-0 place-items-center rounded-lg bg-secondary text-xs font-bold text-muted-foreground">{(alt || "?").slice(0, 2)}</div>;
  return <img src={src} alt={alt} onError={() => setOk(false)} className="h-10 w-10 flex-shrink-0 rounded-lg bg-white object-contain p-1.5" />;
}

function Tile({ to, name, blurb, logo, testid }) {
  return (
    <Link to={to} data-testid={testid}
      className="group flex items-start gap-4 rounded-2xl border border-border bg-card p-5 transition-all hover:-translate-y-0.5 hover:border-[hsl(var(--primary))]/50">
      {logo ? <LogoImg src={logo} alt={name} /> : (
        <span className="mt-1 h-2 w-2 flex-shrink-0 rounded-full bg-[hsl(var(--primary))]" />
      )}
      <span className="min-w-0">
        <span className="flex items-center gap-1 font-display text-base font-bold text-foreground group-hover:text-[hsl(var(--primary))]">
          {name} <ArrowUpRight className="h-4 w-4 opacity-0 transition-opacity group-hover:opacity-100" />
        </span>
        <span className="mt-1 block text-sm leading-snug text-muted-foreground line-clamp-2">{blurb}</span>
      </span>
    </Link>
  );
}

export default function ExplorePage() {
  const [sectors, setSectors] = useState([]);
  const [agencies, setAgencies] = useState([]);
  const [oems, setOems] = useState([]);

  useEffect(() => { window.scrollTo(0, 0); }, []);
  useEffect(() => {
    api.get("/sectors").then((r) => setSectors(r.data || [])).catch(() => {});
    api.get("/agencies").then((r) => setAgencies(r.data || [])).catch(() => {});
    api.get("/oems").then((r) => setOems(r.data || [])).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Sectors & Capital — Deep-Dives, Climate Finance Agencies & OEM Profiles | Sudarshan Karweer"
        description="Explore deep-dive briefings on energy sectors, dedicated pages for global & India climate-finance agencies (World Bank, ADB, AIIB, IFC, GCF and more), and profiles of leading clean-energy manufacturers — each with financing, live news and curated video." />
      <Navbar />

      <section className="border-b border-border bg-secondary/30 pt-28 pb-14 md:pt-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">
            <Layers className="h-3.5 w-3.5" /> Sectors & Capital
          </span>
          <h1 className="mt-6 max-w-4xl font-display text-4xl font-bold leading-[1.05] md:text-6xl">
            The transition, <span className="text-[hsl(var(--primary))]">mapped end-to-end.</span>
          </h1>
          <p className="mt-5 max-w-2xl text-base text-muted-foreground md:text-lg">
            Deep-dive briefings on each sector, dedicated pages for the agencies financing India &amp; Asia's transition, and profiles of the manufacturers building it — every page carries financing, live news and a curated watchlist.
          </p>
        </div>
      </section>

      {/* Sectors */}
      <section className="py-14" data-testid="explore-sectors">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <div className="flex items-center gap-2">
            <Layers className="h-5 w-5 text-[hsl(var(--primary))]" />
            <h2 className="font-display text-2xl font-bold">Sector deep-dives</h2>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">Technology, financing, automation &amp; efficiency, live examples, key players and market view.</p>
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {sectors.map((s) => (
              <Tile key={s.slug} to={`/sectors/${s.slug}`} testid={`sector-tile-${s.slug}`} name={s.name} blurb={s.blurb} />
            ))}
          </div>
        </div>
      </section>

      {/* Agencies */}
      <section className="border-t border-border py-14" data-testid="explore-agencies">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <div className="flex items-center gap-2">
            <Landmark className="h-5 w-5 text-[hsl(var(--primary))]" />
            <h2 className="font-display text-2xl font-bold">Climate &amp; development finance agencies</h2>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">Multilaterals, global climate funds, bilateral DFIs and India's own institutions — mandate, India presence, leadership, programmes &amp; live news.</p>
          {agencies.map((grp) => (
            <div key={grp.group} className="mt-10">
              <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-[hsl(var(--primary))]">{grp.group}</h3>
              <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {grp.items.map((a) => (
                  <Tile key={a.slug} to={`/capital/${a.slug}`} testid={`agency-tile-${a.slug}`} name={a.name} blurb={a.blurb} logo={a.logo} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* OEMs */}
      <section className="border-t border-border py-14" data-testid="explore-oems">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <div className="flex items-center gap-2">
            <Factory className="h-5 w-5 text-[hsl(var(--primary))]" />
            <h2 className="font-display text-2xl font-bold">OEM &amp; competitor profiles</h2>
          </div>
          <p className="mt-2 text-sm text-muted-foreground">Manufacturing footprint, locations, technology, competitors and live news for leading players.</p>
          {oems.map((grp) => (
            <div key={grp.group} className="mt-10">
              <h3 className="text-sm font-semibold uppercase tracking-[0.18em] text-[hsl(var(--primary))]">{grp.group}</h3>
              <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {grp.items.map((o) => (
                  <Tile key={o.slug} to={`/oems/${o.slug}`} testid={`oem-tile-${o.slug}`} name={o.name} blurb={o.blurb} logo={o.logo} />
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      <Footer />
    </div>
  );
}
