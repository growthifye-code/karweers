import { useState, useEffect, useCallback } from "react";
import { X, Lock, ShieldCheck, Tag, Check, Gift } from "lucide-react";
import { toast } from "sonner";
import api from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";
import Captcha from "@/components/Captcha";
import { startCommerceCheckout } from "@/lib/checkout";

const inr = (v) => "\u20b9" + Number(v || 0).toLocaleString("en-IN");

export default function CommerceCheckoutModal({ open, item, meta, initialCode, onClose, onDone }) {
  const [form, setForm] = useState({ name: "", email: "", phone: "" });
  const [captcha, setCaptcha] = useState("");
  const [busy, setBusy] = useState(false);
  const [code, setCode] = useState("");
  const [applying, setApplying] = useState(false);
  const [promo, setPromo] = useState(null); // {code, label, final_price, discount}
  const [isGift, setIsGift] = useState(false);
  const [gift, setGift] = useState({ recipient_name: "", recipient_email: "", message: "" });

  const validateCode = useCallback(async (raw, silent = false) => {
    const c = (raw || "").trim();
    if (!c || !item) return;
    setApplying(true);
    try {
      const { data } = await api.post("/promo/validate", { code: c, kind: item.kind, ref_id: item.ref_id });
      if (data.valid) { setPromo(data); if (!silent) toast.success(`${data.label} applied.`); }
      else { setPromo(null); if (!silent) toast.error(data.message || "That code isn't valid."); }
    } catch (err) {
      setPromo(null);
      if (!silent) toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Couldn't check that code.");
    } finally { setApplying(false); }
  }, [item]);

  // Auto-apply a code passed via a shareable campaign link (?code=...).
  useEffect(() => {
    if (open && item && initialCode) {
      setCode(initialCode.toUpperCase());
      validateCode(initialCode, true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, item?.ref_id, initialCode]);

  if (!open || !item) return null;

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const price = promo ? promo.final_price : item.price;
  const clearPromo = () => { setPromo(null); setCode(""); };

  const pay = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email) { toast.error("Please add your name and email."); return; }
    if (isGift && (!gift.recipient_name || !gift.recipient_email)) { toast.error("Please add the recipient's name and email."); return; }
    if (!captcha) { toast.error("Please complete the captcha."); return; }
    setBusy(true);
    const res = await startCommerceCheckout({
      kind: item.kind, ref_id: item.ref_id, name: form.name, email: form.email,
      phone: form.phone, captcha_token: captcha, promo_code: promo ? promo.code : undefined,
      gift: isGift ? gift : undefined,
      meta: meta || undefined,
    }, (result) => { onDone && onDone(result); onClose(); });
    setBusy(false);
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
        <div className="mt-3 flex items-baseline gap-2">
          <p className="font-display text-3xl font-extrabold" data-testid="checkout-price">{inr(price)}</p>
          {promo && <span className="text-sm text-muted-foreground line-through">{inr(item.price)}</span>}
          {promo && <span className="rounded-full bg-[hsl(var(--primary))]/15 px-2.5 py-0.5 text-xs font-semibold text-[hsl(var(--primary))]">{promo.label}</span>}
        </div>

        <form onSubmit={pay} className="mt-5 space-y-3">
          <input value={form.name} onChange={set("name")} placeholder="Full name" data-testid="checkout-name"
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
          <input value={form.email} onChange={set("email")} type="email" placeholder="you@company.com" data-testid="checkout-email"
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
          <input value={form.phone} onChange={set("phone")} placeholder="Phone (optional)" data-testid="checkout-phone"
            className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />

          <label className="flex cursor-pointer items-center gap-2.5 rounded-xl border border-border bg-background px-4 py-3 text-sm" data-testid="gift-toggle">
            <input type="checkbox" checked={isGift} onChange={(e) => setIsGift(e.target.checked)} data-testid="gift-checkbox" />
            <Gift className="h-4 w-4 text-[hsl(var(--primary))]" /> This is a gift for someone else
          </label>
          {isGift && (
            <div className="space-y-3 rounded-xl border border-[hsl(var(--primary))]/30 bg-[hsl(var(--primary))]/5 p-3" data-testid="gift-fields">
              <input value={gift.recipient_name} onChange={(e) => setGift({ ...gift, recipient_name: e.target.value })} placeholder="Recipient's name" data-testid="gift-name"
                className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:border-[hsl(var(--primary))]" />
              <input value={gift.recipient_email} onChange={(e) => setGift({ ...gift, recipient_email: e.target.value })} type="email" placeholder="Recipient's email" data-testid="gift-email"
                className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:border-[hsl(var(--primary))]" />
              <textarea value={gift.message} onChange={(e) => setGift({ ...gift, message: e.target.value })} rows={2} placeholder="Add a short message (optional)" data-testid="gift-message"
                className="w-full rounded-xl border border-border bg-background px-4 py-2.5 text-sm outline-none focus:border-[hsl(var(--primary))]" />
              <p className="text-xs text-muted-foreground">We'll email access straight to them.</p>
            </div>
          )}

          {promo ? (
            <div className="flex items-center justify-between rounded-xl border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/8 px-4 py-2.5 text-sm" data-testid="promo-applied">
              <span className="inline-flex items-center gap-1.5 font-semibold text-[hsl(var(--primary))]"><Check className="h-4 w-4" /> {promo.code} · {promo.label}</span>
              <button type="button" onClick={clearPromo} data-testid="promo-remove" className="text-xs text-muted-foreground hover:text-foreground">Remove</button>
            </div>
          ) : (
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Tag className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <input value={code} onChange={(e) => setCode(e.target.value.toUpperCase())} placeholder="Promo code" data-testid="promo-input"
                  className="w-full rounded-xl border border-border bg-background pl-9 pr-3 py-3 text-sm uppercase outline-none focus:border-[hsl(var(--primary))]" />
              </div>
              <button type="button" onClick={() => validateCode(code)} disabled={applying || !code.trim()} data-testid="promo-apply"
                className="rounded-xl border border-border px-4 py-3 text-sm font-semibold hover:bg-secondary disabled:opacity-50">{applying ? "…" : "Apply"}</button>
            </div>
          )}

          <div className="flex justify-center"><Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} /></div>
          <button type="submit" disabled={busy} data-testid="checkout-pay"
            className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3.5 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
            <Lock className="h-4 w-4" /> {busy ? "Starting…" : `Pay ${inr(price)}`}
          </button>
        </form>
        <p className="mt-3 flex items-center justify-center gap-1.5 text-[11px] text-muted-foreground"><ShieldCheck className="h-3.5 w-3.5" /> Paid securely via Razorpay · GST invoice on request</p>
      </div>
    </div>
  );
}
