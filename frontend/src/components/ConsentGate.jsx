import { useState } from "react";
import { Check, FileText, ShieldCheck, X } from "lucide-react";
import { DOCS } from "@/pages/LegalPage";

// Consent: a simple tick confirms agreement to Terms & Privacy. The documents
// remain openable in an in-page modal (optional reading — no new tab), preserving
// the sign-in form state.
export default function ConsentGate({ agreed, setAgreed }) {
  const [termsOpened, setTermsOpened] = useState(false);
  const [privacyOpened, setPrivacyOpened] = useState(false);
  const [activeDoc, setActiveDoc] = useState(null); // "terms" | "privacy" | null

  const openDoc = (key, mark) => { mark(true); setActiveDoc(key); };
  const doc = activeDoc ? DOCS[activeDoc] : null;

  const DocBtn = ({ opened, onClick, icon: Icon, label, testid }) => (
    <button type="button" onClick={onClick} data-testid={testid}
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg border px-3 py-2.5 text-xs font-semibold transition-colors ${
        opened ? "border-[hsl(var(--primary))] text-[hsl(var(--primary))]" : "border-border text-foreground hover:bg-secondary"}`}>
      {opened ? <Check className="h-3.5 w-3.5" /> : <Icon className="h-3.5 w-3.5" />} {label}
    </button>
  );

  return (
    <div className="rounded-xl border border-border bg-secondary/40 p-4" data-testid="consent-gate">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Before you continue</p>
      <p className="mt-1 text-xs text-muted-foreground">Just tick to confirm — no need to open the documents (they're here if you'd like to read them).</p>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <DocBtn opened={termsOpened} onClick={() => openDoc("terms", setTermsOpened)} icon={FileText} label="Terms & Conditions" testid="consent-open-terms" />
        <DocBtn opened={privacyOpened} onClick={() => openDoc("privacy", setPrivacyOpened)} icon={ShieldCheck} label="Privacy Policy" testid="consent-open-privacy" />
      </div>
      <label className="mt-3 flex items-start gap-2.5 text-xs cursor-pointer text-foreground">
        <input type="checkbox" data-testid="consent-checkbox"
          checked={agreed} onChange={(e) => setAgreed(e.target.checked)}
          className="mt-0.5 h-4 w-4 shrink-0 accent-[hsl(var(--primary))]" />
        <span>
          I have read and agree to the{" "}
          <button type="button" onClick={() => openDoc("terms", setTermsOpened)} className="font-semibold text-[hsl(var(--primary))] underline">Terms &amp; Conditions</button>{" "}and{" "}
          <button type="button" onClick={() => openDoc("privacy", setPrivacyOpened)} className="font-semibold text-[hsl(var(--primary))] underline">Privacy Policy</button>.
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
