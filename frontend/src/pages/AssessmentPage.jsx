import { useEffect, useState } from "react";
import { Compass, Sparkles, AlertTriangle, Flag, ChevronLeft, Info, ArrowUpRight } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";

export default function AssessmentPage() {
  const [items, setItems] = useState([]);
  const [scale, setScale] = useState([]);
  const [credit, setCredit] = useState("");
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [status, setStatus] = useState("intro"); // intro | quiz | loading | done | error

  useEffect(() => { window.scrollTo(0, 0); }, [status]);
  useEffect(() => {
    api.get("/assessment/questions").then((r) => { setItems(r.data.items); setScale(r.data.scale); setCredit(r.data.credit); }).catch(() => {});
  }, []);

  const answered = Object.keys(answers).length;
  const allDone = items.length > 0 && answered === items.length;

  const submit = async () => {
    setStatus("loading");
    try {
      const r = await api.post("/assessment/score", { answers });
      setResult(r.data); setStatus("done");
    } catch { setStatus("error"); }
  };

  const bp = result?.blueprint || {};

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Leadership Blueprint — Discover Your Quadrant | Sudarshan Karweer"
        description="A validated Big Five profile maps you to a leadership quadrant, with your strengths, blind spots and a milestone roadmap from Sudarshan Karweer." />
      <Navbar />

      <section className="border-b border-border bg-secondary/30 pt-28 pb-12 md:pt-32">
        <div className="mx-auto max-w-4xl px-6 lg:px-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">
            <Compass className="h-3.5 w-3.5" /> Leadership Blueprint
          </span>
          <h1 className="mt-6 font-display text-4xl font-bold leading-[1.05] md:text-5xl">Which leader are you?</h1>
          <p className="mt-4 max-w-2xl text-base text-muted-foreground">A short, scientifically-validated Big Five check-in maps you to a leadership quadrant — then I'll draw out your strengths, blind spots and a clear roadmap. 20 quick statements, ~3 minutes.</p>
        </div>
      </section>

      <section className="py-12">
        <div className="mx-auto max-w-4xl px-6 lg:px-10">
          {status === "intro" && (
            <div className="rounded-2xl border border-border bg-card p-8 text-center">
              <p className="text-sm text-muted-foreground">Rate how much each statement describes you. Be honest — there are no right answers.</p>
              <button onClick={() => setStatus("quiz")} data-testid="assessment-start"
                className="mt-6 inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                Start the check-in <ArrowUpRight className="h-4 w-4" />
              </button>
              <p className="mt-4 inline-flex items-start gap-1.5 text-xs text-muted-foreground"><Info className="mt-0.5 h-3.5 w-3.5" /> {credit}</p>
            </div>
          )}

          {status === "quiz" && (
            <div data-testid="assessment-quiz">
              <div className="sticky top-16 z-10 mb-4 rounded-full bg-card/95 p-1 backdrop-blur">
                <div className="h-2 w-full overflow-hidden rounded-full bg-secondary">
                  <div className="h-full rounded-full bg-[hsl(var(--primary))] transition-all" style={{ width: `${(answered / items.length) * 100}%` }} />
                </div>
              </div>
              <div className="space-y-3">
                {items.map((it, idx) => (
                  <div key={it.id} className="rounded-xl border border-border bg-card p-4" data-testid={`q-${it.id}`}>
                    <p className="text-sm font-medium text-foreground">{idx + 1}. {it.text}</p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {scale.map((s, v) => (
                        <button key={v} onClick={() => setAnswers((a) => ({ ...a, [it.id]: v + 1 }))} data-testid={`q-${it.id}-opt-${v + 1}`}
                          className={`rounded-full border px-3 py-1.5 text-xs font-semibold transition-colors ${answers[it.id] === v + 1 ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))]/10 text-[hsl(var(--primary))]" : "border-border text-muted-foreground hover:text-foreground"}`}>
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
              <button onClick={submit} disabled={!allDone} data-testid="assessment-submit"
                className={`mt-6 w-full rounded-full px-6 py-3.5 text-sm font-semibold transition-transform ${allDone ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] hover:-translate-y-0.5" : "cursor-not-allowed bg-secondary text-muted-foreground"}`}>
                {allDone ? "Reveal my Leadership Blueprint" : `Answer all ${items.length} (${answered}/${items.length})`}
              </button>
            </div>
          )}

          {status === "loading" && (
            <div className="grid place-items-center py-24">
              <div className="h-9 w-9 animate-spin rounded-full border-2 border-[hsl(var(--primary))] border-t-transparent" />
              <p className="mt-4 text-sm text-muted-foreground">Reading your profile and drafting your blueprint…</p>
            </div>
          )}

          {status === "error" && <p className="rounded-xl border border-red-500/40 bg-red-500/5 p-4 text-sm text-red-400">Something went wrong. Please try again.</p>}

          {status === "done" && result && (
            <div className="space-y-6" data-testid="assessment-result">
              <div className="rounded-2xl border border-[hsl(var(--primary))]/30 bg-[hsl(var(--primary))]/5 p-7 text-center">
                <p className="text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">Your leadership quadrant</p>
                <h2 className="mt-2 font-display text-3xl font-bold" data-testid="quadrant-name">{result.quadrant.name}</h2>
                <p className="mt-2 text-sm text-muted-foreground">{result.quadrant.tagline}</p>
              </div>

              <div className="grid gap-6 md:grid-cols-2">
                <div className="rounded-2xl border border-border bg-card p-6">
                  <h3 className="font-display text-lg font-bold">Where you sit</h3>
                  <div className="relative mt-4 aspect-square rounded-xl border border-border bg-background">
                    <span className="absolute left-2 top-1/2 -translate-y-1/2 -rotate-90 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">People focus →</span>
                    <span className="absolute bottom-2 left-1/2 -translate-x-1/2 text-[10px] font-semibold uppercase tracking-wide text-muted-foreground">Drive & results →</span>
                    <div className="absolute left-1/2 top-0 h-full w-px bg-border" /><div className="absolute top-1/2 left-0 w-full h-px bg-border" />
                    <div className="absolute h-4 w-4 -translate-x-1/2 translate-y-1/2 rounded-full bg-[hsl(var(--primary))] ring-4 ring-[hsl(var(--primary))]/20"
                      style={{ left: `${result.axes.task}%`, bottom: `${result.axes.people}%` }} data-testid="quadrant-dot" />
                  </div>
                </div>
                <div className="rounded-2xl border border-border bg-card p-6">
                  <h3 className="font-display text-lg font-bold">Your profile</h3>
                  <div className="mt-4 space-y-3">
                    {Object.entries(result.scores).map(([k, v]) => (
                      <div key={k}>
                        <div className="flex justify-between text-xs"><span className="text-muted-foreground">{k}</span><span className="font-semibold text-foreground">{v}</span></div>
                        <div className="mt-1 h-2 overflow-hidden rounded-full bg-secondary"><div className="h-full rounded-full bg-[hsl(var(--primary))]" style={{ width: `${v}%` }} /></div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {bp.narrative && (
                <div className="rounded-2xl border border-border bg-card p-6">
                  <p className="flex items-center gap-1.5 text-xs font-bold text-[hsl(var(--primary))]"><Sparkles className="h-3.5 w-3.5" /> SK's read on your style</p>
                  <p className="mt-2 text-sm leading-relaxed text-foreground">{bp.narrative}</p>
                </div>
              )}

              <div className="grid gap-6 md:grid-cols-2">
                {bp.strengths?.length > 0 && (
                  <div className="rounded-2xl border border-border bg-card p-6">
                    <h3 className="font-display text-lg font-bold">Your strengths</h3>
                    <ul className="mt-3 space-y-2.5">{bp.strengths.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground"><span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[hsl(var(--primary))]" />{s}</li>))}</ul>
                  </div>
                )}
                {bp.blind_spots?.length > 0 && (
                  <div className="rounded-2xl border border-border bg-card p-6">
                    <h3 className="flex items-center gap-1.5 font-display text-lg font-bold"><AlertTriangle className="h-4 w-4 text-amber-500" /> Blind spots</h3>
                    <ul className="mt-3 space-y-3">{bp.blind_spots.map((b, i) => (
                      <li key={i} className="text-sm"><p className="font-semibold text-foreground">{b.spot}</p><p className="text-xs text-muted-foreground">{b.why}</p></li>))}</ul>
                  </div>
                )}
              </div>

              {bp.roadmap?.length > 0 && (
                <div className="rounded-2xl border border-border bg-card p-6">
                  <h3 className="flex items-center gap-1.5 font-display text-lg font-bold"><Flag className="h-4 w-4 text-[hsl(var(--primary))]" /> Your roadmap</h3>
                  <div className="mt-4 space-y-3">
                    {bp.roadmap.map((r, i) => (
                      <div key={i} className="flex gap-4 rounded-xl border border-border bg-background p-4">
                        <span className="flex-shrink-0 rounded-full bg-[hsl(var(--primary))]/12 px-3 py-1 text-xs font-bold text-[hsl(var(--primary))]">{r.horizon}</span>
                        <div><p className="text-sm font-semibold text-foreground">{r.milestone}</p><p className="mt-0.5 text-xs text-muted-foreground">{r.action}</p></div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-border bg-secondary/40 p-6">
                <p className="flex-1 text-sm text-muted-foreground">Want to go deeper on your roadmap? Work through it with Sudarshan directly.</p>
                <a href="/#consult" className="rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))]">Book a coaching session</a>
              </div>
              <p className="inline-flex items-start gap-1.5 text-xs text-muted-foreground"><Info className="mt-0.5 h-3.5 w-3.5" /> {result.credit}</p>
            </div>
          )}
        </div>
      </section>
      <Footer />
    </div>
  );
}
