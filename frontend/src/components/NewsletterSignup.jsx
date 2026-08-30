import { useState } from "react";
import { toast } from "sonner";
import { Mail, ArrowRight } from "lucide-react";
import api from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";
import Captcha from "@/components/Captcha";

export default function NewsletterSignup() {
  const [email, setEmail] = useState("");
  const [captcha, setCaptcha] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!email) { toast.error("Please enter your email."); return; }
    if (!captcha) { toast.error("Please complete the captcha."); return; }
    setBusy(true);
    try {
      const { data } = await api.post("/newsletter", { email, captcha_token: captcha });
      toast.success(data.message);
      setEmail("");
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Subscription failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="border-t border-border py-24 lg:py-28" data-testid="newsletter">
      <div className="mx-auto max-w-4xl px-6 text-center">
        <div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-[hsl(var(--accent))]/15">
          <Mail className="h-6 w-6 text-[hsl(var(--accent))]" />
        </div>
        <h2 className="mt-6 font-display text-3xl font-bold tracking-tight sm:text-4xl">Get the insights, before the market does.</h2>
        <p className="mx-auto mt-4 max-w-xl text-muted-foreground">
          Join Sudarshan's list for a regular, no-fluff digest on the energy transition, economics, climate finance and business strategy.
        </p>
        <form onSubmit={submit} className="mx-auto mt-8 flex max-w-md flex-col gap-3 sm:flex-row" data-testid="newsletter-form">
          <input
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            type="email"
            placeholder="you@company.com"
            data-testid="newsletter-email"
            className="flex-1 rounded-full border border-border bg-card px-5 py-3.5 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
          />
          <button type="submit" disabled={busy} data-testid="newsletter-submit" className="inline-flex items-center justify-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3.5 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
            {busy ? "Subscribing…" : <>Subscribe <ArrowRight className="h-4 w-4" /></>}
          </button>
        </form>
        <div className="mt-5 flex justify-center"><Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} /></div>
        <p className="mt-4 text-xs text-muted-foreground">No spam. Unsubscribe anytime.</p>
      </div>
    </section>
  );
}
