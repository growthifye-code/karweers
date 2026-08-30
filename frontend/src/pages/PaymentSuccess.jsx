import { useEffect, useState, useRef } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { Logo } from "@/components/Navbar";
import api from "@/lib/api";

const MAX_TRIES = 20;

export default function PaymentSuccess() {
  const [params] = useSearchParams();
  const sessionId = params.get("session_id");
  const [state, setState] = useState("checking"); // checking | paid | timeout | error
  const [info, setInfo] = useState(null);
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
      } catch {
        setTimeout(poll, 2000);
      }
    };
    poll();
    return () => { cancelled = true; };
  }, [sessionId]);

  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto max-w-6xl px-6 py-4"><Logo /></div>
      </header>
      <div className="mx-auto grid max-w-lg place-items-center px-6 py-32 text-center" data-testid="payment-success">
        {state === "checking" && (<><Loader2 className="h-14 w-14 animate-spin text-[hsl(var(--primary))]" /><h1 className="mt-6 font-display text-3xl font-bold">Confirming your payment…</h1><p className="mt-3 text-muted-foreground">Please hold on a moment.</p></>)}
        {state === "paid" && (<><CheckCircle2 className="h-16 w-16 text-[hsl(var(--primary))]" /><h1 className="mt-6 font-display text-3xl font-bold">Booking confirmed!</h1><p className="mt-3 text-muted-foreground">Thank you — your consultation{info?.amount ? ` ($${info.amount})` : ""} is reserved. Sudarshan's team will email you to schedule the session.</p><Link to="/" className="mt-8 rounded-full bg-[hsl(var(--accent))] px-6 py-3 font-semibold text-[hsl(var(--accent-foreground))]">Back to home</Link></>)}
        {state === "timeout" && (<><Loader2 className="h-14 w-14 text-muted-foreground" /><h1 className="mt-6 font-display text-3xl font-bold">Still processing</h1><p className="mt-3 text-muted-foreground">Your payment is being confirmed. If it was successful, you'll receive an email shortly.</p><Link to="/" className="mt-8 rounded-full border border-border px-6 py-3 font-semibold">Back to home</Link></>)}
        {state === "error" && (<><XCircle className="h-16 w-16 text-[hsl(var(--destructive))]" /><h1 className="mt-6 font-display text-3xl font-bold">Something went wrong</h1><p className="mt-3 text-muted-foreground">We couldn't confirm this payment. Please try again or contact us.</p><Link to="/#consult" className="mt-8 rounded-full bg-[hsl(var(--accent))] px-6 py-3 font-semibold text-[hsl(var(--accent-foreground))]">Try again</Link></>)}
      </div>
    </div>
  );
}
