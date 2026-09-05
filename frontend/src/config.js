// Frontend runtime config.
//
// Admin console path: kept as a BUILD-TIME constant (never exposed over the API) so the
// URL stays obscure. To rotate it, update ADMIN_CONSOLE_PATH here AND ADMIN_PATH in
// backend/.env so the two stay in sync.
//
// hCaptcha sitekey: fetched from the backend (GET /api/public-config) at startup so it can
// be rotated in the backend .env without a frontend rebuild; cached in localStorage with an
// env fallback.
import axios from "axios";

const ADMIN_CONSOLE_PATH = "/sk-control-92f4a7e1";

export function getAdminPath() {
  return ADMIN_CONSOLE_PATH;
}

export function getHcaptchaSitekey() {
  // Prefer the build-time env value (the source of truth after a key rotation) so a stale
  // localStorage cache from a previous key can never serve an outdated sitekey. Fall back to
  // the backend-provided value only when the env var is unset.
  const envKey = process.env.REACT_APP_HCAPTCHA_SITEKEY || "";
  if (envKey) return envKey;
  try {
    return localStorage.getItem("sk_hcaptcha_sitekey") || "";
  } catch {
    return "";
  }
}

export function getTurnstileSitekey() {
  // Cloudflare Turnstile sitekey (public). Prefer build-time env, fall back to the
  // backend-provided value cached at startup (rotatable via backend .env, no rebuild).
  const envKey = process.env.REACT_APP_TURNSTILE_SITEKEY || "";
  if (envKey) return envKey;
  try {
    return localStorage.getItem("sk_turnstile_sitekey") || "";
  } catch {
    return "";
  }
}

export async function loadPublicConfig() {
  try {
    const { data } = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/public-config`, { timeout: 8000 });
    if (data?.hcaptcha_sitekey) localStorage.setItem("sk_hcaptcha_sitekey", data.hcaptcha_sitekey);
    if (data?.turnstile_sitekey) localStorage.setItem("sk_turnstile_sitekey", data.turnstile_sitekey);
    return data;
  } catch {
    return null;
  }
}

// Back-compat export.
export const ADMIN_PATH = ADMIN_CONSOLE_PATH;
