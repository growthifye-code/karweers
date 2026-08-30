import { useState, useEffect } from "react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { Mail, Phone, MessageCircle, Quote, Check, ArrowUpRight } from "lucide-react";
import api from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";
import { CONTACT } from "@/lib/assets";

const AREAS = [
  "Fundraising", "Strategy", "New Business Development", "Scaling Current Business",
  "Renewable Energy Advisory", "Energy Storage / BESS", "Green Hydrogen",
  "Green / Climate Financing", "Government Asset Monetisation", "Business Coaching",
];

export default function Consultation({ testimonials = [] }) {
  const [packages, setPackages] = useState([]);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState({ name: "", email: "", phone: "", company: "", area: AREAS[0], message: "" });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/payments/packages").then((r) => setPackages(r.data)).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || (!selected && !form.message)) {
      toast.error("Please fill in your name, email and message.");
      return;
    }
    setBusy(true);
    try {
      if (selected) {
        const { data } = await api.post("/payments/checkout", {
          package_id: selected, origin_url: window.location.origin,
          name: form.name, email: form.email, phone: form.phone, area: form.area, message: form.message,
        });
        window.location.href = data.checkout_url;
        return;
      }
      const { data } = await api.post("/consultations", {
        name: form.name, email: form.email, phone: form.phone, company: form.company, area: form.area, message: form.message,
      });
      toast.success(data.message || "Request received!");
      setForm({ name: "", email: "", phone: "", company: "", area: AREAS[0], message: "" });
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const selectedPkg = packages.find((p) => p.id === selected);

  return (
    <section id="consult" className="scroll-mt-24 border-t border-border bg-[hsl(var(--primary))] py-24 text-[hsl(var(--primary-foreground))] lg:py-32" data-testid="consultation">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Premium 1:1 Consultation</p>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">Reserve decision-grade counsel, directly with Sudarshan.</h2>
          <p className="mt-4 max-w-xl leading-relaxed text-[hsl(var(--primary-foreground))]/80">
            Choose a session and pay securely to book, or send a general enquiry below.
          </p>
        </div>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {packages.map((p) => {
            const active = selected === p.id;
            return (
              <button
                key={p.id}
                onClick={() => setSelected(active ? null : p.id)}
                data-testid={`package-${p.id}`}
                className={`group rounded-2xl border p-7 text-left transition-transform hover:-translate-y-1 ${active ? "border-[hsl(var(--accent))] bg-white/15" : "border-white/15 bg-white/5"}`}
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-display text-xl font-bold">{p.name}</h3>
                  {active && <span className="grid h-6 w-6 place-items-center rounded-full bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]"><Check className="h-3.5 w-3.5" /></span>}
                </div>
                <p className="mt-1 text-xs uppercase tracking-wide text-white/60">{p.duration}</p>
                <p className="mt-4 font-display text-3xl font-black text-[hsl(var(--accent))]">${p.amount}</p>
                <ul className="mt-4 space-y-2 text-sm text-white/80">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2"><Check className="mt-0.5 h-4 w-4 flex-shrink-0 text-[hsl(var(--accent))]" /> {f}</li>
                  ))}
                </ul>
              </button>
            );
          })}
        </div>

        <div className="mt-12 grid gap-10 lg:grid-cols-[1fr_1.1fr]">
          <div>
            <div className="flex flex-wrap gap-4 text-sm">
              <a href={`mailto:${CONTACT.email}`} data-testid="contact-email" className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 transition-colors hover:bg-white/20"><Mail className="h-4 w-4" /> {CONTACT.email}</a>
              <a href={`tel:${CONTACT.phoneRaw}`} data-testid="contact-phone" className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 transition-colors hover:bg-white/20"><Phone className="h-4 w-4" /> {CONTACT.phone}</a>
              <a href={`https://wa.me/${CONTACT.whatsapp}`} target="_blank" rel="noreferrer" data-testid="contact-whatsapp" className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 transition-colors hover:bg-white/20"><MessageCircle className="h-4 w-4" /> WhatsApp</a>
            </div>
            <div className="mt-8 space-y-4">
              {testimonials.map((t, i) => (
                <motion.div key={i} initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.4, delay: i * 0.08 }} className="rounded-2xl bg-white/10 p-5">
                  <Quote className="h-5 w-5 text-[hsl(var(--accent))]" />
                  <p className="mt-2 text-sm italic leading-relaxed">"{t.quote}"</p>
                  <p className="mt-2 text-xs font-semibold">{t.name} · <span className="opacity-70">{t.role}</span></p>
                </motion.div>
              ))}
            </div>
          </div>

          <form onSubmit={submit} className="rounded-2xl bg-card p-8 text-foreground" data-testid="consult-form">
            <h3 className="font-display text-xl font-bold">{selected ? `Book: ${selectedPkg?.name}` : "Send a general enquiry"}</h3>
            {selected && <p className="mt-1 text-sm text-muted-foreground">You'll be redirected to secure Stripe checkout to pay ${selectedPkg?.amount}.</p>}
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <input value={form.name} onChange={set("name")} data-testid="consult-name" placeholder="Full name *" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <input value={form.email} onChange={set("email")} data-testid="consult-email" type="email" placeholder="Email *" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <input value={form.phone} onChange={set("phone")} data-testid="consult-phone" placeholder="Phone" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <input value={form.company} onChange={set("company")} data-testid="consult-company" placeholder="Company" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            </div>
            <select value={form.area} onChange={set("area")} data-testid="consult-area" className="mt-4 w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]">
              {AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
            <textarea value={form.message} onChange={set("message")} data-testid="consult-message" placeholder={selected ? "Anything to share before the session (optional)" : "Tell me about your business and what you'd like to achieve *"} rows={4} className="mt-4 w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            <button type="submit" disabled={busy} data-testid="consult-submit" className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[hsl(var(--accent))] px-6 py-3.5 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
              {busy ? "Please wait…" : selected ? <>Reserve & Pay ${selectedPkg?.amount} <ArrowUpRight className="h-4 w-4" /></> : "Send Enquiry"}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
