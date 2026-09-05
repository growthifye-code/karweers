// Frontend runtime config.
//
// Admin console path: kept as a BUILD-TIME constant (never exposed over the API) so the
// URL stays obscure. To rotate it, update ADMIN_CONSOLE_PATH here AND ADMIN_PATH in
// backend/.env so the two stay in sync.
//
// reCAPTCHA v3 sitekey: fetched from the backend (GET /api/public-config) at startup so it can
// be rotated in the backend .env without a frontend rebuild; cached in localStorage with an
// env fallback.
import axios from "axios";

const ADMIN_CONSOLE_PATH = "/sk-control-92f4a7e1";

export function getAdminPath() {
  return ADMIN_CONSOLE_PATH;
}

export function getRecaptchaSitekey() {
  // Google reCAPTCHA v3 sitekey (public). Prefer build-time env, fall back to the
  // backend-provided value cached at startup (rotatable via backend .env, no rebuild).
  const envKey = process.env.REACT_APP_RECAPTCHA_SITEKEY || "";
  if (envKey) return envKey;
  try {
    return localStorage.getItem("sk_recaptcha_sitekey") || "";
  } catch {
    return "";
  }
}

export async function loadPublicConfig() {
  try {
    const { data } = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/public-config`, { timeout: 8000 });
    if (data?.recaptcha_sitekey) localStorage.setItem("sk_recaptcha_sitekey", data.recaptcha_sitekey);
    return data;
  } catch {
    return null;
  }
}

// Back-compat export.
export const ADMIN_PATH = ADMIN_CONSOLE_PATH;
