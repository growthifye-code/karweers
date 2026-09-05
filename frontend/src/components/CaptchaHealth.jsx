import { useState, useEffect, useRef, useCallback } from "react";
import { ShieldCheck, ShieldAlert, ShieldQuestion, Loader2, RefreshCw } from "lucide-react";
import api from "@/lib/api";
import Captcha from "@/components/Captcha";

const secretBadge = {
  valid: { cls: "bg-emerald-500/15 text-emerald-500", label: "Secret recognised by Google" },
  invalid: { cls: "bg-red-500/15 text-red-500", label: "Secret not recognised" },
  test: { cls: "bg-amber-500/15 text-amber-500", label: "Not configured (lenient)" },
  error: { cls: "bg-amber-500/15 text-amber-500", label: "Could not reach Google" },
  unknown: { cls: "bg-muted text-muted-foreground", label: "Unknown" },
};

export const CaptchaHealth = () => {
  const [health, setHealth] = useState(null);
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const captchaRef = useRef(null);
  const pendingRef = useRef(false);

  const load = () => api.get("/admin/captcha/health").then((r) => setHealth(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const onToken = useCallback(async (token) => {
    if (!pendingRef.current || !token) return;
    pendingRef.current = false;
    try {
      const r = await api.post("/admin/captcha/verify-test", { token });
      setTestResult(r.data);
    } catch (e) {
      setTestResult({ success: false, message: "Test request failed. Try again." });
    } finally {
      setTesting(false);
    }
  }, []);

  const runTest = () => {
    setTesting(true);
    setTestResult(null);
    pendingRef.current = true;
    try { captchaRef.current?.execute(); } catch (e) { setTesting(false); }
  };

  const sb = secretBadge[health?.secret_status] || secretBadge.unknown;

  return (
    <div className="mt-6 rounded-2xl border border-border bg-card p-6" data-testid="captcha-health-card">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="flex items-center gap-2 font-display text-lg font-bold">
            <ShieldCheck className="h-4 w-4 text-[hsl(var(--primary))]" /> Captcha Health — reCAPTCHA v3
          </h3>
          <p className="text-sm text-muted-foreground">Confirm the reCAPTCHA v3 sitekey/secret are configured and score visitors correctly.</p>
        </div>
        <button onClick={load} data-testid="captcha-health-refresh" className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary">
          <RefreshCw className="h-3.5 w-3.5" /> Refresh
        </button>
      </div>

      {health && (
        <div className="mt-5 grid gap-3 sm:grid-cols-3">
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
          <div className="rounded-xl border border-border bg-background p-4">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">Score threshold</p>
            <p className="mt-1 font-mono text-sm" data-testid="captcha-threshold">{health.score_threshold ?? "0.5"}</p>
            <p className="mt-2 text-xs text-muted-foreground">Requests scoring below this are rejected as bots.</p>
          </div>
        </div>
      )}

      <div className="mt-5 rounded-xl border border-dashed border-border p-4">
        <p className="text-sm font-semibold">Live score test</p>
        <p className="mt-1 text-xs text-muted-foreground">Runs an invisible reCAPTCHA check against your configured secret and reports the score. Only works once real keys are set on the live domain.</p>

        <button onClick={runTest} disabled={!health?.sitekey || testing} data-testid="captcha-run-test"
          className="mt-3 rounded-full bg-[hsl(var(--accent))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
          {testing ? "Testing…" : "Run live test"}
        </button>

        {/* Invisible token provider reused for the test. */}
        <div className="hidden"><Captcha ref={captchaRef} lazy={false} action="admin_health" onVerify={onToken} /></div>

        {testing && (
          <p className="mt-3 inline-flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Verifying token…</p>
        )}

        {testResult && (
          <div className={`mt-3 rounded-xl border p-4 ${testResult.success ? "border-emerald-500/40 bg-emerald-500/5" : "border-red-500/40 bg-red-500/5"}`} data-testid="captcha-test-result">
            <p className={`flex items-center gap-2 text-sm font-bold ${testResult.success ? "text-emerald-500" : "text-red-500"}`}>
              {testResult.success ? <ShieldCheck className="h-4 w-4" /> : <ShieldAlert className="h-4 w-4" />}
              {testResult.success ? "Verified" : "Failed"}
            </p>
            <p className="mt-1.5 text-sm text-foreground">{testResult.message}</p>
            {testResult.error_codes?.length > 0 && (
              <p className="mt-1 font-mono text-xs text-muted-foreground">codes: {testResult.error_codes.join(", ")}</p>
            )}
            <button onClick={() => setTestResult(null)} data-testid="captcha-test-again" className="mt-3 rounded-full border border-border px-4 py-1.5 text-xs font-medium hover:bg-secondary">Test again</button>
          </div>
        )}
      </div>
    </div>
  );
};

export default CaptchaHealth;
