import { useState, useEffect, useRef } from "react";
import { Mic, Clock, ChevronDown, Loader2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import api from "@/lib/api";

const API = process.env.REACT_APP_BACKEND_URL;

function EpisodePlayer({ episodeId, introUrl }) {
  const audioRef = useRef(null);
  const playlist = introUrl ? [introUrl, `${API}/api/podcast/episodes/${episodeId}/audio`] : [`${API}/api/podcast/episodes/${episodeId}/audio`];
  const [idx, setIdx] = useState(0);
  const onEnded = () => {
    if (idx < playlist.length - 1) {
      setIdx(idx + 1);
      setTimeout(() => { audioRef.current?.play(); }, 60);
    }
  };
  return (
    <div className="mt-4">
      <audio ref={audioRef} src={playlist[idx]} controls preload="none" onEnded={onEnded} className="w-full" data-testid="episode-audio" />
      {introUrl && idx === 0 && <p className="mt-1 text-xs text-muted-foreground">Plays a short intro from Sudarshan, then the episode.</p>}
    </div>
  );
}

function EpisodeCard({ ep, introUrl }) {
  const [open, setOpen] = useState(false);
  const [full, setFull] = useState(null);
  const toggle = async () => {
    const next = !open;
    setOpen(next);
    if (next && !full) {
      try { const r = await api.get(`/podcast/episodes/${ep.id}`); setFull(r.data); } catch (e) { /* noop */ }
    }
  };
  return (
    <article className="rounded-2xl border border-border bg-card p-6 transition-colors hover:border-[hsl(var(--primary))]/40" data-testid={`podcast-episode-${ep.id}`}>
      <div className="flex items-center gap-3 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))]/10 px-2.5 py-1 font-semibold text-[hsl(var(--primary))]"><Mic className="h-3 w-3" /> Episode</span>
        {ep.duration_min && <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" /> {ep.duration_min} min</span>}
        {ep.published_at && <span>{new Date(ep.published_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</span>}
      </div>
      <h3 className="mt-3 font-display text-xl font-bold leading-snug">{ep.title}</h3>
      {ep.description && <p className="mt-2 text-sm text-muted-foreground">{ep.description}</p>}
      <EpisodePlayer episodeId={ep.id} introUrl={introUrl} />
      {ep.key_takeaways?.length > 0 && (
        <ul className="mt-4 space-y-1.5">
          {ep.key_takeaways.map((t, i) => (
            <li key={i} className="flex gap-2 text-sm text-foreground"><span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[hsl(var(--primary))]" />{t}</li>
          ))}
        </ul>
      )}
      <button onClick={toggle} data-testid={`podcast-transcript-toggle-${ep.id}`} className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-[hsl(var(--primary))]">
        {open ? "Hide transcript" : "Read transcript"} <ChevronDown className={`h-4 w-4 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="mt-3 max-h-80 overflow-y-auto whitespace-pre-line rounded-xl border border-border bg-background p-4 text-sm leading-relaxed text-muted-foreground" data-testid={`podcast-transcript-${ep.id}`}>
          {full ? full.script : <span className="inline-flex items-center gap-2"><Loader2 className="h-4 w-4 animate-spin" /> Loading…</span>}
        </div>
      )}
    </article>
  );
}

export default function PodcastPage() {
  const [data, setData] = useState(null);
  useEffect(() => { api.get("/podcast/episodes").then((r) => setData(r.data)).catch(() => setData({ episodes: [] })); }, []);
  const introUrl = data?.has_intro ? `${API}/api/podcast/intro-audio` : null;
  const eps = data?.episodes || [];

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-5xl px-6 py-20 lg:py-28">
          <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/30 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold text-[hsl(var(--primary))]"><Mic className="h-3.5 w-3.5" /> Weekly podcast</span>
          <h1 className="mt-5 font-display text-4xl font-black leading-tight sm:text-5xl lg:text-6xl">The SK Strategy Brief</h1>
          <p className="mt-5 max-w-2xl text-base text-muted-foreground">Sharp, weekly insight for founders and CXOs — strategy, structure, people, KPIs, fundraising, and the energy transition. Hosted by Sudarshan Karweer.</p>
        </div>
      </header>
      <main className="mx-auto max-w-5xl px-6 py-16">
        {!data && <p className="inline-flex items-center gap-2 text-muted-foreground"><Loader2 className="h-5 w-5 animate-spin" /> Loading episodes…</p>}
        {data && eps.length === 0 && (
          <div className="rounded-2xl border border-dashed border-border bg-card p-14 text-center" data-testid="podcast-empty">
            <Mic className="mx-auto h-10 w-10 text-muted-foreground" />
            <p className="mt-3 font-semibold">First episode dropping soon</p>
            <p className="mt-1 text-sm text-muted-foreground">A fresh episode publishes every week. Check back shortly.</p>
          </div>
        )}
        <div className="grid gap-6" data-testid="podcast-list">
          {eps.map((ep) => <EpisodeCard key={ep.id} ep={ep} introUrl={introUrl} />)}
        </div>
      </main>
      <Footer />
    </div>
  );
}
