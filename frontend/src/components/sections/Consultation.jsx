import { useState, useEffect } from "react";
import { toast } from "sonner";
import { motion } from "framer-motion";
import { Mail, Phone, MessageCircle, Quote, Check, ArrowUpRight, CalendarClock, Clock } from "lucide-react";
import api from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";
import { CONTACT } from "@/lib/assets";
import Captcha from "@/components/Captcha";

const AREAS = [
  "Fundraising", "Strategy", "New Business Development", "Scaling Current Business",
  "Renewable Energy Advisory", "Energy Storage / BESS", "Green Hydrogen",
  "Green / Climate Financing", "Government Asset Monetisation", "Business Coaching",
];

const inr = (v) => "\u20b9" + Number(v || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 });

function loadRazorpay() {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const s = document.createElement("script");
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.body.appendChild(s);
  });
}

export default function Consultation({ testimonials = [] }) {
  const [packages, setPackages] = useState([]);
  const [selected, setSelected] = useState(null);
  const [avail, setAvail] = useState({ days: [], hours: "", days_label: "" });
  const [selDate, setSelDate] = useState("");
  const [selTime, setSelTime] = useState("");
  const [wlDate, setWlDate] = useState("");
  const [form, setForm] = useState({ name: "", email: "", phone: "", company: "", area: AREAS[0], message: "" });
  const [captcha, setCaptcha] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/consultation/packages").then((r) => setPackages(r.data)).catch(() => {});
    api.get("/consultation/availability").then((r) => setAvail(r.data)).catch(() => {});
  }, []);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const dayObj = avail.days.find((d) => d.date === selDate);
  const selectedPkg = packages.find((p) => p.id === selected);

  const joinWaitlist = async () => {
    if (!form.name || !form.email) { toast.error("Please add your name and email above first."); return; }
    if (!captcha) { toast.error("Please complete the captcha."); return; }
    setBusy(true);
    try {
      const { data } = await api.post("/consultation/waitlist", { name: form.name, email: form.email, package_id: selected, date: wlDate, captcha_token: captcha });
      toast.success(data.message || "You're on the waitlist.");
      setWlDate("");
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Could not join the waitlist.");
    } finally {
      setBusy(false);
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email) { toast.error("Please fill in your name and email."); return; }
    if (!captcha) { toast.error("Please complete the captcha."); return; }
    if (selected && (!selDate || !selTime)) { toast.error("Please pick an available date and time."); return; }
    if (!selected && !form.message) { toast.error("Please tell us a bit about what you'd like to achieve."); return; }
    setBusy(true);
    try {
      if (selected) {
        const { data } = await api.post("/consultation/book", {
          package_id: selected, name: form.name, email: form.email, phone: form.phone,
          area: form.area, message: form.message, date: selDate, time: selTime, captcha_token: captcha,
        });
        await openCheckout(data);
      } else {
        const { data } = await api.post("/consultations", {
          name: form.name, email: form.email, phone: form.phone, company: form.company,
          area: form.area, message: form.message, captcha_token: captcha,
        });
        toast.success(data.message || "Request received!");
        setForm({ name: "", email: "", phone: "", company: "", area: AREAS[0], message: "" });
      }
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  const refreshAvail = () => api.get("/consultation/availability").then((r) => setAvail(r.data)).catch(() => {});

  const openCheckout = async (data) => {
    const ok = await loadRazorpay();
    if (!ok) {
      toast.error("Couldn't load the secure payment window. Please try again.");
      await api.post(`/payments/abandon/${data.booking_id}`).catch(() => {});
      return;
    }
    const rzp = new window.Razorpay({
      key: data.key_id,
      amount: data.amount,
      currency: data.currency,
      name: "Sudarshan Karweer",
      description: `${data.package} · ${selDate} ${selTime} IST`,
      order_id: data.order_id,
      prefill: data.prefill,
      theme: { color: "#0A0A0A" },
      handler: async (resp) => {
        try {
          const v = await api.post("/payments/verify", {
            booking_id: data.booking_id,
            razorpay_order_id: resp.razorpay_order_id,
            razorpay_payment_id: resp.razorpay_payment_id,
            razorpay_signature: resp.razorpay_signature,
          });
          toast.success(v.data.message || "Payment received! Your slot is reserved and pending confirmation.");
          setSelected(null); setSelDate(""); setSelTime("");
          setForm({ name: "", email: "", phone: "", company: "", area: AREAS[0], message: "" });
          refreshAvail();
        } catch (e) {
          toast.error("We couldn't verify the payment. If any amount was deducted, it is automatically refunded.");
        }
      },
      modal: {
        ondismiss: async () => {
          await api.post(`/payments/abandon/${data.booking_id}`).catch(() => {});
          toast("Payment cancelled — the slot has been released.");
          refreshAvail();
        },
      },
    });
    rzp.on("payment.failed", () => toast.error("Payment failed. Please try again or use another method."));
    rzp.open();
  };

  return (
    <section id="consult" className="scroll-mt-24 border-t border-border bg-[hsl(var(--primary))] py-24 text-[hsl(var(--primary-foreground))] lg:py-32" data-testid="consultation">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Premium 1:1 Consultation</p>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">Reserve decision-grade counsel, directly with Sudarshan.</h2>
          <p className="mt-4 max-w-xl leading-relaxed text-[hsl(var(--primary-foreground))]/80">
            Pick a session, choose an available slot and request your booking — Sudarshan's team confirms every session personally. Or send a general enquiry below.
          </p>
        </div>

        <div className="mt-12 grid gap-5 md:grid-cols-3">
          {packages.map((p) => {
            const active = selected === p.id;
            return (
              <button
                key={p.id}
                onClick={() => { setSelected(active ? null : p.id); setSelDate(""); setSelTime(""); }}
                data-testid={`package-${p.id}`}
                className={`group rounded-2xl border bg-[hsl(var(--card))] p-7 text-left transition-transform hover:-translate-y-1 ${active ? "border-[hsl(var(--primary))] ring-2 ring-[hsl(var(--primary))]" : "border-border"}`}
              >
                <div className="flex items-center justify-between">
                  <h3 className="font-display text-2xl font-extrabold text-foreground">{p.name}</h3>
                  {active && <span className="grid h-6 w-6 place-items-center rounded-full bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]"><Check className="h-3.5 w-3.5" /></span>}
                </div>
                <p className="mt-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">{p.duration}</p>
                <p className="mt-4 flex items-baseline gap-2">
                  <span className="text-xs font-medium text-muted-foreground">from</span>
                  <span className="font-display text-4xl font-extrabold text-[hsl(var(--primary))]">${p.amount}</span>
                </p>
                <p className="text-[11px] text-muted-foreground">Indicative — final fee shared on confirmation</p>
                <ul className="mt-4 space-y-2 text-sm text-muted-foreground">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2"><Check className="mt-0.5 h-4 w-4 flex-shrink-0 text-[hsl(var(--primary))]" /> {f}</li>
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
            <h3 className="font-display text-xl font-bold">{selected ? `Request: ${selectedPkg?.name}` : "Send a general enquiry"}</h3>
            {selected && <p className="mt-1 text-sm text-muted-foreground">Choose an available slot below. Your booking will be <strong>pending confirmation</strong> until Sudarshan's team confirms it.</p>}
            <div className="mt-6 grid gap-4 sm:grid-cols-2">
              <input value={form.name} onChange={set("name")} data-testid="consult-name" placeholder="Full name *" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <input value={form.email} onChange={set("email")} data-testid="consult-email" type="email" placeholder="Email *" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <input value={form.phone} onChange={set("phone")} data-testid="consult-phone" placeholder="Phone" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <input value={form.company} onChange={set("company")} data-testid="consult-company" placeholder="Company" className="rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            </div>
            <select value={form.area} onChange={set("area")} data-testid="consult-area" className="mt-4 w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]">
              {AREAS.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>

            {selected && (
              <div className="mt-5 rounded-xl border border-border bg-background p-4" data-testid="availability-picker">
                <p className="flex items-center gap-2 text-sm font-semibold"><CalendarClock className="h-4 w-4 text-[hsl(var(--primary))]" /> Choose a slot <span className="ml-auto text-xs font-normal text-muted-foreground">{avail.days_label} · {avail.hours}</span></p>
                {avail.days.length === 0 ? (
                  <p className="mt-3 text-sm text-muted-foreground" data-testid="no-slots">No slots are open this week. Send a general enquiry and we'll arrange a time.</p>
                ) : (
                  <>
                    <div className="mt-3 flex flex-wrap gap-2">
                      {avail.days.map((d) => (
                        <button type="button" key={d.date} onClick={() => { setSelDate(d.date); setSelTime(""); }} data-testid={`book-date-${d.date}`}
                          className={`rounded-xl border px-3 py-2 text-xs font-medium ${selDate === d.date ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border-border hover:bg-secondary"}`}>
                          {d.label}
                        </button>
                      ))}
                    </div>
                    {dayObj && (
                      <div className="mt-4">
                        <p className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground"><Clock className="h-3.5 w-3.5" /> Times (IST, {selectedPkg?.duration})</p>
                        <div className="mt-2 grid grid-cols-4 gap-2 sm:grid-cols-6">
                          {dayObj.slots.map((t) => (
                            <button type="button" key={t} onClick={() => setSelTime(t)} data-testid={`book-time-${t}`}
                              className={`rounded-lg border px-2 py-1.5 text-xs ${selTime === t ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border-border hover:bg-secondary"}`}>
                              {t}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
                {avail.full_days?.length > 0 && (
                  <div className="mt-4 border-t border-border pt-4" data-testid="waitlist-box">
                    <p className="text-xs font-semibold">Fully booked days — join the waitlist</p>
                    <p className="text-[11px] text-muted-foreground">We'll email you (using the name &amp; email above) if a slot opens up.</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {avail.full_days.map((d) => (
                        <button type="button" key={d.date} onClick={() => setWlDate(d.date)} data-testid={`waitlist-date-${d.date}`}
                          className={`rounded-xl border px-3 py-2 text-xs font-medium ${wlDate === d.date ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]" : "border-border hover:bg-secondary"}`}>
                          {d.label}
                        </button>
                      ))}
                    </div>
                    {wlDate && (
                      <button type="button" onClick={joinWaitlist} disabled={busy} data-testid="join-waitlist-btn" className="mt-3 rounded-full border border-[hsl(var(--accent))] px-4 py-2 text-xs font-semibold text-[hsl(var(--accent))] hover:bg-[hsl(var(--accent))]/10 disabled:opacity-60">Notify me if a slot opens</button>
                    )}
                  </div>
                )}
              </div>
            )}

            <textarea value={form.message} onChange={set("message")} data-testid="consult-message" placeholder={selected ? "Anything to share before the session (optional)" : "Tell me about your business and what you'd like to achieve *"} rows={4} className="mt-4 w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            <div className="mt-4"><Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} /></div>
            <button type="submit" disabled={busy} data-testid="consult-submit" className="mt-5 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[hsl(var(--accent))] px-6 py-3.5 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
              {busy ? "Please wait…" : selected ? <>Request this session <ArrowUpRight className="h-4 w-4" /></> : "Send Enquiry"}
            </button>
          </form>
        </div>
      </div>
    </section>
  );
}
