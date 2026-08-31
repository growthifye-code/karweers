import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ArrowUpRight, Sparkles, Newspaper, GraduationCap, Building2, ChevronLeft, Info } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import VideoCard from "@/components/VideoCard";
import TopicModal from "@/components/TopicModal";
import api, { track } from "@/lib/api";

const PLURAL = { sector: "sectors", agency: "agencies", oem: "oems" };

// Ordered field config per entity kind. type: text | list | cards
const FIELDS = {
  sector: [
    { key: "overview", label: "Overview", type: "text" },
    { key: "technology", label: "Core technology", type: "text" },
    { key: "financing", label: "Financing & capital", type: "text" },
    { key: "tech_automation", label: "Technology, automation & efficiency", type: "text" },
    { key: "efficiency", label: "Highest-impact automation & efficiency areas", type: "list" },
    { key: "use_cases", label: "Live examples & use cases", type: "cards" },
    { key: "key_oems", label: "Key players & OEMs", type: "cards" },
    { key: "competition", label: "Competitive landscape", type: "cards" },
    { key: "competing_tech", label: "Competing technologies", type: "text" },
    { key: "leader", label: "Who's leading", type: "text" },
    { key: "market_valuation", label: "Market & valuation", type: "text" },
  ],
  agency: [
    { key: "overview", label: "Overview", type: "text" },
    { key: "mandate", label: "Mandate & focus", type: "text" },
    { key: "india_presence", label: "India & Asia presence", type: "text" },
    { key: "key_people", label: "Leadership roles", type: "cards", note: "Roles are shown generally — verify the current appointees on the agency's own site." },
    { key: "focus_areas", label: "Focus areas", type: "list" },
    { key: "notable_programs", label: "Notable programmes", type: "cards" },
    { key: "financing_instruments", label: "Financing instruments", type: "list" },
    { key: "how_to_engage", label: "How to engage", type: "text" },
  ],
  oem: [
    { key: "overview", label: "Overview", type: "text" },
    { key: "technology", label: "Technology & products", type: "text" },
    { key: "manufacturing_capacity", label: "Manufacturing & capacity", type: "text" },
    { key: "locations", label: "Key locations", type: "list" },
    { key: "sales_presence", label: "Sales & market presence", type: "text" },
    { key: "recent_focus", label: "Recent focus", type: "cards" },
    { key: "competition", label: "Key competitors", type: "cards" },
    { key: "tech_automation", label: "Automation & efficiency", type: "text" },
    { key: "market_position", label: "Market position", type: "text" },
  ],
};

const KIND_META = {
  sector: { eyebrow: "Sector Deep-Dive", back: "/explore" },
  agency: { eyebrow: "Climate Capital", back: "/explore" },
  oem: { eyebrow: "Company Profile", back: "/explore" },
};

function cardHeading(item) {
  return item.name || item.role || item.title || "";
}

function NewsItem({ n }) {
  const [imgOk, setImgOk] = useState(true);
  return (
    <a href={n.link} target="_blank" rel="noopener noreferrer" data-testid="entity-news-item"
      className="group flex items-start gap-3 rounded-xl border border-border bg-card p-4 transition-colors hover:border-[hsl(var(--primary))]/50">
      <img
        src={imgOk ? (n.logo || n.favicon) : n.favicon}
        onError={() => setImgOk(false)}
        alt={n.source}
        className="mt-0.5 h-8 w-8 flex-shrink-0 rounded-md bg-white object-contain p-1"
      />
      <span className="min-w-0">
        <span className="flex items-center gap-2 text-xs font-semibold text-[hsl(var(--primary))]">
          {n.source}
          {n.credible && <span className="rounded-full bg-[hsl(var(--primary))]/15 px-1.5 py-0.5 text-[10px] uppercase tracking-wide">Credible source</span>}
        </span>
        <span className="mt-1 block text-sm font-medium leading-snug text-foreground line-clamp-2 group-hover:text-[hsl(var(--primary))]">{n.title}</span>
        {n.published && <span className="mt-1 block text-[11px] text-muted-foreground">{n.published.replace(/ \+0000$/, "").replace(/^\w{3}, /, "")}</span>}
      </span>
    </a>
  );
}

export default function EntityPage({ kind }) {
  const { slug } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => { window.scrollTo(0, 0); }, [slug]);

  useEffect(() => {
    setLoading(true);
    setNotFound(false);
    api.get(`/${PLURAL[kind]}/${slug}`)
      .then((r) => { setData(r.data); track("view", `${kind}:${slug}`); })
      .catch((e) => { if (e?.response?.status === 404) setNotFound(true); })
      .finally(() => setLoading(false));
  }, [kind, slug]);

  const profile = (data && (data.profile || data.deepdive)) || {};
  const fields = FIELDS[kind] || [];
  const meta = KIND_META[kind];
  const [topicItem, setTopicItem] = useState(null);
  const vtopic = data?.video_topic || "energy";
  const openTopic = (name) => { if (name) setTopicItem({ name, context: data?.name || "" }); };

  const CardLogo = ({ item }) => {
    const [ok, setOk] = useState(true);
    const src = item.logo || item.favicon;
    if (!src || !ok) return null;
    return <img src={src} onError={() => setOk(false)} alt="" className="h-7 w-7 flex-shrink-0 rounded-md bg-white object-contain p-1" />;
  };

  const renderField = (f) => {
    const v = profile[f.key];
    if (v == null || (Array.isArray(v) && v.length === 0) || v === "") return null;
    return (
      <div key={f.key} data-testid={`field-${f.key}`} onClick={() => openTopic(`${f.label} — ${data?.name || ""}`)}
        className="group cursor-pointer rounded-2xl border border-border bg-card p-6 transition-colors hover:border-[hsl(var(--primary))]/50">
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-display text-lg font-bold">{f.label}</h3>
          <span className="inline-flex flex-shrink-0 items-center gap-1 text-[11px] font-semibold text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100 group-hover:text-[hsl(var(--primary))]">
            Dive deeper <ArrowUpRight className="h-3.5 w-3.5" />
          </span>
        </div>
        {f.note && (
          <p className="mt-1 inline-flex items-start gap-1.5 text-[11px] font-medium text-amber-500">
            <Info className="mt-0.5 h-3 w-3 flex-shrink-0" /> {f.note}
          </p>
        )}
        {f.type === "text" && <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{v}</p>}
        {f.type === "list" && (
          <ul className="mt-3 flex flex-wrap gap-2">
            {v.map((s, i) => (
              <li key={i} className="rounded-full border border-border bg-background px-3 py-1.5 text-xs font-medium text-foreground">{s}</li>
            ))}
          </ul>
        )}
        {f.type === "cards" && (
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {v.map((item, i) => (
              <button key={i} type="button" data-testid={`card-${f.key}-${i}`}
                onClick={(e) => { e.stopPropagation(); openTopic(cardHeading(item)); }}
                className="flex items-start gap-3 rounded-xl border border-border bg-background p-4 text-left transition-all hover:-translate-y-0.5 hover:border-[hsl(var(--primary))]/60">
                <CardLogo item={item} />
                <span className="min-w-0">
                  <span className="flex items-center gap-1 text-sm font-semibold text-foreground">
                    {cardHeading(item)} <ArrowUpRight className="h-3.5 w-3.5 flex-shrink-0 opacity-40" />
                  </span>
                  {item.note && <span className="mt-1 block text-xs leading-relaxed text-muted-foreground">{item.note}</span>}
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    );
  };

  if (notFound) {
    return (
      <div className="min-h-screen bg-background text-foreground">
        <Navbar />
        <div className="mx-auto grid max-w-3xl place-items-center px-6 py-40 text-center">
          <h1 className="font-display text-3xl font-bold">Not found</h1>
          <p className="mt-3 text-muted-foreground">This page doesn't exist yet.</p>
          <Link to="/explore" className="mt-6 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))]">Explore all →</Link>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title={data ? `${data.name} — ${meta.eyebrow} | Sudarshan Karweer` : "Loading…"}
        description={data?.blurb || "Deep-dive briefing, financing, live news and curated video."} />
      <Navbar />

      {/* Hero */}
      <section className="border-b border-border bg-secondary/30 pt-28 pb-14 md:pt-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <Link to={meta.back} data-testid="entity-back" className="inline-flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground">
            <ChevronLeft className="h-4 w-4" /> Sectors & Capital
          </Link>
          {loading && !data ? (
            <div className="mt-8 h-10 w-2/3 animate-pulse rounded-lg bg-muted" />
          ) : data && (
            <div className="mt-6 flex flex-col gap-6 md:flex-row md:items-center md:justify-between">
              <div className="flex items-start gap-4">
                {data.logo && (kind === "agency" || kind === "oem") && (
                  <img src={data.logo} alt={data.name} onError={(e) => { e.currentTarget.style.display = "none"; }}
                    className="h-16 w-16 flex-shrink-0 rounded-xl bg-white object-contain p-2" />
                )}
                <div>
                  <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">
                    <Building2 className="h-3.5 w-3.5" /> {meta.eyebrow} · {data.tag}
                  </span>
                  <h1 className="mt-4 font-display text-4xl font-bold leading-[1.05] md:text-5xl" data-testid="entity-title">{data.name}</h1>
                  <p className="mt-3 max-w-2xl text-base text-muted-foreground">{data.blurb}</p>
                </div>
              </div>
              <a href="/#consult" className="group inline-flex flex-shrink-0 items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-5 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                Book a consultation <ArrowUpRight className="h-4 w-4" />
              </a>
            </div>
          )}
        </div>
      </section>

      {loading && !data ? (
        <div className="mx-auto grid max-w-7xl place-items-center px-6 py-24">
          <div className="h-8 w-8 animate-spin rounded-full border-2 border-[hsl(var(--primary))] border-t-transparent" />
        </div>
      ) : data && (
        <>
          {/* SK Insights */}
          {data.insights?.length > 0 && (
            <section className="border-b border-border py-12" data-testid="entity-insights">
              <div className="mx-auto max-w-7xl px-6 lg:px-10">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-[hsl(var(--primary))]" />
                  <h2 className="font-display text-2xl font-bold">SK Insights</h2>
                </div>
                <div className="mt-6 grid gap-4 md:grid-cols-2">
                  {data.insights.slice(0, 4).map((ins, i) => (
                    <div key={i} className="rounded-2xl border border-border bg-card p-6">
                      <p className="text-sm font-bold text-[hsl(var(--primary))]">{ins.title}</p>
                      <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{ins.insight}</p>
                      {ins.date && <p className="mt-3 text-[11px] uppercase tracking-wide text-muted-foreground/70">{ins.date}</p>}
                    </div>
                  ))}
                </div>
              </div>
            </section>
          )}

          {/* Profile fields */}
          <section className="py-12">
            <div className="mx-auto grid max-w-7xl gap-5 px-6 lg:grid-cols-2 lg:px-10">
              {fields.map(renderField)}
            </div>
          </section>

          {/* News */}
          {data.news?.length > 0 && (
            <section className="border-t border-border py-12" data-testid="entity-news">
              <div className="mx-auto max-w-7xl px-6 lg:px-10">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Newspaper className="h-5 w-5 text-[hsl(var(--primary))]" />
                    <h2 className="font-display text-2xl font-bold">Latest news</h2>
                  </div>
                  <span className="text-xs text-muted-foreground">Auto-refreshed every 4 hours · credible publications</span>
                </div>
                <div className="mt-6 grid gap-3 md:grid-cols-2 lg:grid-cols-3">
                  {data.news.map((n, i) => <NewsItem key={i} n={n} />)}
                </div>
              </div>
            </section>
          )}

          {/* Videos */}
          {data.videos?.length > 0 && (
            <section className="border-t border-border py-12" data-testid="entity-videos">
              <div className="mx-auto max-w-7xl px-6 lg:px-10">
                <div className="flex items-center gap-2">
                  <GraduationCap className="h-5 w-5 text-[hsl(var(--primary))]" />
                  <h2 className="font-display text-2xl font-bold">Curated watchlist</h2>
                </div>
                <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
                  {data.videos.slice(0, 8).map((v) => (
                    <VideoCard key={v.video_id} video={v} onPlay={() => track("video", `${kind}:${slug}`)} />
                  ))}
                </div>
              </div>
            </section>
          )}
        </>
      )}
      {topicItem && (
        <TopicModal name={topicItem.name} context={topicItem.context} topic={vtopic} onClose={() => setTopicItem(null)} />
      )}
      <Footer />
    </div>
  );
}
