import { useEffect, useState, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { CheckCircle2, XCircle, Loader2, CalendarCheck } from "lucide-react";
import { Logo } from "@/components/Navbar";
import api from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";

const MAX_TRIES = 20;
const TIMES = ["09:00", "10:00", "11:00", "14:00", "15:00", "16:00", "17:00"];

function nextDays(n) {
  const out = [];
  const d = new Date();
  for (let i = 1; i <= n; i++) {
    const day = new Date(d);
    day.setDate(d.getDate() + i);
    out.push(day);
  }
  return out;
}

export default function PaymentSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [state, setState] = useState("checking");
  const [info, setInfo] = useState(null);
  const [scheduled, setScheduled] = useState(false);
  const [date, setDate] = useState("");
  const [tslot, setTslot] = useState(TIMES[0]);
  const [busy, setBusy] = useState(false);
  const tries = useRef(0);

  useEffect(() => {
    if (!sessionId) { setState("error"); return; }
    let cancelled = false;
    const poll = async () => {
      if (cancelled) return;
      if (tries.current >= MAX_TRIES) { setState("timeout"); return; }
      tries.current += 1;
      try {
        const { data } = await api.get(`/payments/status/${sessionId}`);
        if (data.payment_status === "paid") { setInfo(data); setState("paid"); return; }
        if (data.status === "expired" || data.payment_status === "failed") { setState("error"); return; }
        setTimeout(poll, 2000);
      } catch { setTimeout(poll, 2000); }
    };
    poll();
    return () => { cancelled = true; };
  }, [sessionId]);

  const days = nextDays(10);

  const confirmSlot = async () => {
    if (!date) { toast.error("Please choose a date."); return; }
    setBusy(true);
    try {
      const start = new Date(`${date}T${tslot}:00`);
      const end = new Date(start.getTime() + 60 * 60 * 1000);
      const { data } = await api.post("/bookings/schedule", {
        session_id: sessionId, start: start.toISOString(), end: end.toISOString(),
      });
      toast.success(data.message || "Scheduled!");
      setScheduled(true);
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Could not schedule.");
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border"><div className="mx-auto max-w-6xl px-6 py-4"><Logo /></div></header>
      <div className="mx-auto max-w-xl px-6 py-24 text-center" data-testid="payment-success">
        {state === "checking" && (<><Loader2 className="mx-auto h-14 w-14 animate-spin text-[hsl(var(--primary))]" /><h1 className="mt-6 font-display text-3xl font-bold">Confirming your payment…</h1></>)}
        {state === "paid" && !scheduled && (
          <>
            <CheckCircle2 className="mx-auto h-16 w-16 text-[hsl(var(--primary))]" />
            <h1 className="mt-6 font-display text-3xl font-bold">Payment confirmed!</h1>
            <p className="mt-3 text-muted-foreground">Now pick a slot for your session{info?.amount ? ` ($${info.amount})` : ""}. We'll email a calendar invite.</p>
            <div className="mt-8 rounded-2xl border border-border bg-card p-6 text-left" data-testid="scheduler">
              <label className="text-sm font-medium">Choose a date</label>
              <div className="mt-3 flex flex-wrap gap-2">
                {days.map((d) => {
                  const iso = d.toISOString().slice(0, 10);
                  return (
                    <button key={iso} onClick={() => setDate(iso)} data-testid={`slot-date-${iso}`}
                      className={`rounded-xl border px-3 py-2 text-xs ${date === iso ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border-border hover:bg-secondary"}`}>
                      {d.toLocaleDateString(undefined, { weekday: "short", day: "numeric", month: "short" })}
                    </button>
                  );
                })}
              </div>
              <label className="mt-5 block text-sm font-medium">Choose a time (local)</label>
              <select value={tslot} onChange={(e) => setTslot(e.target.value)} data-testid="slot-time" className="mt-3 w-full rounded-lg border border-border bg-background px-4 py-3 text-sm">
                {TIMES.map((t) => <option key={t} value={t}>{t}</option>)}
              </select>
              <button onClick={confirmSlot} disabled={busy} data-testid="confirm-slot" className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[hsl(var(--accent))] px-6 py-3.5 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
                {busy ? "Scheduling…" : <>Confirm slot <CalendarCheck className="h-4 w-4" /></>}
              </button>
            </div>
          </>
        )}
        {state === "paid" && scheduled && (
          <><CalendarCheck className="mx-auto h-16 w-16 text-[hsl(var(--primary))]" /><h1 className="mt-6 font-display text-3xl font-bold">You're all set!</h1><p className="mt-3 text-muted-foreground">Your session is booked. A calendar invite is on its way to your inbox.</p><Link to="/" className="mt-8 inline-block rounded-full bg-[hsl(var(--accent))] px-6 py-3 font-semibold text-[hsl(var(--accent-foreground))]">Back to home</Link></>
        )}
        {state === "timeout" && (<><Loader2 className="mx-auto h-14 w-14 text-muted-foreground" /><h1 className="mt-6 font-display text-3xl font-bold">Still processing</h1><p className="mt-3 text-muted-foreground">If your payment succeeded, you'll get an email shortly.</p><Link to="/" className="mt-8 inline-block rounded-full border border-border px-6 py-3 font-semibold">Back to home</Link></>)}
        {state === "error" && (<><XCircle className="mx-auto h-16 w-16 text-[hsl(var(--destructive))]" /><h1 className="mt-6 font-display text-3xl font-bold">Something went wrong</h1><p className="mt-3 text-muted-foreground">We couldn't confirm this payment.</p><Link to="/#consult" className="mt-8 inline-block rounded-full bg-[hsl(var(--accent))] px-6 py-3 font-semibold text-[hsl(var(--accent-foreground))]">Try again</Link></>)}
      </div>
    </div>
  );
}
