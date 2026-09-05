import { useState, useEffect, useRef } from "react";
import HCaptcha from "@hcaptcha/react-hcaptcha";
import { ShieldCheck, ShieldAlert, ShieldQuestion, Loader2, RefreshCw } from "lucide-react";
import api from "@/lib/api";

const secretBadge = {
  valid: { cls: "bg-emerald-500/15 text-emerald-500", label: "Secret recognised" },
  invalid: { cls: "bg-red-500/15 text-red-500", label: "Secret not recognised" },
  test: { cls: "bg-amber-500/15 text-amber-500", label: "Test secret (no protection)" },
  error: { cls: "bg-amber-500/15 text-amber-500", label: "Could not reach hCaptcha" },
  unknown: { cls: "bg-muted text-muted-foreground", label: "Unknown" },
};

export const CaptchaHealth = () => {
  const [health, setHealth] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [showWidget, setShowWidget] = useState(false);
  const captchaRef = useRef(null);

  const load = () => api.get("/admin/captcha/health").then((r) => setHealth(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const runTest = async (token) => {
    setTesting(true);
    setTestResult(null);
    try {
      const r = await api.post("/admin/captcha/verify-test", { token });
      setTestResult(r.data);
    } catch (e) {
      setTestResult({ success: false, message: "Test request failed. Try again." });
    } finally {
      setTesting(false);
      setShowWidget(false);
      try { captchaRef.current?.resetCaptcha(); } catch (x) { /* noop */ }
    }
  };

  const sb = secretBadge[health?.secret_status] || secretBadge.unknown;

  return (
    <div className="mt-6 rounded-2xl border border-border bg-card p-6" data-testid="captcha-health-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="flex items-center gap-2 font-display text-lg font-bold">
            <ShieldCheck className="h-4 w-4 text-[hsl(var(--primary))]" /> Captcha Health
          </h3>
          <p className="text-sm text-muted-foreground">Live-test the hCaptcha sitekey/secret pairing before a visitor hits a mismatch.</p>
        </div>
        <button onClick={load} data-testid="captcha-health-refresh" className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary">
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>

      {health && (
        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          <div className="rounded-xl border border-border bg-background p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Sitekey</p>
            <p className="mt-1 break-all font-mono text-xs" data-testid="captcha-sitekey">{health.sitekey || "— not set —"}</p>
          </div>
          <div className="rounded-xl border border-border bg-background p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Secret status</p>
            <span className={`mt-1 inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${sb.cls}`} data-testid="captcha-secret-status">
              {health.secret_status === "valid" ? <ShieldCheck className="h-3.5 w-3.5" /> : health.secret_status === "invalid" ? <ShieldAlert className="h-3.5 w-3.5" /> : <ShieldQuestion className="h-3.5 w-3.5" />}
              {sb.label}
            </span>
            {health.secret_detail && <p className="mt-2 text-xs text-muted-foreground">{health.secret_detail}</p>}
          </div>
        </div>
      )}

      <div className="mt-5 rounded-xl border border-dashed border-border p-4">
        <p className="text-sm font-semibold">Live pairing test</p>
        <p className="mt-1 text-xs text-muted-foreground">Solve the captcha below — we verify the real token against your configured secret. This is the only definitive way to catch a <span className="font-mono">sitekey-secret-mismatch</span>.</p>

        {!showWidget && !testResult && (
          <button onClick={() => setShowWidget(true)} disabled={!health?.sitekey} data-testid="captcha-run-test"
            className="mt-3 rounded-full bg-[hsl(var(--accent))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
            Run live test
          </button>
        )}

        {showWidget && health?.sitekey && (
          <div className="mt-4" data-testid="captcha-test-widget">
            <HCaptcha ref={captchaRef} sitekey={health.sitekey} onVerify={runTest} onExpire={() => setShowWidget(false)} />
          </div>
        )}

        {testing && (
          <p className="mt-3 inline-flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Verifying token…</p>
        )}

        {testResult && (
          <div className={`mt-3 rounded-xl border p-4 ${testResult.success ? "border-emerald-500/40 bg-emerald-500/5" : "border-red-500/40 bg-red-500/5"}`} data-testid="captcha-test-result">
            <p className={`flex items-center gap-2 text-sm font-bold ${testResult.success ? "text-emerald-500" : "text-red-500"}`}>
              {testResult.success ? <ShieldCheck className="h-4 w-4" /> : <ShieldAlert className="h-4 w-4" />}
              {testResult.success ? "Pairing verified" : "Pairing failed"}
            </p>
            <p className="mt-1.5 text-sm text-foreground">{testResult.message}</p>
            {testResult.error_codes?.length > 0 && (
              <p className="mt-1 font-mono text-xs text-muted-foreground">codes: {testResult.error_codes.join(", ")}</p>
            )}
            <button onClick={() => { setTestResult(null); }} data-testid="captcha-test-again" className="mt-3 rounded-full border border-border px-4 py-1.5 text-xs font-medium hover:bg-secondary">Test again</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CaptchaHealth;
