import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck } from "lucide-react";

export default function ConsentBanner() {
  const [show, setShow] = useState(false);

  useEffect(() => {
    try { if (!localStorage.getItem("sk_consent")) setShow(true); } catch {}
  }, []);

  const choose = (v) => {
    try { localStorage.setItem("sk_consent", v); } catch {}
    setShow(false);
  };

  if (!show) return null;

  return (
    <div data-testid="consent-banner" className="fixed inset-x-0 bottom-0 z-[60] px-4 pb-4">
      <div className="mx-auto flex max-w-4xl flex-col gap-4 rounded-2xl border border-border bg-card/95 p-5 shadow-2xl backdrop-blur md:flex-row md:items-center">
        <ShieldCheck className="h-6 w-6 shrink-0 text-[hsl(var(--primary))]" />
        <p className="flex-1 text-sm text-muted-foreground">
          We use essential cookies to run the site and, with your consent, track your activity to personalise your learning and recommendations.
          See our <Link to="/privacy" className="font-semibold text-[hsl(var(--primary))] underline">Privacy Policy</Link>.
        </p>
        <div className="flex shrink-0 gap-3">
          <button onClick={() => choose("declined")} data-testid="consent-decline"
            className="rounded-full border border-border px-5 py-2.5 text-sm font-medium hover:bg-secondary">Decline</button>
          <button onClick={() => choose("accepted")} data-testid="consent-accept"
            className="rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">Accept</button>
        </div>
      </div>
    </div>
  );
}
