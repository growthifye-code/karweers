import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { useAuth, formatApiErrorDetail } from "@/context/AuthContext";
import { Logo } from "@/components/Navbar";
import ThemeToggle from "@/components/ThemeToggle";
import { Users, FileText, Inbox, Sparkles, Trash2, Wand2, Mail, LifeBuoy, UserCircle, ChevronDown, Tag, AlertTriangle, Star } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from "recharts";
import api from "@/lib/api";

const CATS = [
  { key: "news", label: "News" },
  { key: "analysis", label: "Company Analysis" },
  { key: "blog", label: "Blog" },
  { key: "rd", label: "R&D / Technology" },
  { key: "casestudy", label: "Case Study" },
];

const SECTORS = ["Renewable Energy", "Energy Storage", "Green Hydrogen", "Green Financing", "Economy", "Sustainability", "Business Strategy", "Asset Monetisation"];

const DEFAULT_IMG = "https://images.unsplash.com/photo-1497436072909-60f360e1d4b1?crop=entropy&cs=srgb&fm=jpg&q=85&w=1200";

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const [tab, setTab] = useState("overview");
  const [stats, setStats] = useState({ articles: 0, consultations: 0, new_leads: 0, clients: 0 });
  const [leads, setLeads] = useState([]);
  const [articles, setArticles] = useState([]);
  const [subscribers, setSubscribers] = useState([]);
  const [clients, setClients] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [activeClient, setActiveClient] = useState(null);
  const [clientNotes, setClientNotes] = useState("");
  const [clientTags, setClientTags] = useState("");
  const [crmTag, setCrmTag] = useState("all");
  const [segments, setSegments] = useState([]);
  const [leadSource, setLeadSource] = useState("all");
  const [analytics, setAnalytics] = useState(null);
  const [chartPeriod, setChartPeriod] = useState("8w");
  const [ticketReplies, setTicketReplies] = useState({});

  const [form, setForm] = useState({ title: "", category: "news", sector: SECTORS[0], summary: "", content: "", tags: "", image: DEFAULT_IMG, featured: false });
  const [aiTopic, setAiTopic] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = () => {
    api.get("/admin/stats").then((r) => setStats(r.data)).catch(() => {});
    api.get("/consultations").then((r) => setLeads(r.data)).catch(() => {});
    api.get("/articles").then((r) => setArticles(r.data)).catch(() => {});
    api.get("/newsletter").then((r) => setSubscribers(r.data)).catch(() => {});
    api.get("/admin/clients").then((r) => setClients(r.data)).catch(() => {});
    api.get("/admin/tickets").then((r) => setTickets(r.data)).catch(() => {});
    api.get("/admin/lead-analytics").then((r) => setAnalytics(r.data)).catch(() => {});
  };
  useEffect(load, []);

  useEffect(() => {
    api.get("/admin/lead-analytics", { params: { period: chartPeriod } }).then((r) => setAnalytics(r.data)).catch(() => {});
  }, [chartPeriod]);

  const openClient = async (id) => {
    try {
      const { data } = await api.get(`/admin/clients/${id}`);
      setActiveClient(data);
      setClientNotes(data.user.notes || "");
      setClientTags((data.user.tags || []).join(", "));
    } catch { toast.error("Could not load client."); }
  };
  const saveClientMeta = async () => {
    if (!activeClient) return;
    try {
      const tags = clientTags.split(",").map((t) => t.trim()).filter(Boolean);
      await api.patch(`/admin/clients/${activeClient.user.id}`, { notes: clientNotes, tags });
      setActiveClient((c) => ({ ...c, user: { ...c.user, notes: clientNotes, tags } }));
      setClients((cs) => cs.map((c) => c.id === activeClient.user.id ? { ...c, notes: clientNotes, tags } : c));
      toast.success("Client profile saved.");
    } catch { toast.error("Save failed."); }
  };
  const ticketStatus = async (id, status) => {
    try { await api.patch(`/admin/tickets/${id}`, { status }); setTickets((t) => t.map((x) => x.id === id ? { ...x, status } : x)); }
    catch { toast.error("Update failed"); }
  };
  const ticketPriority = async (id, priority) => {
    try { await api.patch(`/admin/tickets/${id}`, { priority }); setTickets((t) => t.map((x) => x.id === id ? { ...x, priority } : x)); }
    catch { toast.error("Update failed"); }
  };
  const adminReply = async (id) => {
    const msg = ticketReplies[id];
    if (!msg?.trim()) return;
    try { await api.post(`/tickets/${id}/reply`, { message: msg }); setTicketReplies((r) => ({ ...r, [id]: "" })); load(); toast.success("Reply sent"); }
    catch { toast.error("Reply failed"); }
  };

  const SLA_HOURS = { high: 4, medium: 24, low: 72 };
  const ticketAgeHrs = (t) => (Date.now() - new Date(t.updated_at || t.created_at).getTime()) / 3.6e6;
  const isBreached = (t) => ["open", "in-progress"].includes(t.status) && ticketAgeHrs(t) > (SLA_HOURS[t.priority] ?? 24);
  const fmtAge = (h) => (h >= 24 ? `${Math.floor(h / 24)}d` : `${Math.max(1, Math.floor(h))}h`);
  const allTags = [...new Set(clients.flatMap((c) => c.tags || []))].sort();
  const filteredClients = crmTag === "all" ? clients : clients.filter((c) => (c.tags || []).includes(crmTag));
  const sortedTickets = [...tickets].sort((a, b) => (isBreached(b) ? 1 : 0) - (isBreached(a) ? 1 : 0));
  const breachedCount = tickets.filter(isBreached).length;

  useEffect(() => {
    try { setSegments(JSON.parse(localStorage.getItem("sk_crm_segments") || "[]")); } catch { setSegments([]); }
  }, []);
  const persistSegments = (next) => { setSegments(next); try { localStorage.setItem("sk_crm_segments", JSON.stringify(next)); } catch {} };
  const saveSegment = () => {
    if (crmTag === "all" || segments.includes(crmTag)) return;
    persistSegments([...segments, crmTag]);
    toast.success(`Saved segment: ${crmTag}`);
  };
  const removeSegment = (s) => persistSegments(segments.filter((x) => x !== s));

  const SOURCE_META = {
    "booking-form": { label: "Booking Form", cls: "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]" },
    "ask-sk-chatbot": { label: "Ask SK Bot", cls: "bg-[hsl(var(--accent))]/15 text-[hsl(var(--accent))]" },
    "consultation-checkout": { label: "Checkout", cls: "bg-blue-500/15 text-blue-400" },
    "whatsapp": { label: "WhatsApp", cls: "bg-[#25D366]/15 text-[#25D366]" },
    "": { label: "Other", cls: "bg-secondary text-muted-foreground" },
  };
  const srcMeta = (s) => SOURCE_META[s] || SOURCE_META[""];
  const leadSources = [...new Set(leads.map((l) => l.source || ""))];
  const filteredLeads = leadSource === "all" ? leads : leads.filter((l) => (l.source || "") === leadSource);

  const generate = async () => {
    if (!aiTopic.trim()) { toast.error("Enter a topic for the AI to write about."); return; }
    setAiBusy(true);
    try {
      const { data } = await api.post("/ai/generate", { topic: aiTopic, category: form.category });
      setForm((f) => ({
        ...f,
        title: data.title || f.title,
        summary: data.summary || f.summary,
        content: data.content || f.content,
        tags: Array.isArray(data.tags) ? data.tags.join(", ") : f.tags,
      }));
      toast.success("AI draft generated — review and publish.");
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "AI generation failed");
    } finally {
      setAiBusy(false);
    }
  };

  const publish = async (e) => {
    e.preventDefault();
    if (!form.title || !form.summary || !form.content) { toast.error("Title, summary and content are required."); return; }
    setSaving(true);
    try {
      await api.post("/articles", {
        ...form,
        tags: form.tags.split(",").map((t) => t.trim()).filter(Boolean),
      });
      toast.success("Article published!");
      setForm({ title: "", category: "news", sector: SECTORS[0], summary: "", content: "", tags: "", image: DEFAULT_IMG, featured: false });
      load();
      setTab("articles");
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Publish failed");
    } finally {
      setSaving(false);
    }
  };

  const remove = async (slug) => {
    if (!window.confirm("Delete this article?")) return;
    try {
      await api.delete(`/articles/${slug}`);
      toast.success("Deleted");
      load();
    } catch { toast.error("Delete failed"); }
  };

  const setLeadStatus = async (id, status) => {
    try {
      await api.patch(`/consultations/${id}`, null, { params: { status } });
      setLeads((l) => l.map((x) => (x.id === id ? { ...x, status } : x)));
    } catch { toast.error("Update failed"); }
  };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const SOURCE_LABELS = { "booking-form": "Booking Form", "ask-sk-chatbot": "Ask SK Bot", "consultation-checkout": "Checkout", "whatsapp": "WhatsApp", "other": "Other" };
  const SOURCE_COLORS = { "booking-form": "#C6F135", "ask-sk-chatbot": "#7dd3fc", "consultation-checkout": "#60a5fa", "whatsapp": "#25D366", "other": "#9ca3af" };

  const statCards = [
    { icon: FileText, label: "Articles", value: stats.articles },
    { icon: Inbox, label: "Consultation Leads", value: stats.consultations },
    { icon: Sparkles, label: "New Leads", value: stats.new_leads },
    { icon: Users, label: "Registered Clients", value: stats.clients },
  ];

  const subCard = { icon: Mail, label: "Newsletter Subscribers", value: subscribers.length };
  statCards.push(subCard);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-4">
            <Logo />
            <span className="rounded-full bg-[hsl(var(--accent))] px-3 py-1 text-xs font-semibold text-[hsl(var(--accent-foreground))]">Admin</span>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">View site</Link>
            <button onClick={logout} data-testid="admin-logout" className="rounded-full border border-border px-4 py-2 text-sm font-medium hover:bg-secondary">Logout</button>
          </div>
        </div>
      </header>

      <div className="mx-auto max-w-7xl px-6 py-10">
        <h1 className="font-display text-3xl font-bold">Admin Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">Signed in as {user?.email}</p>

        <div className="mt-8 flex flex-wrap gap-2 border-b border-border pb-4">
          {["overview", "crm", "leads", "tickets", "articles", "create", "subscribers"].map((t) => (
            <button key={t} onClick={() => setTab(t)} data-testid={`admin-tab-${t}`}
              className={`rounded-full px-4 py-2 text-sm font-medium capitalize transition-colors ${tab === t ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border border-border text-muted-foreground hover:bg-secondary"}`}>
              {t === "create" ? "Create + AI" : t === "crm" ? "CRM" : t === "tickets" ? "Service Desk" : t}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <div className="mt-8 space-y-8" data-testid="admin-overview">
            <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {statCards.map((s) => (
                <div key={s.label} className="rounded-2xl border border-border bg-card p-6">
                  <s.icon className="h-7 w-7 text-[hsl(var(--accent))]" />
                  <p className="mt-4 font-display text-4xl font-black">{s.value}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{s.label}</p>
                </div>
              ))}
            </div>

            {analytics && (
              <div className="rounded-2xl border border-border bg-card p-6" data-testid="lead-source-chart">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-display text-lg font-bold">Lead volume by source</h3>
                    <p className="text-sm text-muted-foreground">Where your enquiries come from</p>
                  </div>
                  <div className="flex gap-1 rounded-full border border-border p-1" data-testid="chart-period-toggle">
                    {[["8w", "8 weeks"], ["3m", "3 months"], ["12m", "12 months"]].map(([v, l]) => (
                      <button key={v} onClick={() => setChartPeriod(v)} data-testid={`period-${v}`}
                        className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${chartPeriod === v ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "text-muted-foreground hover:bg-secondary"}`}>{l}</button>
                    ))}
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-3">
                  {analytics.sources.filter((s) => analytics.totals[s] > 0).map((s) => (
                    <span key={s} className="inline-flex items-center gap-1.5 text-xs text-muted-foreground">
                      <span className="h-2.5 w-2.5 rounded-full" style={{ background: SOURCE_COLORS[s] }} />
                      {SOURCE_LABELS[s]} <span className="font-semibold text-foreground">{analytics.totals[s]}</span>
                    </span>
                  ))}
                </div>
                <div className="mt-6 h-64 w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={analytics.weeks} margin={{ top: 4, right: 8, left: -18, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                      <XAxis dataKey="week" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                      <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, fontSize: 12 }} cursor={{ fill: "hsl(var(--secondary))", opacity: 0.4 }} />
                      {analytics.sources.map((s) => (
                        <Bar key={s} dataKey={s} stackId="a" name={SOURCE_LABELS[s]} fill={SOURCE_COLORS[s]} radius={s === "other" ? [4, 4, 0, 0] : 0} />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                {analytics.conversion && (
                  <div className="mt-6 border-t border-border pt-5" data-testid="conversion-view">
                    <h4 className="font-display text-sm font-bold">Conversion by source</h4>
                    <p className="text-xs text-muted-foreground">Share of each channel's leads that became paid consultations (all-time)</p>
                    <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {analytics.sources.filter((s) => analytics.conversion[s].total > 0).map((s) => {
                        const c = analytics.conversion[s];
                        return (
                          <div key={s} className="rounded-xl border border-border p-4" data-testid={`conversion-${s}`}>
                            <div className="flex items-center justify-between">
                              <span className="inline-flex items-center gap-1.5 text-sm font-medium">
                                <span className="h-2.5 w-2.5 rounded-full" style={{ background: SOURCE_COLORS[s] }} />{SOURCE_LABELS[s]}
                              </span>
                              <span className="font-display text-lg font-black text-[hsl(var(--primary))]">{c.rate}%</span>
                            </div>
                            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-secondary">
                              <div className="h-full rounded-full" style={{ width: `${c.rate}%`, background: SOURCE_COLORS[s] }} />
                            </div>
                            <p className="mt-2 text-xs text-muted-foreground">{c.paid} paid of {c.total} lead{c.total > 1 ? "s" : ""}</p>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {tab === "crm" && (
          <div className="mt-8" data-testid="admin-crm">
            {allTags.length > 0 && (
              <div className="mb-4 flex flex-wrap items-center gap-2" data-testid="crm-tag-filters">
                <span className="mr-1 inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground"><Tag className="h-3.5 w-3.5" /> Filter</span>
                <button onClick={() => setCrmTag("all")} data-testid="crm-tag-all"
                  className={`rounded-full border px-3 py-1.5 text-xs font-medium capitalize transition-colors ${crmTag === "all" ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border-border text-muted-foreground hover:bg-secondary"}`}>All ({clients.length})</button>
                {allTags.map((tg) => (
                  <button key={tg} onClick={() => setCrmTag(tg)} data-testid={`crm-tag-${tg}`}
                    className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${crmTag === tg ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border-border text-muted-foreground hover:bg-secondary"}`}>
                    {tg} ({clients.filter((c) => (c.tags || []).includes(tg)).length})
                  </button>
                ))}
                {crmTag !== "all" && !segments.includes(crmTag) && (
                  <button onClick={saveSegment} data-testid="save-segment"
                    className="inline-flex items-center gap-1 rounded-full border border-[hsl(var(--accent))]/50 px-3 py-1.5 text-xs font-semibold text-[hsl(var(--accent))] hover:bg-[hsl(var(--accent))]/10">
                    <Star className="h-3.5 w-3.5" /> Save segment
                  </button>
                )}
              </div>
            )}
            {segments.length > 0 && (
              <div className="mb-4 flex flex-wrap items-center gap-2" data-testid="saved-segments">
                <span className="mr-1 inline-flex items-center gap-1 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--accent))]"><Star className="h-3.5 w-3.5" /> Saved</span>
                {segments.map((s) => (
                  <span key={s} className={`inline-flex items-center gap-1 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${crmTag === s ? "border-[hsl(var(--accent))] bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]" : "border-border text-muted-foreground"}`}>
                    <button onClick={() => setCrmTag(s)} data-testid={`segment-${s}`}>{s}</button>
                    <button onClick={() => removeSegment(s)} data-testid={`remove-segment-${s}`} className="opacity-60 hover:opacity-100">×</button>
                  </span>
                ))}
              </div>
            )}
            <div className="overflow-x-auto rounded-2xl border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-card text-muted-foreground">
                <tr>
                  <th className="p-4">Client ID</th><th className="p-4">Name</th><th className="p-4">Source</th><th className="p-4">Interests</th><th className="p-4">Activity</th><th className="p-4">Bookings</th><th className="p-4">Joined</th><th className="p-4"></th>
                </tr>
              </thead>
              <tbody>
                {filteredClients.length === 0 && <tr><td colSpan="8" className="p-8 text-center text-muted-foreground">{crmTag === "all" ? "No registered clients yet." : `No clients tagged "${crmTag}".`}</td></tr>}
                {filteredClients.map((c) => (
                  <tr key={c.id} className="border-t border-border align-top">
                    <td className="p-4 font-mono text-xs font-semibold text-[hsl(var(--primary))]">{c.client_code || "—"}</td>
                    <td className="p-4 font-medium">{c.name}<div className="text-xs text-muted-foreground">{c.email}</div>{c.tags?.length > 0 && <div className="mt-1 flex flex-wrap gap-1">{c.tags.map((tg) => <span key={tg} className="rounded-full bg-[hsl(var(--primary))]/15 px-2 py-0.5 text-[10px] font-semibold text-[hsl(var(--primary))]">{tg}</span>)}</div>}</td>
                    <td className="p-4 text-muted-foreground capitalize">{c.auth || "email"}</td>
                    <td className="p-4 text-xs text-muted-foreground">{(c.interests_computed || []).join(", ") || "—"}</td>
                    <td className="p-4 text-muted-foreground">{c.activity_count}</td>
                    <td className="p-4 text-muted-foreground">{c.booking_count}</td>
                    <td className="p-4 text-muted-foreground">{c.created_at ? new Date(c.created_at).toLocaleDateString() : "—"}</td>
                    <td className="p-4"><button onClick={() => openClient(c.id)} data-testid={`view-client-${c.id}`} className="rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary">View</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>
        )}

        {tab === "tickets" && (
          <div className="mt-8 space-y-4" data-testid="admin-tickets">
            {breachedCount > 0 && (
              <div className="flex items-center gap-2 rounded-xl border border-[hsl(var(--destructive))]/40 bg-[hsl(var(--destructive))]/10 px-4 py-3 text-sm font-medium text-[hsl(var(--destructive))]" data-testid="sla-summary">
                <AlertTriangle className="h-4 w-4" /> {breachedCount} ticket{breachedCount > 1 ? "s" : ""} past SLA — respond now (SLA: high 4h · medium 24h · low 72h).
              </div>
            )}
            {tickets.length === 0 && <div className="rounded-2xl border border-dashed border-border p-10 text-center text-muted-foreground">No support tickets yet.</div>}
            {sortedTickets.map((t) => {
              const breached = isBreached(t);
              return (
              <div key={t.id} className={`rounded-2xl border bg-card p-5 ${breached ? "border-[hsl(var(--destructive))]/60" : "border-border"}`} data-testid={`admin-ticket-${t.id}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-semibold">{t.subject}</p>
                      {breached && <span className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--destructive))]/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[hsl(var(--destructive))]" data-testid={`sla-breach-${t.id}`}><AlertTriangle className="h-3 w-3" /> SLA breached</span>}
                      {t.auto_escalated && <span className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--accent))]/15 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[hsl(var(--accent))]" data-testid={`auto-escalated-${t.id}`}>Auto-escalated</span>}
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">{t.ticket_code} · {t.name} ({t.client_code || t.email}) · {t.category} · <span className={breached ? "font-semibold text-[hsl(var(--destructive))]" : ""}>open {fmtAge(ticketAgeHrs(t))}</span></p>
                  </div>
                  <div className="flex gap-2">
                    <select value={t.priority} onChange={(e) => ticketPriority(t.id, e.target.value)} data-testid={`ticket-priority-${t.id}`} className="rounded-lg border border-border bg-background px-2 py-1 text-xs capitalize">
                      {["low", "medium", "high"].map((p) => <option key={p} value={p}>{p}</option>)}
                    </select>
                    <select value={t.status} onChange={(e) => ticketStatus(t.id, e.target.value)} data-testid={`ticket-status-${t.id}`} className="rounded-lg border border-border bg-background px-2 py-1 text-xs capitalize">
                      {["open", "in-progress", "resolved", "closed"].map((s) => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                </div>
                <p className="mt-3 text-sm text-muted-foreground">{t.message}</p>
                {t.replies?.length > 0 && (
                  <div className="mt-4 space-y-2 border-t border-border pt-4">
                    {t.replies.map((r, i) => (
                      <div key={i} className={`rounded-lg p-3 text-sm ${r.role === "admin" ? "bg-[hsl(var(--primary))]/10" : "bg-secondary"}`}>
                        <span className="text-xs font-semibold">{r.role === "admin" ? "Team SK" : t.name}</span>
                        <p className="mt-1 text-muted-foreground">{r.message}</p>
                      </div>
                    ))}
                  </div>
                )}
                <div className="mt-3 flex gap-2">
                  <input value={ticketReplies[t.id] || ""} onChange={(e) => setTicketReplies({ ...ticketReplies, [t.id]: e.target.value })} placeholder="Reply to client…" data-testid={`admin-reply-input-${t.id}`} className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none" />
                  <button onClick={() => adminReply(t.id)} data-testid={`admin-reply-send-${t.id}`} className="rounded-lg bg-[hsl(var(--accent))] px-4 py-2 text-sm font-medium text-[hsl(var(--accent-foreground))]">Reply</button>
                </div>
              </div>
              );
            })}
          </div>
        )}

        {tab === "leads" && (
          <div className="mt-8" data-testid="admin-leads">
            <div className="mb-4 flex flex-wrap items-center gap-2" data-testid="lead-source-filters">
              <span className="mr-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Source</span>
              <button onClick={() => setLeadSource("all")} data-testid="lead-source-all"
                className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${leadSource === "all" ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border-border text-muted-foreground hover:bg-secondary"}`}>All ({leads.length})</button>
              {leadSources.map((s) => (
                <button key={s || "other"} onClick={() => setLeadSource(s)} data-testid={`lead-source-${s || "other"}`}
                  className={`rounded-full border px-3 py-1.5 text-xs font-medium transition-colors ${leadSource === s ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border-border text-muted-foreground hover:bg-secondary"}`}>
                  {srcMeta(s).label} ({leads.filter((l) => (l.source || "") === s).length})
                </button>
              ))}
            </div>
            <div className="overflow-x-auto rounded-2xl border border-border">
            <table className="w-full text-left text-sm">
              <thead className="bg-card text-muted-foreground">
                <tr>
                  <th className="p-4">Name</th><th className="p-4">Contact</th><th className="p-4">Source</th><th className="p-4">Area / Package</th><th className="p-4">Message</th><th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {filteredLeads.length === 0 && <tr><td colSpan="6" className="p-8 text-center text-muted-foreground">No consultation leads yet.</td></tr>}
                {filteredLeads.map((l) => (
                  <tr key={l.id} className="border-t border-border align-top">
                    <td className="p-4 font-medium">{l.name}<div className="text-xs text-muted-foreground">{l.company}</div></td>
                    <td className="p-4 text-muted-foreground">{l.email}<div className="text-xs">{l.phone}</div></td>
                    <td className="p-4"><span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold ${srcMeta(l.source || "").cls}`} data-testid={`lead-source-badge-${l.id}`}>{srcMeta(l.source || "").label}</span></td>
                    <td className="p-4 text-muted-foreground">{l.area}{l.package && <div className="mt-1 text-xs font-semibold text-[hsl(var(--primary))]">{l.package} · ${l.amount}</div>}</td>
                    <td className="p-4 max-w-xs text-muted-foreground">{l.message}</td>
                    <td className="p-4">
                      <select value={l.status} onChange={(e) => setLeadStatus(l.id, e.target.value)} data-testid={`lead-status-${l.id}`} className="rounded-lg border border-border bg-background px-2 py-1 text-xs">
                        <option value="new">New</option>
                        <option value="contacted">Contacted</option>
                        <option value="qualified">Qualified</option>
                        <option value="payment_pending">Payment Pending</option>
                        <option value="paid">Paid</option>
                        <option value="scheduled">Scheduled</option>
                        <option value="won">Won</option>
                        <option value="lost">Lost</option>
                        <option value="closed">Closed</option>
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            </div>
          </div>
        )}

        {tab === "articles" && (
          <div className="mt-8 space-y-3" data-testid="admin-articles">
            {articles.map((a) => (
              <div key={a.slug} className="flex items-center gap-4 rounded-2xl border border-border bg-card p-4">
                <img src={a.image} alt="" className="h-14 w-20 rounded-lg object-cover" />
                <div className="flex-1">
                  <p className="font-medium">{a.title}</p>
                  <p className="text-xs text-muted-foreground">{a.category} · {a.sector}</p>
                </div>
                <button onClick={() => remove(a.slug)} data-testid={`delete-${a.slug}`} className="grid h-9 w-9 place-items-center rounded-full border border-border text-[hsl(var(--destructive))] hover:bg-secondary">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {tab === "create" && (
          <div className="mt-8 grid gap-8 lg:grid-cols-[1fr_1.4fr]" data-testid="admin-create">
            <div className="rounded-2xl border border-border bg-card p-6">
              <div className="flex items-center gap-2">
                <Wand2 className="h-5 w-5 text-[hsl(var(--accent))]" />
                <h3 className="font-display text-lg font-bold">AI Content Engine</h3>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">Describe a topic — Karweer AI (Claude) drafts a full article for you to review and publish.</p>
              <input value={aiTopic} onChange={(e) => setAiTopic(e.target.value)} data-testid="ai-topic" placeholder="e.g. India's green hydrogen export opportunity" className="mt-4 w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <p className="mt-3 text-xs text-muted-foreground">Category: <span className="font-semibold">{CATS.find((c) => c.key === form.category)?.label}</span> (set on the right)</p>
              <button onClick={generate} disabled={aiBusy} data-testid="ai-generate" className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
                {aiBusy ? "Generating…" : <>Generate Draft <Sparkles className="h-4 w-4" /></>}
              </button>
            </div>

            <form onSubmit={publish} className="rounded-2xl border border-border bg-card p-6 space-y-4" data-testid="article-form">
              <h3 className="font-display text-lg font-bold">Article details</h3>
              <input value={form.title} onChange={set("title")} data-testid="art-title" placeholder="Title" className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <div className="grid gap-4 sm:grid-cols-2">
                <select value={form.category} onChange={set("category")} data-testid="art-category" className="rounded-lg border border-border bg-background px-4 py-3 text-sm">
                  {CATS.map((c) => <option key={c.key} value={c.key}>{c.label}</option>)}
                </select>
                <select value={form.sector} onChange={set("sector")} data-testid="art-sector" className="rounded-lg border border-border bg-background px-4 py-3 text-sm">
                  {SECTORS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <textarea value={form.summary} onChange={set("summary")} data-testid="art-summary" placeholder="Summary" rows={2} className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <textarea value={form.content} onChange={set("content")} data-testid="art-content" placeholder="Content (use blank lines between paragraphs)" rows={8} className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <input value={form.tags} onChange={set("tags")} data-testid="art-tags" placeholder="Tags (comma separated)" className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <input value={form.image} onChange={set("image")} data-testid="art-image" placeholder="Image URL" className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <label className="flex items-center gap-2 text-sm text-muted-foreground">
                <input type="checkbox" checked={form.featured} onChange={(e) => setForm({ ...form, featured: e.target.checked })} data-testid="art-featured" /> Featured
              </label>
              <button type="submit" disabled={saving} data-testid="art-publish" className="w-full rounded-full bg-[hsl(var(--accent))] px-6 py-3.5 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
                {saving ? "Publishing…" : "Publish Article"}
              </button>
            </form>
          </div>
        )}
        {tab === "subscribers" && (
          <div className="mt-8 overflow-x-auto rounded-2xl border border-border" data-testid="admin-subscribers">
            <table className="w-full text-left text-sm">
              <thead className="bg-card text-muted-foreground"><tr><th className="p-4">Email</th><th className="p-4">Subscribed</th></tr></thead>
              <tbody>
                {subscribers.length === 0 && <tr><td colSpan="2" className="p-8 text-center text-muted-foreground">No subscribers yet.</td></tr>}
                {subscribers.map((s) => (
                  <tr key={s.id} className="border-t border-border">
                    <td className="p-4 font-medium">{s.email}</td>
                    <td className="p-4 text-muted-foreground">{new Date(s.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {activeClient && (
          <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={() => setActiveClient(null)} data-testid="client-drawer">
            <div className="h-full w-full max-w-lg overflow-y-auto bg-background p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  {activeClient.user.picture ? <img src={activeClient.user.picture} alt="" className="h-12 w-12 rounded-full object-cover" /> : <UserCircle className="h-12 w-12 text-muted-foreground" />}
                  <div>
                    <p className="font-display text-xl font-bold">{activeClient.user.name}</p>
                    <p className="text-xs text-muted-foreground">{activeClient.user.email}</p>
                    <p className="mt-1 font-mono text-xs font-semibold text-[hsl(var(--primary))]">{activeClient.user.client_code}</p>
                  </div>
                </div>
                <button onClick={() => setActiveClient(null)} className="text-2xl leading-none text-muted-foreground">×</button>
              </div>

              {activeClient.interests?.length > 0 && (
                <div className="mt-6">
                  <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Interest profile</p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {activeClient.interests.map((it) => <span key={it.topic} className="rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs text-[hsl(var(--primary))]">{it.topic} · {it.score}</span>)}
                  </div>
                </div>
              )}

              <div className="mt-6 rounded-xl border border-border p-4" data-testid="client-meta">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Private notes &amp; tags</p>
                <input value={clientTags} onChange={(e) => setClientTags(e.target.value)} data-testid="client-tags"
                  placeholder="Tags (comma separated) e.g. VIP, warm, fundraising"
                  className="mt-3 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
                <textarea value={clientNotes} onChange={(e) => setClientNotes(e.target.value)} data-testid="client-notes" rows={4}
                  placeholder="Private notes about this relationship (only visible to admins)…"
                  className="mt-3 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
                <button onClick={saveClientMeta} data-testid="save-client-meta"
                  className="mt-3 rounded-full bg-[hsl(var(--accent))] px-5 py-2 text-sm font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5">Save profile</button>
              </div>

              <div className="mt-6">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Bookings ({activeClient.bookings.length})</p>
                <div className="mt-2 space-y-2">
                  {activeClient.bookings.length === 0 && <p className="text-sm text-muted-foreground">None yet.</p>}
                  {activeClient.bookings.map((b) => <div key={b.id} className="rounded-lg border border-border p-3 text-sm">{b.area || b.package || "Consultation"} <span className="text-xs text-muted-foreground">· {b.status}</span></div>)}
                </div>
              </div>

              <div className="mt-6">
                <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Activity timeline ({activeClient.timeline.length})</p>
                <div className="mt-2 space-y-1.5">
                  {activeClient.timeline.length === 0 && <p className="text-sm text-muted-foreground">No tracked activity yet.</p>}
                  {activeClient.timeline.slice(0, 60).map((ev, i) => (
                    <div key={i} className="flex items-center justify-between gap-3 border-l-2 border-[hsl(var(--primary))]/40 pl-3 text-sm">
                      <span className="text-muted-foreground"><span className="font-medium capitalize text-foreground">{ev.kind}</span> {ev.label || ev.ref}</span>
                      <span className="shrink-0 text-xs text-muted-foreground">{new Date(ev.created_at).toLocaleString()}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
