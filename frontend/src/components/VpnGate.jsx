import { useEffect, useState } from "react";
import { ShieldAlert } from "lucide-react";
import api from "@/lib/api";

export default function VpnGate() {
  const [blocked, setBlocked] = useState(false);
  const [reason, setReason] = useState("");
  const [country, setCountry] = useState("");
  const [code, setCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/vpn/status")
      .then((r) => { setBlocked(!!r.data.blocked); setReason(r.data.reason || ""); setCountry(r.data.country || ""); })
      .catch((e) => {
        const d = e?.response?.data;
        if (e?.response?.status === 403 && (d?.vpn_block || d?.country_block)) {
          setBlocked(true);
          if (d?.country_block) { setReason("country"); setCountry(d.country || ""); }
        }
      });
  }, []);

  if (!blocked) return null;
  const isCountry = reason === "country";

  const verify = async (e) => {
    e.preventDefault();
    if (code.length !== 6) { setError("Enter the 6-digit code."); return; }
    setBusy(true); setError("");
    try {
      await api.post("/vpn/verify", { code });
      window.location.reload();
    } catch (err) {
      setError(err?.response?.data?.detail || "Invalid or expired code.");
      setBusy(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[9999] grid place-items-center bg-[#050505] px-6" data-testid="vpn-gate">
      <div className="w-full max-w-md rounded-2xl border border-border bg-card p-8 text-center">
        <div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-red-500/15">
          <ShieldAlert className="h-7 w-7 text-red-500" />
        </div>
        {isCountry ? (
          <>
            <h1 className="mt-6 font-display text-2xl font-black">Region not available</h1>
            <p className="mt-3 text-sm text-muted-foreground">
              We're sorry — access from {country || "your region"} is currently restricted. If you believe this is an error, please contact us.
            </p>
            <button onClick={() => window.location.reload()} data-testid="vpn-reload-btn"
              className="mt-6 rounded-full border border-border px-6 py-3 text-sm font-semibold hover:bg-secondary">Reload</button>
          </>
        ) : (
          <>
            <h1 className="mt-6 font-display text-2xl font-black">VPN / proxy detected</h1>
            <p className="mt-3 text-sm text-muted-foreground">
              For security, access from VPNs, proxies and anonymisers is restricted. Please turn off your VPN and reload —
              or, if you're a trusted user, enter your 6-digit access code below.
            </p>
            <form onSubmit={verify} className="mt-6 space-y-3">
              <input
                value={code}
                onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
                inputMode="numeric" autoComplete="one-time-code" placeholder="000000"
                data-testid="vpn-code-input"
                className="w-full rounded-xl border border-border bg-background px-4 py-3 text-center text-lg font-mono tracking-[0.4em] outline-none focus:border-[hsl(var(--primary))]"
              />
              {error && <p className="text-sm text-red-500" data-testid="vpn-gate-error">{error}</p>}
              <button type="submit" disabled={busy || code.length !== 6} data-testid="vpn-verify-btn"
                className="w-full rounded-full bg-[hsl(var(--primary))] px-6 py-3 font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-60">
                {busy ? "Verifying…" : "Verify access code"}
              </button>
            </form>
            <button onClick={() => window.location.reload()} data-testid="vpn-reload-btn"
              className="mt-4 text-sm text-muted-foreground hover:text-foreground">I've disabled my VPN — reload</button>
          </>
        )}
      </div>
    </div>
  );
}
