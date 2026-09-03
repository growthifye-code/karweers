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
  try {
    return localStorage.getItem("sk_hcaptcha_sitekey") || process.env.REACT_APP_HCAPTCHA_SITEKEY || "";
  } catch {
    return process.env.REACT_APP_HCAPTCHA_SITEKEY || "";
  }
}

export async function loadPublicConfig() {
  try {
    const { data } = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/public-config`, { timeout: 8000 });
    if (data?.hcaptcha_sitekey) localStorage.setItem("sk_hcaptcha_sitekey", data.hcaptcha_sitekey);
    return data;
  } catch {
    return null;
  }
}

// Back-compat export.
export const ADMIN_PATH = ADMIN_CONSOLE_PATH;
