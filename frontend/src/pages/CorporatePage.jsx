import { useState } from "react";
import { toast } from "sonner";
import { Building2, ArrowRight, Check } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";
import Captcha from "@/components/Captcha";

const BUDGETS = ["Under ₹5L", "₹5L – ₹15L", "₹15L – ₹50L", "₹50L+", "Not sure yet"];
const ENGAGEMENTS = ["Strategy advisory (retainer)", "Leadership development / cohort", "Fundraising & bankability", "Board / one-off masterclass", "Something else"];

const BENEFITS = [
  "A named senior advisor — not a rotating team",
  "Board-ready strategy, capital and scaling counsel",
  "Custom leadership programs for your executive bench",
  "NDA-backed, confidential engagements",
];

export default function CorporatePage() {
  const [form, setForm] = useState({ name: "", email: "", company: "", phone: "", budget: BUDGETS[0], engagement: ENGAGEMENTS[0], message: "" });
  const [captcha, setCaptcha] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.company) { toast.error("Please add your name, work email and company."); return; }
    if (!captcha) { toast.error("Please complete the captcha."); return; }
    setBusy(true);
    try {
      const { data } = await api.post("/corporate/inquiry", { ...form, captcha_token: captcha });
      toast.success(data.message);
      setDone(true);
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Something went wrong.");
    } finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Corporate & Enterprise — Sudarshan Karweer" description="Retained advisory and custom leadership programs for companies, boards and executive teams." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-40 lg:pt-48">
        <div className="pointer-events-none absolute -right-40 top-20 h-96 w-96 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 lg:px-10">
          <p className="inline-flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]"><Building2 className="h-4 w-4" /> Corporate & Enterprise</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-extrabold tracking-tight sm:text-5xl">Bring Sudarshan into your boardroom.</h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">Retained advisory, custom leadership programs and board-level counsel for companies scaling through complexity. Tell us what you're solving — we'll design the engagement around it.</p>
        </div>
      </section>

      <div className="mx-auto grid max-w-7xl gap-12 px-6 pb-24 lg:grid-cols-2 lg:px-10">
        <div>
          <h2 className="font-display text-2xl font-bold">What an enterprise engagement includes</h2>
          <ul className="mt-6 space-y-4">
            {BENEFITS.map((b) => (
              <li key={b} className="flex items-start gap-3 text-sm text-muted-foreground">
                <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-[hsl(var(--primary))]/15"><Check className="h-3.5 w-3.5 text-[hsl(var(--primary))]" /></span>
                {b}
              </li>
            ))}
          </ul>
        </div>

        {done ? (
          <div className="rounded-3xl border border-border bg-card p-8" data-testid="corporate-done">
            <div className="grid h-12 w-12 place-items-center rounded-full bg-[hsl(var(--primary))]/15"><Check className="h-6 w-6 text-[hsl(var(--primary))]" /></div>
            <h3 className="mt-4 font-display text-xl font-bold">Your enquiry is with Sudarshan's team.</h3>
            <p className="mt-2 text-sm text-muted-foreground">We review every enterprise request personally and will be in touch shortly to scope the engagement.</p>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-3 rounded-3xl border border-border bg-card p-7" data-testid="corporate-form">
            <div className="grid gap-3 sm:grid-cols-2">
              <input value={form.name} onChange={set("name")} placeholder="Full name" data-testid="corp-name" className="rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
              <input value={form.company} onChange={set("company")} placeholder="Company" data-testid="corp-company" className="rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
              <input value={form.email} onChange={set("email")} type="email" placeholder="Work email" data-testid="corp-email" className="rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
              <input value={form.phone} onChange={set("phone")} placeholder="Phone (optional)" data-testid="corp-phone" className="rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
            </div>
            <select value={form.engagement} onChange={set("engagement")} data-testid="corp-engagement" className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]">
              {ENGAGEMENTS.map((o) => <option key={o}>{o}</option>)}
            </select>
            <select value={form.budget} onChange={set("budget")} data-testid="corp-budget" className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]">
              {BUDGETS.map((o) => <option key={o}>{o}</option>)}
            </select>
            <textarea value={form.message} onChange={set("message")} rows={4} placeholder="What are you trying to achieve?" data-testid="corp-message" className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
            <div className="flex justify-center"><Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} /></div>
            <button type="submit" disabled={busy} data-testid="corp-submit" className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3.5 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
              {busy ? "Sending…" : <>Request a conversation <ArrowRight className="h-4 w-4" /></>}
            </button>
          </form>
        )}
      </div>
      <Footer />
    </div>
  );
}
