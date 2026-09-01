import { useState } from "react";
import { X, Lock, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import Captcha from "@/components/Captcha";
import { startCommerceCheckout } from "@/lib/checkout";

const inr = (v) => "\u20b9" + Number(v || 0).toLocaleString("en-IN");

export default function CommerceCheckoutModal({ open, item, meta, onClose, onDone }) {
  const [form, setForm] = useState({ name: "", email: "", phone: "" });
  const [captcha, setCaptcha] = useState("");
  const [busy, setBusy] = useState(false);
  if (!open || !item) return null;

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const pay = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email) { toast.error("Please add your name and email."); return; }
    if (!captcha) { toast.error("Please complete the captcha."); return; }
    setBusy(true);
    const res = await startCommerceCheckout({
      kind: item.kind, ref_id: item.ref_id, name: form.name, email: form.email,
      phone: form.phone, captcha_token: captcha, meta: meta || undefined,
    }, (result) => { onDone && onDone(result); onClose(); });
    setBusy(false);
    if (!res.ok && !res.waitlist) { /* toast already shown */ }
    if (res.waitlist) onClose();
  };

  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-black/70 p-4 backdrop-blur-sm" data-testid="checkout-modal" onClick={onClose}>
      <div className="w-full max-w-md rounded-3xl border border-border bg-card p-7 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Secure checkout</p>
            <h3 className="mt-1 font-display text-xl font-bold leading-tight">{item.title}</h3>
          </div>
          <button onClick={onClose} data-testid="checkout-close" className="grid h-9 w-9 place-items-center rounded-full border border-border hover:bg-secondary"><X className="h-4 w-4" /></button>
        </div>
        <p className="mt-3 font-display text-3xl font-extrabold">{inr(item.price)}</p>
        <form onSubmit={pay} className="mt-5 space-y-3">
          <input value={form.name} onChange={set("name")} placeholder="Full name" data-testid="checkout-name"
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
          <input value={form.email} onChange={set("email")} type="email" placeholder="you@company.com" data-testid="checkout-email"
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
          <input value={form.phone} onChange={set("phone")} placeholder="Phone (optional)" data-testid="checkout-phone"
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
          <div className="flex justify-center"><Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} /></div>
          <button type="submit" disabled={busy} data-testid="checkout-pay"
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3.5 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
            <Lock className="h-4 w-4" /> {busy ? "Starting…" : `Pay ${inr(item.price)}`}
          </button>
        </form>
        <p className="mt-3 flex items-center justify-center gap-1.5 text-[11px] text-muted-foreground"><ShieldCheck className="h-3.5 w-3.5" /> Paid securely via Razorpay · GST invoice on request</p>
      </div>
    </div>
  );
}
