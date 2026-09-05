import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Mic, Clock, Play, Pause, ArrowUpRight } from "lucide-react";
import api from "@/lib/api";

const API = process.env.REACT_APP_BACKEND_URL;
const EMBLEM = "https://static.prod-images.emergentagent.com/jobs/69d54eb7-07e1-4ffd-ad08-8725f9f9829e/images/a09b8b2f1be637508ef78c38659a1ba5388d54e23e2c4150d7b98bf1a2775ce8.jpeg";

export default function FeaturedPodcast() {
  const [ep, setEp] = useState(null);
  const [introUrl, setIntroUrl] = useState(null);
  const [playing, setPlaying] = useState(false);
  const [idx, setIdx] = useState(0);
  const audioRef = useRef(null);

  useEffect(() => {
    api.get("/podcast/episodes").then((r) => {
      const eps = r.data?.episodes || [];
      if (eps.length) setEp(eps[0]);
      if (r.data?.has_intro) setIntroUrl(`${API}/api/podcast/intro-audio`);
    }).catch(() => {});
  }, []);

  if (!ep) return null;

  const playlist = introUrl
    ? [introUrl, `${API}/api/podcast/episodes/${ep.id}/audio`]
    : [`${API}/api/podcast/episodes/${ep.id}/audio`];

  const toggle = () => {
    const a = audioRef.current;
    if (!a) return;
    if (playing) { a.pause(); setPlaying(false); }
    else { a.play(); setPlaying(true); }
  };

  const onEnded = () => {
    if (idx < playlist.length - 1) {
      const next = idx + 1;
      setIdx(next);
      setTimeout(() => audioRef.current?.play(), 60);
    } else {
      setPlaying(false);
      setIdx(0);
    }
  };

  return (
    <section className="border-t border-border py-20" data-testid="home-featured-podcast">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">The SK Strategy Brief · Latest episode</p>
        <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }}
          className="mt-6 grid items-center gap-8 overflow-hidden rounded-3xl border border-[hsl(var(--primary))]/30 bg-card p-6 sm:p-8 lg:grid-cols-[auto_1fr] lg:gap-10 lg:p-10">
          <div className="relative mx-auto shrink-0">
            <img src={EMBLEM} alt="The SK Strategy Brief emblem" data-testid="featured-podcast-emblem"
              className="h-36 w-36 rounded-full object-cover ring-2 ring-[hsl(var(--primary))]/40 shadow-[0_0_60px_-12px_hsl(var(--primary)/0.6)] sm:h-44 sm:w-44" />
            <button onClick={toggle} data-testid="featured-podcast-play"
              className="absolute inset-0 m-auto grid h-16 w-16 place-items-center rounded-full bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] shadow-2xl transition-transform hover:scale-105"
              aria-label={playing ? "Pause episode" : "Play episode"}>
              {playing ? <Pause className="h-7 w-7" /> : <Play className="ml-0.5 h-7 w-7" />}
            </button>
          </div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))]/10 px-2.5 py-1 font-semibold text-[hsl(var(--primary))]"><Mic className="h-3 w-3" /> Weekly podcast</span>
              {ep.duration_min && <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" /> {ep.duration_min} min</span>}
              {ep.published_at && <span>{new Date(ep.published_at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })}</span>}
            </div>
            <h2 className="mt-3 font-display text-2xl font-black leading-tight tracking-tight sm:text-3xl">{ep.title}</h2>
            {ep.description && <p className="mt-3 line-clamp-3 text-muted-foreground">{ep.description}</p>}
            <audio ref={audioRef} src={playlist[idx]} preload="none" onEnded={onEnded}
              onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} className="mt-5 w-full" controls data-testid="featured-podcast-audio" />
            {introUrl && idx === 0 && <p className="mt-1 text-xs text-muted-foreground">Opens with a short music intro, then Sudarshan's episode.</p>}
            <Link to="/podcast" data-testid="featured-podcast-all"
              className="mt-5 inline-flex items-center gap-1.5 text-sm font-semibold text-[hsl(var(--primary))]">
              All episodes <ArrowUpRight className="h-4 w-4" />
            </Link>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
