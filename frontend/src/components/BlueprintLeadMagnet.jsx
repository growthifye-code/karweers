import { useState } from "react";
import { toast } from "sonner";
import { Download, FileText, ArrowRight } from "lucide-react";
import api, { API } from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";
import Captcha from "@/components/Captcha";

// Free lead-magnet: capture email -> nurture funnel -> download the generic Blueprint Starter PDF.
export default function BlueprintLeadMagnet() {
  const [form, setForm] = useState({ name: "", email: "" });
  const [captcha, setCaptcha] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!form.email) { toast.error("Please enter your email."); return; }
    if (!captcha) { toast.error("Please complete the captcha."); return; }
    setBusy(true);
    try {
      const { data } = await api.post("/nurture/subscribe", { email: form.email, name: form.name, source: "blueprint-lead-magnet", captcha_token: captcha });
      toast.success(data.message);
      setDone(true);
      window.open(`${API}/blueprint/starter.pdf`, "_blank");
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Something went wrong.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <section className="relative overflow-hidden rounded-[2rem] border border-border bg-[hsl(var(--primary))] p-8 text-[hsl(var(--primary-foreground))] lg:p-12" data-testid="lead-magnet">
      <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-black/10 blur-3xl" />
      <div className="relative grid items-center gap-8 lg:grid-cols-2">
        <div>
          <p className="inline-flex items-center gap-2 rounded-full bg-black/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em]"><FileText className="h-3.5 w-3.5" /> Free download</p>
          <h2 className="mt-4 font-display text-3xl font-extrabold leading-tight sm:text-4xl">The Leadership Blueprint — Starter</h2>
          <p className="mt-4 max-w-md text-[hsl(var(--primary-foreground))]/80">
            A crisp, five-part framework to run your leadership like a system: strategy, capital, people and the 90-day loop. Get the PDF free — no fluff, just what works.
          </p>
        </div>
        {done ? (
          <div className="rounded-2xl bg-black/10 p-6" data-testid="lead-magnet-done">
            <Download className="h-8 w-8" />
            <p className="mt-3 font-display text-lg font-bold">Your download is on its way.</p>
            <p className="mt-1 text-sm text-[hsl(var(--primary-foreground))]/80">If it didn't open automatically, use the button below.</p>
            <a href={`${API}/blueprint/starter.pdf`} target="_blank" rel="noreferrer" data-testid="lead-magnet-redownload"
              className="mt-4 inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary-foreground))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary))]">
              Download again <Download className="h-4 w-4" />
            </a>
          </div>
        ) : (
          <form onSubmit={submit} className="space-y-3 rounded-2xl bg-black/10 p-6" data-testid="lead-magnet-form">
            <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="First name" data-testid="lead-magnet-name"
              className="w-full rounded-xl border border-black/10 bg-white/90 px-4 py-3 text-sm text-black outline-none placeholder:text-black/50" />
            <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} type="email" placeholder="you@company.com" data-testid="lead-magnet-email"
              className="w-full rounded-xl border border-black/10 bg-white/90 px-4 py-3 text-sm text-black outline-none placeholder:text-black/50" />
            <div className="flex justify-center"><Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} /></div>
            <button type="submit" disabled={busy} data-testid="lead-magnet-submit"
              className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[hsl(var(--primary-foreground))] px-6 py-3.5 font-semibold text-[hsl(var(--primary))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
              {busy ? "Preparing…" : <>Get the free PDF <ArrowRight className="h-4 w-4" /></>}
            </button>
          </form>
        )}
      </div>
    </section>
  );
}
