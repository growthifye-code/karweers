import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { ChevronLeft, CheckCircle2, XCircle, Trophy, RotateCcw, ArrowRight, Sparkles, MessageSquare, Medal, LogIn } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import { useAuth } from "@/context/AuthContext";
import api, { track } from "@/lib/api";

export default function GamePlayPage() {
  const { slug } = useParams();
  const { user } = useAuth();
  const [game, setGame] = useState(null);
  const [started, setStarted] = useState(false);
  const [idx, setIdx] = useState(0);
  const [answers, setAnswers] = useState({});
  const [picked, setPicked] = useState(null);       // option id chosen for current round (locked)
  const [result, setResult] = useState(null);        // final debrief
  const [board, setBoard] = useState(null);          // leaderboard

  useEffect(() => { window.scrollTo(0, 0); }, [slug, started, idx, result]);
  useEffect(() => {
    api.get(`/games/${slug}`).then((r) => { setGame(r.data); track("game", slug); }).catch(() => setGame(false));
  }, [slug]);

  if (game === false) return (
    <div className="min-h-screen bg-background text-foreground"><Navbar />
      <div className="grid place-items-center py-40 text-center"><h1 className="font-display text-3xl font-bold">Game not found</h1>
        <Link to="/games" className="mt-6 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))]">Back to War Room</Link></div><Footer /></div>
  );

  const round = game?.rounds?.[idx];
  const chosenOpt = round?.options?.find((o) => o.id === picked);
  const isLast = game && idx === game.rounds.length - 1;

  const choose = (optId) => {
    if (picked) return;
    setPicked(optId);
    setAnswers((a) => ({ ...a, [round.id]: optId }));
  };

  const next = async () => {
    if (isLast) {
      const r = await api.post(`/games/${slug}/score`, { answers: { ...answers, [round.id]: picked } });
      setResult(r.data);
      api.get(`/games/${slug}/leaderboard`).then((lb) => setBoard(lb.data)).catch(() => {});
    } else {
      setIdx((i) => i + 1);
      setPicked(null);
    }
  };

  const restart = () => { setStarted(true); setIdx(0); setAnswers({}); setPicked(null); setResult(null); setBoard(null); };

  const bandColor = (band) => band === "high" ? "text-[hsl(var(--primary))]" : band === "mid" ? "text-amber-400" : "text-rose-400";

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title={game ? `${game.title} — Strategy Simulation | Sudarshan Karweer` : "Loading…"} description={game?.blurb} />
      <Navbar />
      <section className="border-b border-border bg-secondary/30 pt-28 pb-10 md:pt-32">
        <div className="mx-auto max-w-3xl px-6 lg:px-10">
          <Link to="/games" data-testid="game-back" className="inline-flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground"><ChevronLeft className="h-4 w-4" /> War Room</Link>
          {game && (
            <>
              <span className="mt-6 inline-flex items-center rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">{game.framework}</span>
              <h1 className="mt-4 font-display text-3xl font-bold md:text-5xl" data-testid="game-title">{game.title}</h1>
              {!started && !result && <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted-foreground">{game.intro}</p>}
            </>
          )}
        </div>
      </section>

      {game && (
        <section className="py-10">
          <div className="mx-auto max-w-3xl px-6 lg:px-10">

            {/* Intro / Start */}
            {!started && !result && (
              <button onClick={() => setStarted(true)} data-testid="game-start"
                className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                Start the simulation <ArrowRight className="h-4 w-4" />
              </button>
            )}

            {/* Play */}
            {started && !result && round && (
              <div data-testid="game-round">
                <div className="mb-6 flex items-center gap-3">
                  <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-secondary">
                    <div className="h-full rounded-full bg-[hsl(var(--primary))] transition-all" style={{ width: `${((idx + (picked ? 1 : 0)) / game.rounds.length) * 100}%` }} />
                  </div>
                  <span className="text-xs font-semibold text-muted-foreground">{idx + 1} / {game.rounds.length}</span>
                </div>

                <div className="rounded-2xl border border-border bg-card p-6">
                  <p className="text-sm leading-relaxed text-muted-foreground">{round.situation}</p>
                  <h2 className="mt-3 font-display text-xl font-bold" data-testid="game-question">{round.question}</h2>
                  <div className="mt-5 space-y-3">
                    {round.options.map((o) => {
                      const isPicked = picked === o.id;
                      const locked = !!picked;
                      const good = o.score >= round.options.reduce((m, x) => Math.max(m, x.score), 0);
                      return (
                        <button key={o.id} onClick={() => choose(o.id)} disabled={locked} data-testid={`game-option-${o.id}`}
                          className={`flex w-full items-start gap-3 rounded-xl border p-4 text-left text-sm transition-all ${
                            !locked ? "border-border hover:border-[hsl(var(--primary))]/60 hover:bg-secondary/40" :
                            isPicked ? (good ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))]/10" : "border-rose-500/50 bg-rose-500/5") :
                            good ? "border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/5" : "border-border opacity-60"}`}>
                          <span className="mt-0.5 grid h-5 w-5 flex-shrink-0 place-items-center rounded-full border border-current text-[11px] font-bold">{o.id.toUpperCase()}</span>
                          <span className="flex-1 text-foreground/90">{o.text}</span>
                          {locked && (isPicked || good) && (good ? <CheckCircle2 className="h-5 w-5 flex-shrink-0 text-[hsl(var(--primary))]" /> : isPicked ? <XCircle className="h-5 w-5 flex-shrink-0 text-rose-400" /> : null)}
                        </button>
                      );
                    })}
                  </div>

                  {picked && (
                    <div className="mt-5 rounded-xl border border-[hsl(var(--primary))]/30 bg-[hsl(var(--primary))]/5 p-4" data-testid="game-feedback">
                      <p className="flex items-center gap-1.5 text-xs font-bold text-[hsl(var(--primary))]"><Sparkles className="h-3.5 w-3.5" /> Debrief</p>
                      <p className="mt-2 text-sm text-foreground">{chosenOpt?.feedback}</p>
                    </div>
                  )}
                </div>

                {picked && (
                  <button onClick={next} data-testid="game-next"
                    className="mt-6 inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                    {isLast ? "See my results" : "Next decision"} <ArrowRight className="h-4 w-4" />
                  </button>
                )}
              </div>
            )}

            {/* Result */}
            {result && (
              <div data-testid="game-result">
                <div className="rounded-2xl border border-border bg-card p-7 text-center">
                  <Trophy className={`mx-auto h-10 w-10 ${bandColor(result.band)}`} />
                  <p className="mt-4 text-5xl font-bold" data-testid="game-score"><span className={bandColor(result.band)}>{result.score}</span><span className="text-muted-foreground text-2xl"> / {result.max_score}</span></p>
                  <h2 className={`mt-3 font-display text-2xl font-bold ${bandColor(result.band)}`}>{result.title}</h2>
                  <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-muted-foreground">{result.note}</p>
                </div>

                <div className="mt-6 rounded-2xl border border-border bg-card p-6">
                  <h3 className="font-display text-lg font-bold">Key lessons — {result.framework}</h3>
                  <ul className="mt-3 space-y-2.5">
                    {result.lessons.map((l, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground"><span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[hsl(var(--primary))]" />{l}</li>
                    ))}
                  </ul>
                </div>

                {/* Leaderboard */}
                <div className="mt-6 rounded-2xl border border-border bg-card p-6" data-testid="game-leaderboard">
                  <h3 className="flex items-center gap-2 font-display text-lg font-bold"><Medal className="h-5 w-5 text-[hsl(var(--primary))]" /> Top scores</h3>
                  {user ? (
                    <p className="mt-1 text-xs text-muted-foreground" data-testid="game-mybest">
                      {result.saved ? "Run saved. " : ""}Your best: <span className="font-semibold text-[hsl(var(--primary))]">{board?.my_best ?? result.score}/{result.max_score}</span> · {board?.plays ?? 1} play{(board?.plays ?? 1) === 1 ? "" : "s"}
                    </p>
                  ) : (
                    <div className="mt-3 flex flex-wrap items-center gap-3 rounded-xl border border-[hsl(var(--primary))]/30 bg-[hsl(var(--primary))]/5 p-3" data-testid="game-login-prompt">
                      <LogIn className="h-4 w-4 text-[hsl(var(--primary))]" />
                      <span className="text-sm text-foreground">Sign in to save your score and join the leaderboard.</span>
                      <Link to="/login" className="ml-auto rounded-full bg-[hsl(var(--primary))] px-4 py-1.5 text-xs font-semibold text-[hsl(var(--primary-foreground))]">Sign in</Link>
                    </div>
                  )}
                  {board?.top?.length ? (
                    <ul className="mt-4 divide-y divide-border">
                      {board.top.map((t) => (
                        <li key={t.rank} className="flex items-center gap-3 py-2.5 text-sm" data-testid={`leaderboard-row-${t.rank}`}>
                          <span className={`grid h-6 w-6 flex-shrink-0 place-items-center rounded-full text-[11px] font-bold ${t.rank <= 3 ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border border-border text-muted-foreground"}`}>{t.rank}</span>
                          <span className="flex-1 font-medium text-foreground">{t.name}</span>
                          <span className="text-xs text-muted-foreground">{t.date}</span>
                          <span className="font-semibold text-[hsl(var(--primary))]">{t.score}/{t.max_score}</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="mt-4 text-sm text-muted-foreground">Be the first on the board — sign in and play.</p>
                  )}
                </div>

                <div className="mt-6 flex flex-wrap gap-3">
                  <button onClick={restart} data-testid="game-replay"
                    className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                    <RotateCcw className="h-4 w-4" /> Play again
                  </button>
                  <Link to={`/?area=Business%20Coaching&msg=${encodeURIComponent(`I just played the "${game.title}" strategy simulation (${result.framework}). I'd like to discuss applying these ideas in my business.`)}#consult`}
                    data-testid="game-discuss-sk"
                    className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary))] transition-colors hover:bg-[hsl(var(--primary))]/10">
                    <MessageSquare className="h-4 w-4" /> Discuss this with SK
                  </Link>
                  <Link to="/games" className="inline-flex items-center gap-2 rounded-full border border-border px-6 py-3 text-sm font-semibold text-foreground transition-colors hover:border-[hsl(var(--primary))]">
                    Try another game
                  </Link>
                </div>
              </div>
            )}
          </div>
        </section>
      )}
      <Footer />
    </div>
  );
}
