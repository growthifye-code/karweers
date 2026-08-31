import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ShieldCheck, ChevronDown, Check } from "lucide-react";

const COOKIE_GROUPS = [
  {
    key: "essential",
    title: "Strictly necessary",
    always: true,
    items: [
      "Authentication session (keeps you securely signed in)",
      "Your cookie consent choice",
      "Security & bot protection (hCaptcha)",
    ],
  },
  {
    key: "personalisation",
    title: "Analytics & personalisation",
    always: false,
    items: [
      "Pages you view and services you explore",
      "Learning videos you play and topics you filter",
      "Declared interests — used to tailor recommendations & relevant blogs",
    ],
  },
];

export default function ConsentBanner() {
  const [show, setShow] = useState(false);
  const [details, setDetails] = useState(false);

  useEffect(() => {
    try { if (!localStorage.getItem("sk_consent")) setShow(true); } catch {}
  }, []);

  const choose = (v) => {
    try { localStorage.setItem("sk_consent", v); } catch {}
    setShow(false);
  };

  if (!show) return null;

  return (
    <div data-testid="consent-banner" className="fixed inset-x-0 bottom-0 z-[70] px-4 pb-4">
      <div className="mx-auto max-w-4xl rounded-2xl border border-border bg-card/95 p-5 shadow-2xl backdrop-blur">
        <div className="flex flex-col gap-4 md:flex-row md:items-center">
          <ShieldCheck className="h-6 w-6 shrink-0 text-[hsl(var(--primary))]" />
          <p className="flex-1 text-sm text-muted-foreground">
            We use cookies to run the site and, with your consent, to track your activity and personalise your learning
            and recommendations. See our <Link to="/privacy" className="font-semibold text-[hsl(var(--primary))] underline">Privacy Policy</Link>.
          </p>
          <div className="flex shrink-0 flex-wrap gap-3">
            <button onClick={() => setDetails((d) => !d)} data-testid="consent-details-toggle"
              className="inline-flex items-center gap-1 rounded-full border border-border px-4 py-2.5 text-sm font-medium hover:bg-secondary">
              What we collect <ChevronDown className={`h-4 w-4 transition-transform ${details ? "rotate-180" : ""}`} />
            </button>
            <button onClick={() => choose("declined")} data-testid="consent-decline"
              className="rounded-full border border-border px-5 py-2.5 text-sm font-medium hover:bg-secondary">Essential only</button>
            <button onClick={() => choose("accepted")} data-testid="consent-accept"
              className="rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">Accept all</button>
          </div>
        </div>

        {details && (
          <div className="mt-5 grid gap-4 border-t border-border pt-5 sm:grid-cols-2" data-testid="consent-details">
            {COOKIE_GROUPS.map((g) => (
              <div key={g.key} className="rounded-xl border border-border bg-background/60 p-4">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold">{g.title}</p>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide ${g.always ? "bg-secondary text-muted-foreground" : "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]"}`}>
                    {g.always ? "Always on" : "Optional"}
                  </span>
                </div>
                <ul className="mt-3 space-y-1.5">
                  {g.items.map((it) => (
                    <li key={it} className="flex gap-2 text-xs text-muted-foreground">
                      <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[hsl(var(--primary))]" /> {it}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            <p className="text-xs text-muted-foreground sm:col-span-2">
              "Essential only" runs just the strictly necessary cookies — no activity tracking. You can change this anytime by clearing your choice, and signed-in clients can export or delete their data from the dashboard.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
