import { useState } from "react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { Mail, Phone, MessageCircle, Quote } from "lucide-react";
import api from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";

const AREAS = [
  "Fundraising", "Strategy", "New Business Development", "Scaling Current Business",
  "Renewable Energy Advisory", "Energy Storage / BESS", "Green Hydrogen",
  "Green / Climate Financing", "Government Asset Monetisation", "Business Coaching",
];

export default function Consultation({ testimonials = [] }) {
  const [form, setForm] = useState({ name: "", email: "", phone: "", company: "", area: AREAS[0], message: "" });
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.message) {
      toast.error("Please fill in your name, email and message.");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post("/consultations", form);
      toast.success(data.message || "Request received!");
      setForm({ name: "", email: "", phone: "", company: "", area: AREAS[0], message: "" });
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  return (
    <section id="consult" className="scroll-mt-24 border-t border-border bg-[hsl(var(--primary))] py-24 text-[hsl(var(--primary-foreground))] lg:py-32" data-testid="consultation">
      <div className="mx-auto grid max-w-7xl gap-14 px-6 lg:grid-cols-[1fr_1.1fr] lg:px-10">
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Premium 1:1 Consultation</p>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Decision-grade counsel, directly with Sudarshan.
          </h2>
          <p className="mt-5 max-w-md leading-relaxed text-[hsl(var(--primary-foreground))]/80">
            For business owners in renewable energy and storage looking to raise capital, sharpen strategy,
            develop new business or scale — book a focused, high-signal session.
          </p>

          <div className="mt-8 flex flex-wrap gap-4 text-sm">
            <a href="mailto:sudarshan@karweers.com" className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 transition-colors hover:bg-white/20"><Mail className="h-4 w-4" /> Email</a>
            <a href="tel:+919999999999" className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 transition-colors hover:bg-white/20"><Phone className="h-4 w-4" /> Call</a>
            <a href="https://wa.me/919999999999" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 rounded-full bg-white/10 px-4 py-2 transition-colors hover:bg-white/20"><MessageCircle className="h-4 w-4" /> WhatsApp</a>
          </div>

          <div className="mt-10 space-y-4">
            {testimonials.map((t, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 12 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.08 }}
                className="rounded-2xl bg-white/10 p-5"
              >
                <Quote className="h-5 w-5 text-[hsl(var(--accent))]" />
                <p className="mt-2 text-sm italic leading-relaxed">"{t.quote}"</p>
                <p className="mt-2 text-xs font-semibold">{t.name} · <span className="opacity-70">{t.role}</span></p>
              </motion.div>
            ))}
          </div>
        </div>

        <form onSubmit={submit} className="rounded-2xl bg-card p-8 text-foreground" data-testid="consult-form">
          <h3 className="font-display text-xl font-bold">Request your consultation</h3>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <input value={form.name} onChange={set("name")} data-testid="consult-name" placeholder="Full name *" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            <input value={form.email} onChange={set("email")} data-testid="consult-email" type="email" placeholder="Email *" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            <input value={form.phone} onChange={set("phone")} data-testid="consult-phone" placeholder="Phone" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            <input value={form.company} onChange={set("company")} data-testid="consult-company" placeholder="Company" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
          </div>
          <select value={form.area} onChange={set("area")} data-testid="consult-area" className="mt-4 w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]">
            {AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
          <textarea value={form.message} onChange={set("message")} data-testid="consult-message" placeholder="Tell me about your business and what you'd like to achieve *" rows={4} className="mt-4 w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
          <button type="submit" disabled={busy} data-testid="consult-submit" className="mt-5 w-full rounded-full bg-[hsl(var(--accent))] px-6 py-3.5 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
            {busy ? "Sending…" : "Request Consultation"}
          </button>
        </form>
      </div>
    </section>
  );
}
