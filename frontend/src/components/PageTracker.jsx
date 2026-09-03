import { useEffect } from "react";
import { useLocation } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { track } from "@/lib/api";
import { ADMIN_PATH } from "@/config";

const LABELS = {
  "/": "Home", "/about": "About", "/services": "Services", "/insights": "Insights",
  "/learning": "Learning Hub", "/case-studies": "Case Studies", "/market": "Market", "/deals": "Deals",
};

export default function PageTracker() {
  const location = useLocation();
  const { user } = useAuth();

  useEffect(() => {
    if (!user) return;
    const path = location.pathname;
    if (path.startsWith(ADMIN_PATH) || path.startsWith("/admin") || path.startsWith("/dashboard")) return;
    const label = LABELS[path] || (path.startsWith("/services/") ? "Service page" : path);
    track("page", path, label);
  }, [location.pathname, user]);

  return null;
}
