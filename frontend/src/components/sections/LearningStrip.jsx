import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Sparkles, ArrowUpRight } from "lucide-react";
import api, { track } from "@/lib/api";
import VideoCard from "@/components/VideoCard";

export default function LearningStrip() {
  const [videos, setVideos] = useState([]);

  useEffect(() => {
    api.get("/learning/daily", { params: { limit: 8 } })
      .then((r) => setVideos(r.data.videos || []))
      .catch(() => {});
  }, []);

  if (!videos.length) return null;

  return (
    <section className="border-t border-border bg-secondary/30 py-20 md:py-28" data-testid="home-learning-strip">
      <div className="mx-auto max-w-7xl px-6">
        <div className="flex flex-wrap items-end justify-between gap-6">
          <div className="max-w-2xl">
            <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">
              <Sparkles className="h-3.5 w-3.5" /> Fresh every day
            </span>
            <h2 className="mt-5 font-display text-4xl font-bold leading-tight md:text-5xl">The Curator's Watchlist</h2>
            <p className="mt-4 text-base text-muted-foreground">
              A hand-picked set of the sharpest new videos on the economy, energy, technology and leadership — refreshed daily, so there is always something new to learn.
            </p>
          </div>
          <Link
            to="/learning"
            data-testid="home-learning-viewall"
            className="group inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5"
          >
            Open Learning Hub
            <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </Link>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {videos.map((v) => (
            <VideoCard key={v.video_id} video={v} onPlay={(topic) => track("video", topic)} />
          ))}
        </div>
      </div>
    </section>
  );
}
