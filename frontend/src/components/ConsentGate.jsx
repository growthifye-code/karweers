import { useState } from "react";
import { Check, FileText, ShieldCheck } from "lucide-react";

// Strict consent: the "I agree" checkbox is disabled until BOTH the Terms &
// Conditions and Privacy Policy have been opened in a new tab.
export default function ConsentGate({ agreed, setAgreed }) {
  const [termsOpened, setTermsOpened] = useState(false);
  const [privacyOpened, setPrivacyOpened] = useState(false);
  const bothOpened = termsOpened && privacyOpened;

  const open = (path, mark) => {
    window.open(path, "_blank", "noopener,noreferrer");
    mark(true);
  };

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
      <p className="mt-1 text-xs text-muted-foreground">Please open and read both documents, then confirm your agreement.</p>
      <div className="mt-3 grid grid-cols-2 gap-2">
        <DocBtn opened={termsOpened} onClick={() => open("/terms", setTermsOpened)} icon={FileText} label="Terms & Conditions" testid="consent-open-terms" />
        <DocBtn opened={privacyOpened} onClick={() => open("/privacy", setPrivacyOpened)} icon={ShieldCheck} label="Privacy Policy" testid="consent-open-privacy" />
      </div>
      <label className={`mt-3 flex items-start gap-2.5 text-xs ${bothOpened ? "cursor-pointer text-foreground" : "cursor-not-allowed text-muted-foreground opacity-70"}`}>
        <input type="checkbox" data-testid="consent-checkbox" disabled={!bothOpened}
          checked={agreed} onChange={(e) => setAgreed(e.target.checked)}
          className="mt-0.5 h-4 w-4 shrink-0 accent-[hsl(var(--primary))]" />
        <span>
          I have read and agree to the{" "}
          <a href="/terms" target="_blank" rel="noreferrer" className="font-semibold text-[hsl(var(--primary))] underline">Terms &amp; Conditions</a>{" "}and{" "}
          <a href="/privacy" target="_blank" rel="noreferrer" className="font-semibold text-[hsl(var(--primary))] underline">Privacy Policy</a>.
        </span>
      </label>
      {!bothOpened && (
        <p className="mt-2 text-[11px] font-medium text-amber-500" data-testid="consent-hint">
          Open both documents above to enable this checkbox.
        </p>
      )}
    </div>
  );
}
