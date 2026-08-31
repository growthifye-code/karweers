import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Trophy, Medal, Crown, ArrowUpRight, Swords } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";

export default function GamesLeaderboardPage() {
  const [data, setData] = useState(null);
  useEffect(() => {
    window.scrollTo(0, 0);
    api.get("/games/leaderboard/global").then((r) => setData(r.data)).catch(() => setData({ top: [], champions: [] }));
  }, []);

  const rankColor = (r) => r === 1 ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]"
    : r <= 3 ? "bg-[hsl(var(--primary))]/20 text-[hsl(var(--primary))]" : "border border-border text-muted-foreground";

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="War-Room Leaderboard — Top Strategists | Sudarshan Karweer"
        description="The standalone leaderboard ranking the top strategists across all six CXO strategy simulations — plus the reigning champion of each game." />
      <Navbar />
      <section className="border-b border-border bg-secondary/30 pt-28 pb-14 md:pt-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">
            <Trophy className="h-3.5 w-3.5" /> War-Room Leaderboard
          </span>
          <h1 className="mt-6 max-w-4xl font-display text-4xl font-bold leading-[1.05] md:text-6xl">The top <span className="text-[hsl(var(--primary))]">strategists.</span></h1>
          <p className="mt-5 max-w-2xl text-base text-muted-foreground md:text-lg">Ranked by best score across all {data?.games || 6} simulations — a perfect run is {data?.total_possible || 90} points. Play more games and climb.</p>
          <div className="mt-6 flex flex-wrap gap-3">
            <Link to="/games" data-testid="lb-play" className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))]"><Swords className="h-4 w-4" /> Enter the War Room</Link>
          </div>
          {data?.me && (
            <div className="mt-6 inline-flex items-center gap-3 rounded-xl border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/5 px-4 py-3" data-testid="lb-me">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-[hsl(var(--primary))] text-sm font-bold text-[hsl(var(--primary-foreground))]">{data.me.rank}</span>
              <span className="text-sm text-foreground">You, <span className="font-semibold">{data.me.name}</span> — {data.me.total} pts across {data.me.games_played} game{data.me.games_played === 1 ? "" : "s"}</span>
            </div>
          )}
        </div>
      </section>

      <section className="py-14">
        <div className="mx-auto grid max-w-7xl gap-10 px-6 lg:grid-cols-3 lg:px-10">
          {/* Overall ranking */}
          <div className="lg:col-span-2">
            <h2 className="flex items-center gap-2 font-display text-2xl font-bold"><Medal className="h-5 w-5 text-[hsl(var(--primary))]" /> Overall ranking</h2>
            {data?.top?.length ? (
              <ul className="mt-6 divide-y divide-border rounded-2xl border border-border bg-card" data-testid="lb-overall">
                {data.top.map((u) => (
                  <li key={u.rank} className="flex items-center gap-4 px-5 py-4" data-testid={`lb-row-${u.rank}`}>
                    <span className={`grid h-9 w-9 flex-shrink-0 place-items-center rounded-full text-sm font-bold ${rankColor(u.rank)}`}>{u.rank}</span>
                    <div className="flex-1">
                      <p className="font-semibold text-foreground">{u.name}</p>
                      <p className="text-xs text-muted-foreground">{u.games_played} game{u.games_played === 1 ? "" : "s"} played</p>
                    </div>
                    <span className="font-display text-xl font-bold text-[hsl(var(--primary))]">{u.total}<span className="text-sm text-muted-foreground"> / {data.total_possible}</span></span>
                  </li>
                ))}
              </ul>
            ) : (
              <div className="mt-6 rounded-2xl border border-border bg-card p-6" data-testid="lb-empty">
                <p className="text-sm text-muted-foreground">No scores yet — be the first strategist on the board.</p>
                <Link to="/games" className="mt-4 inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))]">Play a game <ArrowUpRight className="h-4 w-4" /></Link>
              </div>
            )}
          </div>

          {/* Champions per game */}
          <div>
            <h2 className="flex items-center gap-2 font-display text-2xl font-bold"><Crown className="h-5 w-5 text-[hsl(var(--primary))]" /> Reigning champions</h2>
            <ul className="mt-6 space-y-3" data-testid="lb-champions">
              {(data?.champions || []).map((c) => (
                <Link key={c.slug} to={`/games/${c.slug}`} className="group block rounded-xl border border-border bg-card p-4 transition-colors hover:border-[hsl(var(--primary))]/50" data-testid={`champ-${c.slug}`}>
                  <p className="text-[10px] font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">{c.tag}</p>
                  <p className="mt-1 font-display text-base font-bold group-hover:text-[hsl(var(--primary))]">{c.title}</p>
                  {c.name ? (
                    <p className="mt-1 text-sm text-muted-foreground">👑 {c.name} · <span className="font-semibold text-foreground">{c.score}/{c.max_score}</span></p>
                  ) : (
                    <p className="mt-1 text-sm text-muted-foreground">No champion yet — claim the crown</p>
                  )}
                </Link>
              ))}
            </ul>
          </div>
        </div>
      </section>
      <Footer />
    </div>
  );
}
