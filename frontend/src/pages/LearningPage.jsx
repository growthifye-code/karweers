import { useEffect, useState, useCallback } from "react";
import { GraduationCap, Sparkles } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import VideoCard from "@/components/VideoCard";
import { useAuth } from "@/context/AuthContext";
import api, { track } from "@/lib/api";

export default function LearningPage() {
  const { user } = useAuth();
  const [topics, setTopics] = useState([]);
  const [active, setActive] = useState("all");
  const [videos, setVideos] = useState([]);
  const [recommended, setRecommended] = useState([]);
  const [personalised, setPersonalised] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => { window.scrollTo(0, 0); }, []);

  useEffect(() => {
    api.get("/learning/topics").then((r) => setTopics(r.data || [])).catch(() => {});
  }, []);

  const loadRecommended = useCallback(() => {
    if (!user) { setRecommended([]); return; }
    api.get("/learning/recommended", { params: { limit: 8 } })
      .then((r) => { setRecommended(r.data.videos || []); setPersonalised(r.data.personalised); })
      .catch(() => {});
  }, [user]);

  useEffect(() => { loadRecommended(); }, [loadRecommended]);

  useEffect(() => {
    setLoading(true);
    const params = { limit: 60 };
    if (active !== "all") params.topic = active;
    api.get("/learning/videos", { params })
      .then((r) => setVideos(r.data.videos || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [active]);

  const onPlay = (topic) => { track("video", topic); if (user) setTimeout(loadRecommended, 800); };
  const selectTopic = (id) => { setActive(id); if (id !== "all") track("topic", id); };

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Learning Hub — Curated Economy, Energy & AI Videos | Sudarshan Karweer"
        description="A curated, always-fresh library of the best videos on global & India economy, energy transition, climate finance, AI, technology, fundraising and leadership." />
      <Navbar />

      <section className="border-b border-border bg-secondary/30 py-16 md:py-24">
        <div className="mx-auto max-w-7xl px-6">
          <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">
            <GraduationCap className="h-3.5 w-3.5" /> Learning Hub
          </span>
          <h1 className="mt-6 max-w-3xl font-display text-5xl font-bold leading-[1.05] md:text-6xl">
            Best-in-class ideas, <span className="text-[hsl(var(--primary))]">curated for you.</span>
          </h1>
          <p className="mt-5 max-w-2xl text-base text-muted-foreground md:text-lg">
            Hand-picked videos from the world's leading institutions on the economy, energy, climate finance, AI, technology, fundraising and leadership — always fresh, always relevant. All videos are embedded with full credit to their original creators.
          </p>
        </div>
      </section>

      {user && recommended.length > 0 && (
        <section className="border-b border-border py-14" data-testid="learning-recommended">
          <div className="mx-auto max-w-7xl px-6">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-[hsl(var(--primary))]" />
              <h2 className="font-display text-2xl font-bold">Recommended for you</h2>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              {personalised
                ? "Tuned to what you've been exploring across the platform — the more you browse and watch, the sharper this gets."
                : "A great starting set. Browse services and play a few videos and this will personalise to your interests."}
            </p>
            <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {recommended.map((v) => (
                <VideoCard key={`rec-${v.video_id}`} video={v} onPlay={onPlay} />
              ))}
            </div>
          </div>
        </section>
      )}

      <section className="py-14">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex flex-wrap gap-2" data-testid="learning-topic-filters">
            <button
              onClick={() => selectTopic("all")}
              data-testid="topic-all"
              className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${active === "all" ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border-border text-muted-foreground hover:border-[hsl(var(--primary))]/50 hover:text-foreground"}`}
            >
              All topics
            </button>
            {topics.map((t) => (
              <button
                key={t.id}
                onClick={() => selectTopic(t.id)}
                data-testid={`topic-${t.id}`}
                className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${active === t.id ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border-border text-muted-foreground hover:border-[hsl(var(--primary))]/50 hover:text-foreground"}`}
              >
                {t.label}
              </button>
            ))}
          </div>

          {loading ? (
            <div className="mt-16 grid place-items-center py-20 text-muted-foreground">
              <div className="h-8 w-8 animate-spin rounded-full border-2 border-[hsl(var(--primary))] border-t-transparent" />
            </div>
          ) : (
            <div className="mt-10 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4" data-testid="learning-grid">
              {videos.map((v) => (
                <VideoCard key={v.video_id} video={v} onPlay={onPlay} />
              ))}
            </div>
          )}
          {!loading && videos.length === 0 && (
            <p className="mt-16 text-center text-muted-foreground">No videos available right now. Please check back shortly.</p>
          )}
        </div>
      </section>

      <Footer />
    </div>
  );
}
