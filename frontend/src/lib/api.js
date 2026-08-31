import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
export const API = `${BACKEND_URL}/api`;

const api = axios.create({ baseURL: API, withCredentials: true });

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("sk_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Fire-and-forget browsing tracker for the recommendation engine (consent-gated).
export const track = (kind, ref = "", label = "") => {
  try { if (localStorage.getItem("sk_consent") !== "accepted") return Promise.resolve(); } catch { return Promise.resolve(); }
  return api.post("/track", { kind, ref, label }).catch(() => {});
};

export default api;
