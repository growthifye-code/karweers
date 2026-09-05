import { forwardRef, useRef, useState, useEffect, useCallback } from "react";
import HCaptcha from "@hcaptcha/react-hcaptcha";
import { RotateCw, ShieldCheck } from "lucide-react";
import { getHcaptchaSitekey } from "@/config";

// hCaptcha's official always-pass TEST sitekey (works on ANY hostname, never challenges).
const TEST_SITEKEY = "10000000-ffff-ffff-ffff-000000000001";

// The real sitekey is hostname-locked to production in the hCaptcha dashboard, so it
// cannot complete a challenge on the ephemeral preview domain. Select by EXACT hostname:
// real key only on production; the always-pass test key everywhere else (preview/localhost).
// The backend already auto-passes captcha on preview hosts, so the test token is accepted
// on preview and full siteverify runs only on production. The production sitekey is served
// by the backend (/api/public-config → getHcaptchaSitekey) so it can be rotated via .env.
const PRODUCTION_HOSTNAMES = new Set(["sudarshankarweer.com", "www.sudarshankarweer.com"]);

function pickSitekey() {
  // Diagnostic override: force the real sitekey everywhere (used to validate a real key
  // pair on the preview domain before deploying). Requires the preview host to be added to
  // the hCaptcha site's allowed hostnames.
  if (process.env.REACT_APP_CAPTCHA_FORCE_REAL === "1") {
    return getHcaptchaSitekey() || TEST_SITEKEY;
  }
  const host = (typeof window !== "undefined" ? window.location.hostname : "").toLowerCase();
  if (PRODUCTION_HOSTNAMES.has(host)) {
    return getHcaptchaSitekey() || TEST_SITEKEY;
  }
  return TEST_SITEKEY;
}

const SITEKEY = pickSitekey();

// Find the surrounding form (or nearest container that holds form fields) so we can mount
// hCaptcha only once the visitor actually starts filling it in.
function findFieldContainer(el) {
  if (!el) return null;
  const form = el.closest("form");
  if (form) return form;
  let p = el.parentElement;
  for (let i = 0; i < 6 && p; i++) {
    if (p.querySelector("input, textarea, select")) return p;
    p = p.parentElement;
  }
  return null;
}

const Captcha = forwardRef(function Captcha({ onVerify, onExpire, lazy = true }, ref) {
  const wrapRef = useRef(null);
  const innerRef = useRef(null);
  const [active, setActive] = useState(!lazy);
  const [errored, setErrored] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);

  // Forward the widget instance to both our internal ref and the parent's ref.
  const setRefs = useCallback((node) => {
    innerRef.current = node;
    if (typeof ref === "function") ref(node);
    else if (ref) ref.current = node;
  }, [ref]);

  // Lazy mount: load hCaptcha only when the visitor first interacts with the form. This
  // avoids loading the hCaptcha script on every page view and sharply cuts rate-limit risk.
  useEffect(() => {
    if (active) return;
    const container = findFieldContainer(wrapRef.current);
    if (!container) return;
    const activate = () => setActive(true);
    container.addEventListener("focusin", activate, { once: true });
    return () => container.removeEventListener("focusin", activate);
  }, [active]);

  // Recover from a "rate limited / network error" by remounting the widget (a full remount
  // re-requests the hCaptcha script + a fresh challenge, clearing transient load failures).
  const reload = () => {
    setErrored(false);
    try { innerRef.current?.resetCaptcha(); } catch (e) { /* widget not mounted */ }
    setReloadKey((k) => k + 1);
  };

  return (
    <div data-testid="hcaptcha" className="my-2" ref={wrapRef}>
      {!active ? (
        <button
          type="button"
          onClick={() => setActive(true)}
          data-testid="captcha-activate"
          className="flex w-[300px] max-w-full items-center gap-3 rounded-md border border-border bg-secondary/40 px-4 py-3.5 text-left text-sm text-muted-foreground transition-colors hover:bg-secondary"
        >
          <span className="flex h-6 w-6 items-center justify-center rounded border border-border bg-background">
            <ShieldCheck className="h-3.5 w-3.5 text-[hsl(var(--primary))]" />
          </span>
          Verify you&apos;re human
        </button>
      ) : (
        <>
          <HCaptcha
            key={`${SITEKEY}-${reloadKey}`}
            ref={setRefs}
            sitekey={SITEKEY}
            theme="dark"
            reCaptchaCompat={false}
            onVerify={(t) => { setErrored(false); onVerify && onVerify(t); }}
            onExpire={() => onExpire && onExpire()}
            onChalExpired={() => setErrored(true)}
            onError={(e) => { console.error("hCaptcha error", e); setErrored(true); }}
          />
          {/* hCaptcha sometimes shows a "rate limited / network error" note INSIDE its iframe
              without firing onError, so we always expose a reload affordance to recover. */}
          <button
            type="button"
            onClick={reload}
            data-testid="captcha-reload"
            className={`mt-2 inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-secondary ${errored ? "border-[hsl(var(--destructive))]/40 bg-[hsl(var(--destructive))]/5 text-foreground" : "border-border/60 text-muted-foreground"}`}
          >
            <RotateCw className="h-3.5 w-3.5" /> {errored ? "Captcha didn't load — tap to retry" : "Captcha not showing? Reload it"}
          </button>
        </>
      )}
    </div>
  );
});

export default Captcha;
