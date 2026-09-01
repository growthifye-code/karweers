import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Download, X, FileText, ArrowUpRight, Wrench, BookOpen } from "lucide-react";
import { toast } from "sonner";
import api, { API } from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";
import Captcha from "@/components/Captcha";

function ToolDownloadModal({ tool, onClose }) {
  const [form, setForm] = useState({ name: "", email: "" });
  const [captcha, setCaptcha] = useState("");
  const [busy, setBusy] = useState(false);
  if (!tool) return null;
  const submit = async (e) => {
    e.preventDefault();
    if (!form.email) { toast.error("Please enter your email."); return; }
    if (!captcha) { toast.error("Please complete the captcha."); return; }
    setBusy(true);
    try {
      await api.post("/nurture/subscribe", { email: form.email, name: form.name, source: `strategy-tool-${tool.slug}`, captcha_token: captcha });
      toast.success("Enjoy the toolkit — your download is starting.");
      window.open(`${API}/strategy-tools/${tool.slug}.pdf`, "_blank");
      onClose();
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Something went wrong.");
    } finally { setBusy(false); }
  };
  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-black/70 p-4 backdrop-blur-sm" data-testid="tool-download-modal" onClick={onClose}>
      <div className="w-full max-w-md rounded-3xl border border-border bg-card p-7 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Free toolkit</p>
            <h3 className="mt-1 font-display text-xl font-bold leading-tight">{tool.name}</h3>
          </div>
          <button onClick={onClose} data-testid="tool-modal-close" className="grid h-9 w-9 place-items-center rounded-full border border-border hover:bg-secondary"><X className="h-4 w-4" /></button>
        </div>
        <p className="mt-3 text-sm text-muted-foreground">Get the branded worksheet + operational guidelines as a PDF. Pop in your email and it's yours.</p>
        <form onSubmit={submit} className="mt-5 space-y-3">
          <input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="First name" data-testid="tool-name" className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
          <input value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} type="email" placeholder="you@company.com" data-testid="tool-email" className="w-full rounded-xl border border-border bg-background px-4 py-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
          <div className="flex justify-center"><Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} /></div>
          <button type="submit" disabled={busy} data-testid="tool-download-submit" className="inline-flex w-full items-center justify-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3.5 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
            <Download className="h-4 w-4" /> {busy ? "Preparing…" : "Get the PDF"}
          </button>
        </form>
      </div>
    </div>
  );
}

export default function StrategyToolkit({ showInsights = true }) {
  const [tools, setTools] = useState([]);
  const [insights, setInsights] = useState([]);
  const [active, setActive] = useState(null);
  useEffect(() => {
    api.get("/strategy-tools").then((r) => setTools(r.data)).catch(() => {});
    if (showInsights) api.get("/strategy-insights").then((r) => setInsights(r.data)).catch(() => {});
  }, [showInsights]);

  return (
    <>
      <section className="border-t border-border bg-secondary/30 py-16 lg:py-20" data-testid="strategy-toolkit">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <div className="flex items-center gap-2"><Wrench className="h-5 w-5 text-[hsl(var(--primary))]" /><p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">The strategy toolkit</p></div>
          <h2 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">The frameworks top consultants charge for — free.</h2>
          <p className="mt-4 max-w-2xl text-muted-foreground">The same structured tools used at McKinsey, BCG and Bain — each as a branded worksheet with step-by-step operational guidelines. Take them and put them to work.</p>
          <div className="mt-10 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {tools.map((t) => (
              <div key={t.slug} data-testid={`tool-card-${t.slug}`} className="group flex flex-col rounded-2xl border border-border bg-card p-6 transition-all hover:-translate-y-1 hover:border-[hsl(var(--primary))]">
                <span className="text-[11px] font-bold uppercase tracking-wide text-[hsl(var(--primary))]">{t.category}</span>
                <h3 className="mt-2 font-display text-lg font-bold leading-snug">{t.name}</h3>
                <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground line-clamp-3">{t.tagline}</p>
                <button onClick={() => setActive(t)} data-testid={`tool-download-${t.slug}`} className="mt-5 inline-flex items-center gap-1.5 self-start rounded-full border border-border px-4 py-2 text-sm font-semibold transition-colors group-hover:bg-[hsl(var(--primary))] group-hover:text-[hsl(var(--primary-foreground))]">
                  <FileText className="h-4 w-4" /> Download worksheet
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {showInsights && insights.length > 0 && (
        <section className="py-16 lg:py-20" data-testid="strategy-insights">
          <div className="mx-auto max-w-7xl px-6 lg:px-10">
            <div className="flex items-center gap-2"><BookOpen className="h-5 w-5 text-[hsl(var(--accent))]" /><p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Strategy notes</p></div>
            <h2 className="mt-3 font-display text-3xl font-bold tracking-tight sm:text-4xl">Thinking on par with the best in the business.</h2>
            <div className="mt-10 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {insights.map((a) => (
                <Link key={a.slug} to={`/strategy-insights/${a.slug}`} data-testid={`insight-card-${a.slug}`} className="group flex flex-col rounded-2xl border border-border bg-card p-6 transition-transform hover:-translate-y-1">
                  <span className="text-[11px] font-bold uppercase tracking-wide text-[hsl(var(--accent))]">{a.category} · {a.read_time}</span>
                  <h3 className="mt-2 font-display text-lg font-bold leading-snug group-hover:text-[hsl(var(--primary))]">{a.title}</h3>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground line-clamp-3">{a.dek}</p>
                  <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-[hsl(var(--primary))]">Read <ArrowUpRight className="h-4 w-4" /></span>
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}
      <ToolDownloadModal tool={active} onClose={() => setActive(null)} />
    </>
  );
}
