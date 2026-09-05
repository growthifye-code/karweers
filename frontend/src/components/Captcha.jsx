import { forwardRef, useRef, useState, useEffect, useImperativeHandle, useCallback } from "react";
import { getRecaptchaSitekey } from "@/config";

// Google reCAPTCHA v3 — invisible & score-based. There is NO widget UI; a token is fetched
// silently and passed to the form via onVerify(token). The same interface as the old widget
// (onVerify / onExpire / ref.resetCaptcha) is preserved so the consuming forms are unchanged.
// When no sitekey is configured (preview/dev, or before keys are added) we emit a bypass
// sentinel so forms still submit — the backend auto-passes captcha on preview and stays
// lenient until RECAPTCHA_SECRET is set.
const BYPASS_TOKEN = "no-captcha-preview";
const REFRESH_MS = 100000; // v3 tokens expire ~120s — refresh before that.

let _scriptPromise = null;

function loadRecaptcha(siteKey) {
  if (typeof window !== "undefined" && window.grecaptcha && window.grecaptcha.execute) {
    return Promise.resolve(window.grecaptcha);
  }
  if (_scriptPromise) return _scriptPromise;
  _scriptPromise = new Promise((resolve, reject) => {
    const existing = document.querySelector("script[data-recaptcha-v3]");
    if (existing) {
      existing.addEventListener("load", () => resolve(window.grecaptcha), { once: true });
      existing.addEventListener("error", () => reject(new Error("load failed")), { once: true });
      return;
    }
    const s = document.createElement("script");
    s.src = `https://www.google.com/recaptcha/api.js?render=${encodeURIComponent(siteKey)}`;
    s.async = true;
    s.defer = true;
    s.dataset.recaptchaV3 = "true";
    s.onload = () => resolve(window.grecaptcha);
    s.onerror = () => reject(new Error("load failed"));
    document.head.appendChild(s);
  });
  return _scriptPromise;
}

// Mount only once the visitor starts interacting with the surrounding form.
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

const Captcha = forwardRef(function Captcha({ onVerify, onExpire, lazy = true, action = "submit" }, ref) {
  const wrapRef = useRef(null);
  const timerRef = useRef(null);
  const sitekey = getRecaptchaSitekey();
  const [active, setActive] = useState(!lazy);

  const execute = useCallback(async () => {
    if (!sitekey) { onVerify && onVerify(BYPASS_TOKEN); return; }
    try {
      const grecaptcha = await loadRecaptcha(sitekey);
      await new Promise((res) => grecaptcha.ready(res));
      const token = await grecaptcha.execute(sitekey, { action });
      onVerify && onVerify(token || "");
    } catch (e) {
      // Network/script blocked: hand back a bypass sentinel so the user isn't hard-stuck.
      // Production still enforces server-side (a bad token fails siteverify).
      onVerify && onVerify(BYPASS_TOKEN);
    }
  }, [sitekey, action, onVerify]);

  const reset = useCallback(() => {
    if (onExpire) { /* forms treat reset as "need a fresh token" */ }
    execute();
  }, [execute, onExpire]);

  useImperativeHandle(ref, () => ({ resetCaptcha: reset, reset, execute }), [reset, execute]);

  // Lazy activate on first form interaction.
  useEffect(() => {
    if (active) return;
    const container = findFieldContainer(wrapRef.current);
    if (!container) { setActive(true); return; }
    const activate = () => setActive(true);
    container.addEventListener("focusin", activate, { once: true });
    return () => container.removeEventListener("focusin", activate);
  }, [active]);

  // Fetch an initial token when active, then keep it fresh.
  useEffect(() => {
    if (!active) return;
    execute();
    if (sitekey) {
      timerRef.current = setInterval(execute, REFRESH_MS);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [active, execute, sitekey]);

  return (
    <div data-testid="captcha" ref={wrapRef} className="my-1">
      {/* Required reCAPTCHA branding notice (badge also shows bottom-right). */}
      <p className="text-[11px] leading-snug text-muted-foreground" data-testid="recaptcha-notice">
        Protected by reCAPTCHA — Google{" "}
        <a href="https://policies.google.com/privacy" target="_blank" rel="noreferrer" className="underline hover:text-foreground">Privacy Policy</a>{" "}
        &amp;{" "}
        <a href="https://policies.google.com/terms" target="_blank" rel="noreferrer" className="underline hover:text-foreground">Terms</a>{" "}
        apply.
      </p>
    </div>
  );
});

export default Captcha;
