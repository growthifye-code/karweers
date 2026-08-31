import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Logo } from "@/components/Navbar";
import ThemeToggle from "@/components/ThemeToggle";
import VideoCard from "@/components/VideoCard";
import api, { track } from "@/lib/api";
import { Sparkles, Calendar, BookOpen, GraduationCap, ArrowUpRight } from "lucide-react";

export default function ClientDashboard() {
  const { user, logout } = useAuth();
  const [recommended, setRecommended] = useState([]);
  const [personalised, setPersonalised] = useState(false);

  const loadRecs = () => {
    api.get("/learning/recommended", { params: { limit: 4 } })
      .then((r) => { setRecommended(r.data.videos || []); setPersonalised(r.data.personalised); })
      .catch(() => {});
  };
  useEffect(() => { loadRecs(); }, []);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo />
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">View site</Link>
            <button onClick={logout} data-testid="client-logout" className="rounded-full border border-border px-4 py-2 text-sm font-medium hover:bg-secondary">Logout</button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-14">
        <div className="flex items-center gap-4">
          {user?.picture && <img src={user.picture} alt={user.name} className="h-12 w-12 rounded-full border border-border object-cover" />}
          <div>
            <p className="text-sm text-muted-foreground">Client Portal</p>
            <h1 className="mt-1 font-display text-3xl font-bold">Welcome, {user?.name} 👋</h1>
          </div>
        </div>
        <p className="mt-3 text-muted-foreground">Your space for curated learning, insights, consultations and the Karweer AI engine.</p>

        <div className="mt-10 grid gap-6 md:grid-cols-3">
          <Link to="/learning" className="group rounded-2xl border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/5 p-8 transition-transform hover:-translate-y-1" data-testid="client-learning">
            <GraduationCap className="h-8 w-8 text-[hsl(var(--primary))]" />
            <h3 className="mt-4 font-display text-lg font-bold">Learning Hub</h3>
            <p className="mt-2 text-sm text-muted-foreground">Best-in-class videos on economy, energy, AI & leadership — curated & always fresh.</p>
          </Link>
          <Link to="/#consult" className="group rounded-2xl border border-border bg-card p-8 transition-transform hover:-translate-y-1" data-testid="client-book">
            <Calendar className="h-8 w-8 text-[hsl(var(--accent))]" />
            <h3 className="mt-4 font-display text-lg font-bold">Book a Consultation</h3>
            <p className="mt-2 text-sm text-muted-foreground">Request a premium 1:1 strategic session with Sudarshan.</p>
          </Link>
          <Link to="/insights" className="group rounded-2xl border border-border bg-card p-8 transition-transform hover:-translate-y-1" data-testid="client-insights">
            <BookOpen className="h-8 w-8 text-[hsl(var(--primary))]" />
            <h3 className="mt-4 font-display text-lg font-bold">Explore Insights</h3>
            <p className="mt-2 text-sm text-muted-foreground">News, analysis, R&D and case studies across the energy transition.</p>
          </Link>
        </div>

        {recommended.length > 0 && (
          <section className="mt-16" data-testid="dashboard-recommended">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-[hsl(var(--primary))]" />
                <h2 className="font-display text-2xl font-bold">Recommended for you</h2>
              </div>
              <Link to="/learning" className="group inline-flex items-center gap-1.5 text-sm font-semibold text-[hsl(var(--primary))]">
                View all <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
              </Link>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              {personalised ? "Based on what you've been exploring across the platform." : "Play a few videos and browse services — this personalises to you."}
            </p>
            <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {recommended.map((v) => (
                <VideoCard key={v.video_id} video={v} onPlay={(topic) => { track("video", topic); setTimeout(loadRecs, 800); }} />
              ))}
            </div>
          </section>
        )}

        <div className="mt-16 rounded-2xl border border-border bg-card p-8">
          <Sparkles className="h-8 w-8 text-[hsl(var(--accent))]" />
          <h3 className="mt-4 font-display text-lg font-bold">Karweer AI</h3>
          <p className="mt-2 text-sm text-muted-foreground">Use the AI engine (bottom-right) for instant advisory intelligence.</p>
        </div>
      </main>
    </div>
  );
}
