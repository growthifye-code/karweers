import { useState } from "react";
import { X } from "lucide-react";
import { DOCS } from "@/pages/LegalPage";

// Consent: a single simple tick confirms agreement. Terms & Privacy are inline
// links that optionally open in an in-page modal (no reading required to proceed).
export default function ConsentGate({ agreed, setAgreed }) {
  const [activeDoc, setActiveDoc] = useState(null); // "terms" | "privacy" | null
  const openDoc = (key) => setActiveDoc(key);
  const doc = activeDoc ? DOCS[activeDoc] : null;

  return (
    <div data-testid="consent-gate">
      <label className="flex items-start gap-2.5 text-xs cursor-pointer text-foreground">
        <input type="checkbox" data-testid="consent-checkbox"
          checked={agreed} onChange={(e) => setAgreed(e.target.checked)}
          className="mt-0.5 h-4 w-4 shrink-0 accent-[hsl(var(--primary))]" />
        <span>
          I have read and agree to the{" "}
          <button type="button" data-testid="consent-open-terms" onClick={() => openDoc("terms")} className="font-semibold text-[hsl(var(--primary))] underline">Terms &amp; Conditions</button>{" "}and{" "}
          <button type="button" data-testid="consent-open-privacy" onClick={() => openDoc("privacy")} className="font-semibold text-[hsl(var(--primary))] underline">Privacy Policy</button>.
        </span>
      </label>

      {doc && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center p-4" data-testid="consent-doc-modal">
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setActiveDoc(null)} />
          <div className="relative z-10 max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-border bg-card p-6 shadow-2xl">
            <button type="button" onClick={() => setActiveDoc(null)} data-testid="consent-doc-close"
              className="absolute right-4 top-4 grid h-8 w-8 place-items-center rounded-full border border-border text-muted-foreground hover:bg-secondary">
              <X className="h-4 w-4" />
            </button>
            <h2 className="pr-10 font-display text-2xl font-bold">{doc.title}</h2>
            <p className="mt-1 text-xs text-muted-foreground">Last updated: {doc.updated}</p>
            <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{doc.intro}</p>
            <div className="mt-6 space-y-5">
              {doc.sections.map(([h, b]) => (
                <div key={h}>
                  <h3 className="font-display text-base font-bold text-foreground">{h}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{b}</p>
                </div>
              ))}
            </div>
            <div className="mt-6 flex justify-end">
              <button type="button" onClick={() => setActiveDoc(null)} data-testid="consent-doc-done"
                className="rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))]">
                I've read this
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
