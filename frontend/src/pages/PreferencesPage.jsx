import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { Check, BellRing } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";

export default function PreferencesPage() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [data, setData] = useState(null);
  const [sectors, setSectors] = useState([]);
  const [agencies, setAgencies] = useState([]);
  const [themes, setThemes] = useState([]);
  const [status, setStatus] = useState("loading"); // loading | ready | error | saved

  useEffect(() => { window.scrollTo(0, 0); }, []);
  useEffect(() => {
    if (!token) { setStatus("error"); return; }
    api.get(`/newsletter/preferences?token=${encodeURIComponent(token)}`)
      .then((r) => { setData(r.data); setSectors(r.data.selected_sectors || []); setAgencies(r.data.selected_agencies || []); setThemes(r.data.selected_themes || []); setStatus("ready"); })
      .catch(() => setStatus("error"));
  }, [token]);

  const toggle = (arr, setArr, slug) => setArr(arr.includes(slug) ? arr.filter((s) => s !== slug) : [...arr, slug]);

  const save = async () => {
    try {
      await api.post("/newsletter/preferences", { token, sectors, agencies, themes });
      setStatus("saved");
    } catch { setStatus("error"); }
  };

  const groupedAgencies = (data?.all_agencies || []).reduce((acc, a) => {
    (acc[a.group] = acc[a.group] || []).push(a); return acc;
  }, {});

  const Pill = ({ active, onClick, children, testid }) => (
    <button type="button" onClick={onClick} data-testid={testid}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3.5 py-2 text-xs font-semibold transition-colors ${active ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))]/10 text-[hsl(var(--primary))]" : "border-border text-muted-foreground hover:text-foreground"}`}>
      {active && <Check className="h-3.5 w-3.5" />} {children}
    </button>
  );

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Your weekly topics — Sudarshan Karweer" description="Choose the sectors and capital agencies for your Monday brief." />
      <Navbar />
      <section className="mx-auto max-w-3xl px-6 pt-28 pb-20 md:pt-32">
        <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">
          <BellRing className="h-3.5 w-3.5" /> Weekly Sector Brief
        </span>
        <h1 className="mt-5 font-display text-3xl font-bold md:text-4xl">Choose your topics</h1>
        <p className="mt-3 text-muted-foreground">Pick the sectors and capital agencies you care about — every Monday you'll get a brief with the week's biggest news across your picks.</p>

        {status === "error" && <p className="mt-8 rounded-xl border border-red-500/40 bg-red-500/5 p-4 text-sm text-red-400" data-testid="prefs-error">This link is invalid or expired. Please use the "Manage your topics" link from a recent email.</p>}

        {(status === "ready" || status === "saved") && data && (
          <div className="mt-8 space-y-8" data-testid="prefs-form">
            <p className="text-xs text-muted-foreground">Signed in as <span className="font-semibold text-foreground">{data.email}</span></p>
            {(data.all_themes || []).length > 0 && (
              <div>
                <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-[hsl(var(--primary))]">Insight themes</h2>
                <p className="mt-1 text-xs text-muted-foreground">Your weekly SK Insights email will lead with these themes.</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {data.all_themes.map((t) => (
                    <Pill key={t} active={themes.includes(t)} onClick={() => toggle(themes, setThemes, t)} testid={`pref-theme-${t}`}>{t}</Pill>
                  ))}
                </div>
              </div>
            )}
            <div>
              <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-[hsl(var(--primary))]">Sectors</h2>
              <div className="mt-3 flex flex-wrap gap-2">
                {data.all_sectors.map((s) => (
                  <Pill key={s.slug} active={sectors.includes(s.slug)} onClick={() => toggle(sectors, setSectors, s.slug)} testid={`pref-sector-${s.slug}`}>{s.name}</Pill>
                ))}
              </div>
            </div>
            {Object.entries(groupedAgencies).map(([group, items]) => (
              <div key={group}>
                <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-[hsl(var(--primary))]">{group}</h2>
                <div className="mt-3 flex flex-wrap gap-2">
                  {items.map((a) => (
                    <Pill key={a.slug} active={agencies.includes(a.slug)} onClick={() => toggle(agencies, setAgencies, a.slug)} testid={`pref-agency-${a.slug}`}>{a.name}</Pill>
                  ))}
                </div>
              </div>
            ))}
            <div className="flex items-center gap-4 pt-2">
              <button type="button" onClick={save} data-testid="prefs-save"
                className="rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                Save my topics
              </button>
              {status === "saved" && <span className="inline-flex items-center gap-1.5 text-sm font-semibold text-[hsl(var(--primary))]" data-testid="prefs-saved"><Check className="h-4 w-4" /> Saved — see you Monday</span>}
            </div>
          </div>
        )}
      </section>
      <Footer />
    </div>
  );
}
