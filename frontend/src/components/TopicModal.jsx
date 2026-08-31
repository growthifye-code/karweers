import { useEffect, useState } from "react";
import { X, Sparkles, Newspaper, PenSquare, GraduationCap, ExternalLink } from "lucide-react";
import VideoCard from "@/components/VideoCard";
import api, { track } from "@/lib/api";

function SourceRow({ n }) {
  const [ok, setOk] = useState(true);
  return (
    <a href={n.link} target="_blank" rel="noopener noreferrer" data-testid="topic-news-item"
      className="group flex items-start gap-3 rounded-xl border border-border bg-background p-3 transition-colors hover:border-[hsl(var(--primary))]/50">
      <img src={ok ? (n.logo || n.favicon) : n.favicon} onError={() => setOk(false)} alt={n.source}
        className="mt-0.5 h-7 w-7 flex-shrink-0 rounded-md bg-white object-contain p-1" />
      <span className="min-w-0">
        <span className="flex items-center gap-2 text-[11px] font-semibold text-[hsl(var(--primary))]">
          {n.source}{n.credible && <span className="rounded-full bg-[hsl(var(--primary))]/15 px-1.5 py-0.5 text-[9px] uppercase tracking-wide">Credible</span>}
        </span>
        <span className="mt-0.5 block text-[13px] font-medium leading-snug text-foreground line-clamp-2 group-hover:text-[hsl(var(--primary))]">{n.title}</span>
      </span>
    </a>
  );
}

export default function TopicModal({ name, context, topic, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState("news");
  const [logoOk, setLogoOk] = useState(true);

  useEffect(() => {
    if (!name) return;
    setLoading(true); setData(null); setTab("news"); setLogoOk(true);
    const params = new URLSearchParams({ name, context: context || "", topic: topic || "energy" });
    api.get(`/topic?${params.toString()}`)
      .then((r) => { setData(r.data); track("topic", `${context}:${name}`); })
      .finally(() => setLoading(false));
  }, [name, context, topic]);

  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  if (!name) return null;
  const logo = data?.logo || data?.favicon;

  return (
    <div className="fixed inset-0 z-[200] flex items-start justify-center overflow-y-auto p-3 sm:p-6" data-testid="topic-modal">
      <div className="absolute inset-0 bg-black/75 backdrop-blur-sm" onClick={onClose} />
      <div className="relative z-10 my-2 w-full max-w-3xl rounded-2xl border border-border bg-card shadow-2xl">
        {/* Header */}
        <div className="sticky top-0 z-10 flex items-start gap-3 rounded-t-2xl border-b border-border bg-card/95 p-5 backdrop-blur">
          {logo && logoOk && (
            <img src={logo} alt={name} onError={() => setLogoOk(false)} className="h-11 w-11 flex-shrink-0 rounded-lg bg-white object-contain p-1.5" />
          )}
          <div className="min-w-0 flex-1">
            {context && <p className="text-[11px] font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">{context}</p>}
            <h2 className="font-display text-xl font-bold leading-tight text-foreground sm:text-2xl">{name}</h2>
          </div>
          <button onClick={onClose} data-testid="topic-modal-close" className="grid h-9 w-9 flex-shrink-0 place-items-center rounded-full border border-border text-muted-foreground hover:bg-secondary">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="p-5">
          {loading ? (
            <div className="grid place-items-center py-16">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-[hsl(var(--primary))] border-t-transparent" />
              <p className="mt-3 text-xs text-muted-foreground">Pulling the latest detail, news &amp; watchlist…</p>
            </div>
          ) : data && (
            <>
              {data.overview && <p className="text-sm leading-relaxed text-muted-foreground">{data.overview}</p>}

              {data.details?.length > 0 && (
                <div className="mt-5 grid gap-3 sm:grid-cols-2">
                  {data.details.map((d, i) => (
                    <div key={i} className="rounded-xl border border-border bg-background p-3.5">
                      <p className="text-[13px] font-semibold text-foreground">{d.point || d.name || d.title}</p>
                      {d.note && <p className="mt-1 text-xs leading-relaxed text-muted-foreground">{d.note}</p>}
                    </div>
                  ))}
                </div>
              )}

              {data.sk_take && (
                <div className="mt-5 rounded-xl border border-[hsl(var(--primary))]/30 bg-[hsl(var(--primary))]/5 p-4">
                  <p className="flex items-center gap-1.5 text-xs font-bold text-[hsl(var(--primary))]"><Sparkles className="h-3.5 w-3.5" /> SK Take</p>
                  <p className="mt-2 text-sm leading-relaxed text-foreground">{data.sk_take}</p>
                </div>
              )}

              {/* Tabs */}
              <div className="mt-6 flex gap-2 border-b border-border">
                {[["news", "News", Newspaper], ["blogs", "Blogs & analysis", PenSquare], ["videos", "Curated videos", GraduationCap]].map(([id, label, Icon]) => (
                  <button key={id} onClick={() => setTab(id)} data-testid={`topic-tab-${id}`}
                    className={`flex items-center gap-1.5 border-b-2 px-2 pb-2 text-xs font-semibold transition-colors ${tab === id ? "border-[hsl(var(--primary))] text-[hsl(var(--primary))]" : "border-transparent text-muted-foreground hover:text-foreground"}`}>
                    <Icon className="h-3.5 w-3.5" /> {label}
                  </button>
                ))}
              </div>

              <div className="mt-4">
                {tab === "news" && (
                  <div className="grid gap-2.5 sm:grid-cols-2">
                    {(data.news || []).length ? data.news.map((n, i) => <SourceRow key={i} n={n} />) : <p className="text-xs text-muted-foreground">No recent news found.</p>}
                  </div>
                )}
                {tab === "blogs" && (
                  <div className="grid gap-2.5 sm:grid-cols-2">
                    {(data.blogs || []).length ? data.blogs.map((n, i) => <SourceRow key={i} n={n} />) : <p className="text-xs text-muted-foreground">No analysis pieces found.</p>}
                  </div>
                )}
                {tab === "videos" && (
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {(data.videos || []).length ? data.videos.map((v) => <VideoCard key={v.video_id} video={v} onPlay={() => track("video", `topic:${name}`)} />) : <p className="text-xs text-muted-foreground">No videos found.</p>}
                  </div>
                )}
              </div>

              <a href="/#consult" className="mt-6 inline-flex items-center gap-1 text-xs font-semibold text-[hsl(var(--primary))] hover:underline">
                Discuss {name} with Sudarshan <ExternalLink className="h-3 w-3" />
              </a>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
