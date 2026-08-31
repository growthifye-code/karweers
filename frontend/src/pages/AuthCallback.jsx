import { useEffect, useRef } from "react";
import api from "@/lib/api";

// REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
export default function AuthCallback() {
  const done = useRef(false);

  useEffect(() => {
    if (done.current) return;
    done.current = true;
    const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
    const sid = params.get("session_id");
    if (!sid) {
      window.location.replace("/login");
      return;
    }
    api.post("/auth/session", { session_id: sid })
      .then(() => window.location.replace("/dashboard"))
      .catch(() => window.location.replace("/login?error=google"));
  }, []);

  return (
    <div className="min-h-screen grid place-items-center bg-background text-foreground">
      <div className="text-center">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-2 border-[hsl(var(--primary))] border-t-transparent" />
        <p className="mt-5 font-display text-lg">Signing you in…</p>
      </div>
    </div>
  );
}
