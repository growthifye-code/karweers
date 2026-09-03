// Frontend runtime config. The admin console path and hCaptcha sitekey come from the
// backend (GET /api/public-config) so they can be rotated in the backend .env without a
// frontend rebuild. We cache the last-known values in localStorage and fall back to a
// sensible default so the app still routes correctly before the fetch resolves.
import axios from "axios";

const DEFAULT_ADMIN_PATH = "/sk-control-92f4a7e1";

export function getAdminPath() {
  try {
    return localStorage.getItem("sk_admin_path") || DEFAULT_ADMIN_PATH;
  } catch {
    return DEFAULT_ADMIN_PATH;
  }
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
    if (data?.admin_path) localStorage.setItem("sk_admin_path", data.admin_path);
    if (data?.hcaptcha_sitekey) localStorage.setItem("sk_hcaptcha_sitekey", data.hcaptcha_sitekey);
    return data;
  } catch {
    return null;
  }
}

// Back-compat export: static best-guess used only as an initial render value.
export const ADMIN_PATH = getAdminPath();
