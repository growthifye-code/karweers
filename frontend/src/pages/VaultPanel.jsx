import { useEffect, useState } from "react";
import { toast } from "sonner";
import { KeyRound, ShieldCheck, Lock, Unlock, Fingerprint, Smartphone, Trash2, Plus, Eye, EyeOff } from "lucide-react";
import api from "@/lib/api";
import { registerPasskey, authPasskey, passkeySupported } from "@/lib/webauthn";

export default function VaultPanel() {
  const [status, setStatus] = useState(null);
  const [enrollQr, setEnrollQr] = useState(null);
  const [enrollCode, setEnrollCode] = useState("");
  const [unlockCode, setUnlockCode] = useState("");
  const [busy, setBusy] = useState(false);
  const [keys, setKeys] = useState([]);
  const [label, setLabel] = useState("");
  const [value, setValue] = useState("");
  const [reveal, setReveal] = useState({});
  const [secsLeft, setSecsLeft] = useState(0);
  const [lockSecs, setLockSecs] = useState(0);

  const load = async () => {
    const { data } = await api.get("/admin/vault/status");
    setStatus(data);
    setSecsLeft(data.unlock_seconds_left || 0);
    setLockSecs(data.lock_seconds_left || 0);
    if (data.unlocked) {
      const r = await api.get("/admin/vault/keys");
      setKeys(r.data.keys || []);
    }
  };
  useEffect(() => { load().catch(() => {}); }, []);

  useEffect(() => {
    if (lockSecs <= 0) return;
    const t = setInterval(() => {
      setLockSecs((s) => {
        if (s <= 1) { clearInterval(t); load().catch(() => {}); return 0; }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [lockSecs > 0]);

  useEffect(() => {
    if (!status?.unlocked || secsLeft <= 0) return;
    const t = setInterval(() => {
      setSecsLeft((s) => {
        if (s <= 1) { clearInterval(t); setKeys([]); load().catch(() => {}); return 0; }
        return s - 1;
      });
    }, 1000);
    return () => clearInterval(t);
  }, [status?.unlocked, secsLeft > 0]);

  const mmss = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;

  const enrollTotp = async () => {
    const { data } = await api.post("/admin/vault/enroll/totp");
    setEnrollQr(data);
  };
  const verifyEnroll = async () => {
    setBusy(true);
    try { await api.post("/admin/vault/enroll/totp/verify", { code: enrollCode }); toast.success("Authenticator enrolled."); setEnrollQr(null); setEnrollCode(""); await load(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Invalid code"); }
    finally { setBusy(false); }
  };
  const registerNewPasskey = async () => {
    setBusy(true);
    try {
      const { data } = await api.post("/admin/vault/webauthn/register/options");
      const cred = await registerPasskey(data);
      await api.post("/admin/vault/webauthn/register/verify", cred);
      toast.success("Passkey registered (Face ID / fingerprint).");
      await load();
    } catch (e) { toast.error(e?.response?.data?.detail || e.message || "Passkey registration failed"); }
    finally { setBusy(false); }
  };
  const unlock = async () => {
    setBusy(true);
    try {
      await api.post("/admin/vault/unlock/totp", { code: unlockCode });
      const { data } = await api.post("/admin/vault/webauthn/auth/options");
      const cred = await authPasskey(data);
      await api.post("/admin/vault/webauthn/auth/verify", cred);
      toast.success("Vault unlocked.");
      setUnlockCode("");
      await load();
    } catch (e) { toast.error(e?.response?.data?.detail || e.message || "Unlock failed"); }
    finally { setBusy(false); }
  };
  const lock = async () => { await api.post("/admin/vault/lock"); setKeys([]); await load(); toast.success("Vault locked."); };
  const addKey = async () => {
    if (!label || !value) return;
    setBusy(true);
    try { await api.post("/admin/vault/keys", { label, value }); setLabel(""); setValue(""); const r = await api.get("/admin/vault/keys"); setKeys(r.data.keys || []); toast.success("Key stored (encrypted)."); }
    catch (e) { toast.error(e?.response?.data?.detail || "Could not store key"); }
    finally { setBusy(false); }
  };
  const delKey = async (id) => {
    await api.delete(`/admin/vault/keys/${id}`);
    setKeys((k) => k.filter((x) => x.id !== id));
    toast.success("Key removed.");
  };

  if (!status) return <div className="mt-8 text-muted-foreground" data-testid="vault-loading">Loading vault…</div>;

  return (
    <div className="mt-8 space-y-6" data-testid="vault-panel">
      <div className="rounded-2xl border border-border bg-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="flex items-center gap-2 font-display text-xl font-black"><KeyRound className="h-5 w-5 text-[hsl(var(--primary))]" /> Super-Admin Vault</h3>
            <p className="text-sm text-muted-foreground">Encrypted API-key vault. Unlock requires your authenticator code <span className="font-semibold">and</span> a device passkey.</p>
          </div>
          <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-xs font-semibold ${status.unlocked ? "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]" : "bg-secondary text-muted-foreground"}`} data-testid="vault-state">
            {status.unlocked ? <><Unlock className="h-3.5 w-3.5" /> Unlocked · auto-locks in <span className="font-mono tabular-nums" data-testid="vault-countdown">{mmss(secsLeft)}</span></> : <><Lock className="h-3.5 w-3.5" /> Locked</>}
          </span>
        </div>

        {!status.ready && <p className="mt-4 rounded-xl bg-red-500/10 px-4 py-3 text-sm text-red-500">Vault not configured (missing encryption / WebAuthn env).</p>}

        {status.last_unlock && (
          <p className="mt-3 text-xs text-muted-foreground" data-testid="vault-last-unlock">
            Last unlocked {new Date(status.last_unlock.at).toLocaleString()} by <span className="font-semibold text-foreground">{status.last_unlock.actor}</span> · <span className="font-mono">{status.last_unlock.ip}</span>
          </p>
        )}

        {/* Setup */}
        {status.ready && !status.unlocked && (
          <div className="mt-5 grid gap-5 lg:grid-cols-2">
            <div className="rounded-xl border border-border p-4">
              <h4 className="flex items-center gap-2 text-sm font-bold"><Smartphone className="h-4 w-4" /> 1 · Authenticator (TOTP) {status.totp_enrolled && <ShieldCheck className="h-4 w-4 text-[hsl(var(--primary))]" />}</h4>
              {!status.totp_enrolled ? (
                enrollQr ? (
                  <div className="mt-3">
                    <img src={enrollQr.qr} alt="QR" className="h-40 w-40 rounded-lg bg-white p-2" />
                    <p className="mt-2 break-all text-xs text-muted-foreground">Key: <code>{enrollQr.secret}</code></p>
                    <div className="mt-2 flex gap-2">
                      <input value={enrollCode} onChange={(e) => setEnrollCode(e.target.value.replace(/\D/g, "").slice(0, 6))} placeholder="6-digit" data-testid="vault-enroll-code" className="w-28 rounded-xl border border-border bg-background px-3 py-2 text-center font-mono outline-none focus:border-[hsl(var(--primary))]" />
                      <button onClick={verifyEnroll} disabled={busy} data-testid="vault-enroll-verify" className="rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-xs font-semibold text-[hsl(var(--primary-foreground))]">Confirm</button>
                    </div>
                  </div>
                ) : (
                  <button onClick={enrollTotp} data-testid="vault-enroll-totp" className="mt-3 rounded-full bg-[hsl(var(--accent))] px-4 py-2 text-xs font-semibold text-[hsl(var(--accent-foreground))]">Set up authenticator</button>
                )
              ) : <p className="mt-2 text-xs text-muted-foreground">Enrolled.</p>}
            </div>

            <div className="rounded-xl border border-border p-4">
              <h4 className="flex items-center gap-2 text-sm font-bold"><Fingerprint className="h-4 w-4" /> 2 · Passkey (Face ID / fingerprint) {status.passkey_enrolled && <ShieldCheck className="h-4 w-4 text-[hsl(var(--primary))]" />}</h4>
              {!passkeySupported() && <p className="mt-2 text-xs text-red-500">This browser/device has no passkey support.</p>}
              <button onClick={registerNewPasskey} disabled={busy || !passkeySupported()} data-testid="vault-register-passkey" className="mt-3 rounded-full bg-[hsl(var(--accent))] px-4 py-2 text-xs font-semibold text-[hsl(var(--accent-foreground))] disabled:opacity-50">
                {status.passkey_enrolled ? "Register another passkey" : "Register a passkey"}
              </button>
            </div>
          </div>
        )}

        {/* Unlock */}
        {status.ready && status.totp_enrolled && status.passkey_enrolled && !status.unlocked && (
          <div className="mt-5 rounded-xl border border-[hsl(var(--primary))]/30 bg-[hsl(var(--primary))]/5 p-4" data-testid="vault-unlock-box">
            <h4 className="text-sm font-bold">Unlock the vault</h4>
            <p className="text-xs text-muted-foreground">Enter your authenticator code, then approve with your passkey.</p>
            {lockSecs > 0 ? (
              <p className="mt-3 rounded-lg bg-red-500/10 px-4 py-3 text-sm font-medium text-red-500" data-testid="vault-frozen">
                <Lock className="mr-1.5 inline h-4 w-4" /> Unlocking frozen after {status.max_fails} failed attempts. Try again in <span className="font-mono tabular-nums" data-testid="vault-freeze-countdown">{mmss(lockSecs)}</span>.
              </p>
            ) : (
              <>
                {status.fails > 0 && (
                  <p className="mt-2 text-xs font-medium text-amber-500" data-testid="vault-fails-left">
                    {status.max_fails - status.fails} attempt{status.max_fails - status.fails !== 1 ? "s" : ""} left before the vault freezes.
                  </p>
                )}
                <div className="mt-3 flex flex-wrap gap-2">
                  <input value={unlockCode} onChange={(e) => setUnlockCode(e.target.value.replace(/\D/g, "").slice(0, 6))} placeholder="6-digit code" inputMode="numeric" data-testid="vault-unlock-code" className="w-36 rounded-xl border border-border bg-background px-3 py-2.5 text-center font-mono outline-none focus:border-[hsl(var(--primary))]" />
                  <button onClick={unlock} disabled={busy || unlockCode.length !== 6} data-testid="vault-unlock-btn" className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-60">
                    <Fingerprint className="h-4 w-4" /> Unlock with passkey
                  </button>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Unlocked contents */}
      {status.unlocked && (
        <div className="rounded-2xl border border-border bg-card p-6" data-testid="vault-keys">
          <div className="flex items-center justify-between">
            <h4 className="font-display text-lg font-bold">Stored secrets ({keys.length})</h4>
            <button onClick={lock} data-testid="vault-lock-btn" className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-2 text-xs font-medium hover:bg-secondary"><Lock className="h-3.5 w-3.5" /> Lock now</button>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            <input value={label} onChange={(e) => setLabel(e.target.value)} placeholder="Label (e.g. Stripe live key)" data-testid="vault-key-label" className="flex-1 min-w-[160px] rounded-xl border border-border bg-background px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]" />
            <input value={value} onChange={(e) => setValue(e.target.value)} placeholder="Secret value" data-testid="vault-key-value" className="flex-1 min-w-[160px] rounded-xl border border-border bg-background px-3 py-2 text-sm font-mono outline-none focus:border-[hsl(var(--primary))]" />
            <button onClick={addKey} disabled={busy} data-testid="vault-key-add" className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-sm font-semibold text-[hsl(var(--primary-foreground))]"><Plus className="h-4 w-4" /> Add</button>
          </div>
          <div className="mt-4 space-y-2">
            {keys.length === 0 && <p className="text-sm text-muted-foreground">No secrets stored yet.</p>}
            {keys.map((k) => (
              <div key={k.id} className="flex items-center justify-between gap-3 rounded-xl border border-border px-4 py-3" data-testid={`vault-key-${k.id}`}>
                <div className="min-w-0">
                  <p className="text-sm font-semibold">{k.label}</p>
                  <p className="truncate font-mono text-xs text-muted-foreground">{reveal[k.id] ? k.value : "•".repeat(Math.min(24, k.value.length))}</p>
                </div>
                <div className="flex items-center gap-2">
                  <button onClick={() => setReveal((r) => ({ ...r, [k.id]: !r[k.id] }))} data-testid={`vault-reveal-${k.id}`} className="text-muted-foreground hover:text-foreground">{reveal[k.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}</button>
                  <button onClick={() => delKey(k.id)} data-testid={`vault-del-${k.id}`} className="text-red-500 hover:text-red-400"><Trash2 className="h-4 w-4" /></button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
