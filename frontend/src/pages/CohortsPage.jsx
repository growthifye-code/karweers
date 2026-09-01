import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { Users, CalendarClock, ArrowUpRight, Clock, Star } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";
import Captcha from "@/components/Captcha";
import CommerceCheckoutModal from "@/components/CommerceCheckoutModal";

const inr = (v) => "\u20b9" + Number(v || 0).toLocaleString("en-IN");

function WaitlistForm({ slug, onClose }) {
  const [form, setForm] = useState({ name: "", email: "" });
  const [captcha, setCaptcha] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (e) => {
    e.preventDefault();
    if (!form.email) { toast.error("Please enter your email."); return; }
    if (!captcha) { toast.error("Please complete the captcha."); return; }
    setBusy(true);
    try {
      const { data } = await api.post(`/cohorts/${slug}/waitlist`, { email: form.email, name: form.name, captcha_token: captcha });
      toast.success(data.message);
      onClose();
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Could not join the waitlist.");
    } finally { setBusy(false); }
  };
  return (
    <form onSubmit={submit} className="mt-4 space-y-3 rounded-2xl border border-border bg-background p-4" data-testid={`waitlist-${slug}`}>
      <p className="text-sm font-semibold">Join the waitlist</p>
      <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm outline-none focus:border-[hsl(var(--primary))]" />
      <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} type="email" placeholder="you@company.com" className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-sm outline-none focus:border-[hsl(var(--primary))]" />
      <div className="flex justify-center"><Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} /></div>
      <button type="submit" disabled={busy} className="w-full rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-60">{busy ? "Joining…" : "Notify me of the next seat"}</button>
    </form>
  );
}

export default function CohortsPage() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [checkout, setCheckout] = useState(null);
  const [waitlist, setWaitlist] = useState(null);
  const [best, setBest] = useState({});
  const [params] = useSearchParams();
  const promoCode = params.get("code") || "";
  const autoCohort = params.get("cohort") || "";

  const load = () => api.get("/cohorts").then((r) => setItems(r.data)).catch(() => {}).finally(() => setLoading(false));
  useEffect(() => { load(); api.get("/commerce/best-sellers").then((r) => setBest(r.data)).catch(() => {}); }, []);

  useEffect(() => {
    if (autoCohort && items.length) {
      const c = items.find((x) => x.slug === autoCohort && x.seats_left > 0);
      if (c) setCheckout({ kind: "cohort", ref_id: c.slug, title: c.title, price: c.price });
    }
  }, [autoCohort, items]);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Cohorts & Masterclasses — Sudarshan Karweer" description="Live, small-group leadership cohorts and masterclasses with Sudarshan Karweer. Seats are deliberately limited." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-40 lg:pt-48">
        <div className="pointer-events-none absolute -left-40 top-20 h-96 w-96 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Live · Small-group</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-extrabold tracking-tight sm:text-5xl">Cohorts & Masterclasses.</h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">Work directly with Sudarshan in a small, high-trust room. Live sessions, peer accountability and a plan you actually execute. Seats are deliberately limited.</p>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 pb-24 lg:px-10">
        {loading ? (
          <p className="py-16 text-center text-muted-foreground">Loading…</p>
        ) : items.length === 0 ? (
          <p className="py-16 text-center text-muted-foreground">New cohorts are being scheduled — check back soon.</p>
        ) : (
          <div className="grid gap-6 lg:grid-cols-2" data-testid="cohorts-grid">
            {items.map((c) => {
              const full = c.seats_left <= 0;
              const scarce = c.seats_left > 0 && c.seats_left <= 5;
              return (
                <div key={c.slug} data-testid={`cohort-${c.slug}`} className="relative flex flex-col rounded-3xl border border-border bg-card p-7">
                  {best.cohort === c.slug && (
                    <span data-testid={`best-seller-${c.slug}`} className="absolute -top-3 right-6 inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-3 py-1 text-xs font-bold text-[hsl(var(--primary-foreground))] shadow-lg"><Star className="h-3.5 w-3.5" /> Most popular</span>
                  )}
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <h3 className="font-display text-2xl font-bold leading-tight">{c.title}</h3>
                      {c.subtitle && <p className="mt-1.5 text-sm font-medium text-[hsl(var(--primary))]">{c.subtitle}</p>}
                    </div>
                    <span className={`shrink-0 rounded-full px-3 py-1 text-xs font-bold ${full ? "bg-destructive/15 text-destructive" : scarce ? "bg-[hsl(var(--accent))]/20 text-[hsl(var(--accent))]" : "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]"}`} data-testid={`cohort-seats-${c.slug}`}>
                      {full ? "Full" : `${c.seats_left} seat${c.seats_left === 1 ? "" : "s"} left`}
                    </span>
                  </div>
                  <p className="mt-4 flex-1 text-sm leading-relaxed text-muted-foreground">{c.description}</p>
                  <div className="mt-5 flex flex-wrap gap-4 text-xs text-muted-foreground">
                    {c.schedule && <span className="inline-flex items-center gap-1.5"><Clock className="h-3.5 w-3.5 text-[hsl(var(--primary))]" /> {c.schedule}</span>}
                    {c.start_date && <span className="inline-flex items-center gap-1.5"><CalendarClock className="h-3.5 w-3.5 text-[hsl(var(--primary))]" /> Starts {c.start_date}</span>}
                    <span className="inline-flex items-center gap-1.5"><Users className="h-3.5 w-3.5 text-[hsl(var(--primary))]" /> {c.seats_total} seats total</span>
                  </div>
                  <div className="mt-6 flex items-center justify-between">
                    <span className="font-display text-2xl font-extrabold">{inr(c.price)}</span>
                    {full ? (
                      <button onClick={() => setWaitlist(waitlist === c.slug ? null : c.slug)} data-testid={`cohort-waitlist-btn-${c.slug}`} className="rounded-full border border-border px-5 py-2.5 text-sm font-semibold hover:bg-secondary">Join waitlist</button>
                    ) : (
                      <button onClick={() => setCheckout({ kind: "cohort", ref_id: c.slug, title: c.title, price: c.price })} data-testid={`cohort-cta-${c.slug}`}
                        className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                        Reserve my seat <ArrowUpRight className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  {waitlist === c.slug && <WaitlistForm slug={c.slug} onClose={() => setWaitlist(null)} />}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <CommerceCheckoutModal open={!!checkout} item={checkout} initialCode={promoCode} onClose={() => setCheckout(null)} onDone={() => load()} />
      <Footer />
    </div>
  );
}
