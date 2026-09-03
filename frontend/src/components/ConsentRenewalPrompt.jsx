import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ShieldCheck, X } from "lucide-react";
import ConsentGate from "@/components/ConsentGate";
import api from "@/lib/api";

// Shown to signed-in clients when their consent is missing, withdrawn, or predates
// the current policy version — asks them to re-agree.
export default function ConsentRenewalPrompt() {
  const [open, setOpen] = useState(false);
  const [version, setVersion] = useState("");
  const [agreed, setAgreed] = useState(false);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/me/consent")
      .then((r) => { if (r.data?.needs_renewal) { setOpen(true); setVersion(r.data.policy_version || ""); } })
      .catch(() => {});
  }, []);

  const confirm = async () => {
    if (!agreed) return;
    setBusy(true);
    try {
      await api.post("/me/consent/renew");
      toast.success("Thank you — your agreement has been updated.");
      setOpen(false);
    } catch {
      toast.error("Could not save your agreement. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 p-4 backdrop-blur-sm" data-testid="consent-renewal">
      <div className="relative w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl">
        <button onClick={() => setOpen(false)} data-testid="consent-renewal-later"
          className="absolute right-4 top-4 text-muted-foreground transition-colors hover:text-foreground" aria-label="Remind me later">
          <X className="h-5 w-5" />
        </button>
        <div className="flex items-center gap-2 text-[hsl(var(--primary))]">
          <ShieldCheck className="h-5 w-5" />
          <span className="text-xs font-semibold uppercase tracking-[0.2em]">Updated terms</span>
        </div>
        <h2 className="mt-3 font-display text-2xl font-bold">Please review & re-agree</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          We've updated our Terms &amp; Conditions and Privacy Policy{version ? <> (version {version})</> : null}.
          Please tick to confirm your agreement to continue with full access.
        </p>
        <div className="mt-5">
          <ConsentGate agreed={agreed} setAgreed={setAgreed} />
        </div>
        <div className="mt-5 flex items-center justify-end gap-3">
          <button onClick={() => setOpen(false)} data-testid="consent-renewal-dismiss"
            className="rounded-full px-4 py-2.5 text-sm font-medium text-muted-foreground hover:text-foreground">Remind me later</button>
          <button onClick={confirm} disabled={!agreed || busy} data-testid="consent-renewal-confirm"
            className="rounded-full bg-[hsl(var(--primary))] px-6 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
            {busy ? "Saving…" : "I agree"}
          </button>
        </div>
      </div>
    </div>
  );
}
