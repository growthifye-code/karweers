import axios from "axios";
import { ADMIN_PATH } from "@/config";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const api = axios.create({ baseURL: API, withCredentials: true });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("sk_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// On an expired/invalid session (401), never leave the user on a broken protected
// page — clear the token and send them back to the login page.
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("sk_token");
      const p = window.location.pathname;
      if ((p.startsWith(ADMIN_PATH) || p.startsWith("/admin") || p.startsWith("/dashboard")) && p !== "/login") {
        window.location.replace("/login");
      }
    }
    return Promise.reject(error);
  }
);

// Fire-and-forget browsing tracker for the recommendation engine (consent-gated).
export const track = (kind, ref = "", label = "") => {
  try { if (localStorage.getItem("sk_consent") !== "accepted") return Promise.resolve(); } catch { return Promise.resolve(); }
  return api.post("/track", { kind, ref, label }).catch(() => {});
};

export default api;
