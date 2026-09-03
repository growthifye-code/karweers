import { createContext, useContext, useEffect, useState, useRef, useCallback } from "react";
import api from "@/lib/api";

const AuthContext = createContext(null);
const IDLE_MS = 30 * 60 * 1000; // 30 minutes

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const idleTimer = useRef(null);

  useEffect(() => {
    // Returning from Google OAuth — let AuthCallback exchange the session first.
    if (window.location.hash?.includes("session_id=")) { setLoading(false); return; }
    // /auth/me resolves either a JWT (bearer) or a Google session cookie.
    // A timeout guarantees we never hang on a protected page — on any failure the
    // user falls through to unauthenticated and ProtectedRoute sends them to /login.
    api.get("/auth/me", { timeout: 12000 })
      .then((r) => setUser(r.data))
      .catch(() => { localStorage.removeItem("sk_token"); })
      .finally(() => setLoading(false));
  }, []);

  const logout = useCallback((redirect = false) => {
    api.post("/auth/logout").catch(() => {});
    localStorage.removeItem("sk_token");
    setUser(null);
    if (redirect) window.location.href = "/login";
  }, []);

  // 30-min inactivity auto-logout
  useEffect(() => {
    if (!user) return;
    const reset = () => {
      if (idleTimer.current) clearTimeout(idleTimer.current);
      idleTimer.current = setTimeout(() => logout(true), IDLE_MS);
    };
    const events = ["mousemove", "keydown", "click", "scroll", "touchstart"];
    events.forEach((e) => window.addEventListener(e, reset, { passive: true }));
    reset();
    return () => {
      events.forEach((e) => window.removeEventListener(e, reset));
      if (idleTimer.current) clearTimeout(idleTimer.current);
    };
  }, [user, logout]);

  const login = async (email, password, captchaToken, consent = false) => {
    const { data } = await api.post("/auth/login", { email, password, captcha_token: captchaToken, consent });
    localStorage.setItem("sk_token", data.token);
    setUser(data.user);
    return data.user;
  };

  const register = async (name, email, password, captchaToken, consent = false) => {
    const { data } = await api.post("/auth/register", { name, email, password, captcha_token: captchaToken, consent });
    localStorage.setItem("sk_token", data.token);
    setUser(data.user);
    return data.user;
  };

  // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
  const loginWithGoogle = async (captchaToken, consent = false) => {
    // hCaptcha + consent must be captured first; backend sets a short-lived gate cookie required by /auth/session.
    await api.post("/auth/captcha-gate", { captcha_token: captchaToken, consent });
    const redirectUrl = window.location.origin + "/dashboard";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, loginWithGoogle }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => useContext(AuthContext);

export function formatApiErrorDetail(detail) {
  if (detail == null) return "Something went wrong. Please try again.";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail.map((e) => (e && typeof e.msg === "string" ? e.msg : JSON.stringify(e))).filter(Boolean).join(" ");
  if (detail && typeof detail.msg === "string") return detail.msg;
  return String(detail);
}

// Turns any auth failure into a user-friendly message. Origin blips (no response,
// 5xx, or a non-JSON body like a raw Cloudflare error page) become a clean retry hint.
export function friendlyAuthError(err, fallback = "Something went wrong. Please try again.") {
  const res = err && err.response;
  const status = res && res.status;
  const data = res && res.data;
  if (!res || (status && status >= 500) || (status === 520) || (status === 522) || (status === 524)) {
    return "The server was briefly busy. Please try again in a moment.";
  }
  if (typeof data === "string") {
    // Non-JSON body (e.g. a Cloudflare/HTML error page) — never surface raw markup.
    return "The server was briefly busy. Please try again in a moment.";
  }
  return formatApiErrorDetail(data && data.detail) || fallback;
}
