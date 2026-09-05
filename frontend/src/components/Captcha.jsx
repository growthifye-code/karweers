import { forwardRef, useRef, useState, useEffect, useImperativeHandle, useCallback } from "react";
import { RotateCw, ShieldCheck } from "lucide-react";
import { getTurnstileSitekey } from "@/config";

// Cloudflare Turnstile — official always-pass TEST sitekey (works on ANY hostname).
const TEST_SITEKEY = "1x00000000000000000000AA";

// The real sitekey is hostname-locked to production in the Cloudflare dashboard, so it
// cannot complete a challenge on the ephemeral preview domain. Select by EXACT hostname:
// real key only on production; the always-pass test key everywhere else (preview/localhost).
// The backend already auto-passes captcha on preview hosts, so the test token is accepted
// on preview and full siteverify runs only on production. The production sitekey is served
// by the backend (/api/public-config → getTurnstileSitekey) so it can be rotated via .env.
const PRODUCTION_HOSTNAMES = new Set(["sudarshankarweer.com", "www.sudarshankarweer.com"]);

function pickSitekey() {
  // Diagnostic override: force the real sitekey everywhere (used to validate a real key
  // pair on the preview domain before deploying). Requires the preview host to be added to
  // the Turnstile widget's allowed hostnames.
  if (process.env.REACT_APP_CAPTCHA_FORCE_REAL === "1") {
    return getTurnstileSitekey() || TEST_SITEKEY;
  }
  const host = (typeof window !== "undefined" ? window.location.hostname : "").toLowerCase();
  if (PRODUCTION_HOSTNAMES.has(host)) {
    return getTurnstileSitekey() || TEST_SITEKEY;
  }
  return TEST_SITEKEY;
}

const SCRIPT_SRC = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
let _scriptPromise = null;

function loadTurnstileScript() {
  if (typeof window !== "undefined" && window.turnstile) return Promise.resolve();
  if (_scriptPromise) return _scriptPromise;
  _scriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector("script[data-turnstile]");
    if (existing) {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("load failed")), { once: true });
      return;
    }
    const s = document.createElement("script");
    s.src = SCRIPT_SRC;
    s.async = true;
    s.defer = true;
    s.dataset.turnstile = "true";
    s.onload = () => resolve();
    s.onerror = () => reject(new Error("load failed"));
    document.head.appendChild(s);
  });
  return _scriptPromise;
}

// Find the surrounding form (or nearest container that holds form fields) so we can mount
// the widget only once the visitor actually starts filling it in.
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
  const boxRef = useRef(null);
  const widgetId = useRef(null);
  const [active, setActive] = useState(!lazy);
  const [errored, setErrored] = useState(false);

  const reset = useCallback(() => {
    setErrored(false);
    try {
      if (widgetId.current !== null && window.turnstile) window.turnstile.reset(widgetId.current);
    } catch (e) { /* widget not mounted */ }
    onVerify && onVerify("");
  }, [onVerify]);

  // Keep the same imperative API the forms already use (captchaRef.current.resetCaptcha()).
  useImperativeHandle(ref, () => ({ resetCaptcha: reset, reset }), [reset]);

  // Lazy mount: activate only when the visitor first interacts with the form.
  useEffect(() => {
    if (active) return;
    const container = findFieldContainer(wrapRef.current);
    if (!container) return;
    const activate = () => setActive(true);
    container.addEventListener("focusin", activate, { once: true });
    return () => container.removeEventListener("focusin", activate);
  }, [active]);

  // Explicit render once active.
  useEffect(() => {
    if (!active) return;
    let cancelled = false;
    let tries = 0;
    const doRender = () => {
      if (cancelled || widgetId.current !== null) return;
      if (!window.turnstile || !window.turnstile.render || !boxRef.current) {
        if (tries++ < 60) { setTimeout(doRender, 100); return; }
        setErrored(true);
        return;
      }
      try {
        widgetId.current = window.turnstile.render(boxRef.current, {
          sitekey: pickSitekey(),
          theme: "dark",
          callback: (token) => { setErrored(false); onVerify && onVerify(token); },
          "expired-callback": () => { onVerify && onVerify(""); onExpire && onExpire(); },
          "timeout-callback": () => { setErrored(true); onVerify && onVerify(""); },
          "error-callback": () => { setErrored(true); onVerify && onVerify(""); },
        });
      } catch (e) { setErrored(true); }
    };
    loadTurnstileScript().then(() => { if (!cancelled) doRender(); }).catch(() => setErrored(true));
    return () => {
      cancelled = true;
      try {
        if (widgetId.current !== null && window.turnstile) window.turnstile.remove(widgetId.current);
      } catch (e) { /* noop */ }
      widgetId.current = null;
    };
  }, [active, onVerify, onExpire]);

  const reload = () => {
    setErrored(false);
    try {
      if (widgetId.current !== null && window.turnstile) {
        window.turnstile.reset(widgetId.current);
        return;
      }
    } catch (e) { /* fall through to remount */ }
    // Force a remount by toggling active off/on.
    widgetId.current = null;
    setActive(false);
    setTimeout(() => setActive(true), 20);
  };

  return (
    <div data-testid="captcha" className="my-2" ref={wrapRef}>
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
          <div ref={boxRef} data-testid="turnstile-widget" aria-live="polite" />
          <button
            type="button"
            onClick={reload}
            data-testid="captcha-reload"
            className={`mt-2 inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors hover:bg-secondary ${errored ? "border-[hsl(var(--destructive))]/40 bg-[hsl(var(--destructive))]/5 text-foreground" : "border-border/60 text-muted-foreground"}`}
          >
            <RotateCw className="h-3.5 w-3.5" /> {errored ? "Verification didn't load — tap to retry" : "Verification not showing? Reload it"}
          </button>
        </>
      )}
    </div>
  );
});

export default Captcha;
