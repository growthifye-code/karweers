import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { useAuth, formatApiErrorDetail } from "@/context/AuthContext";
import { Logo } from "@/components/Navbar";
import ThemeToggle from "@/components/ThemeToggle";
import { Users, FileText, Inbox, Sparkles, Trash2, Wand2, Mail, LifeBuoy, UserCircle, ChevronDown } from "lucide-react";
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
  };
  useEffect(load, []);

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
          <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-4" data-testid="admin-overview">
            {statCards.map((s) => (
              <div key={s.label} className="rounded-2xl border border-border bg-card p-6">
                <s.icon className="h-7 w-7 text-[hsl(var(--accent))]" />
                <p className="mt-4 font-display text-4xl font-black">{s.value}</p>
                <p className="mt-1 text-sm text-muted-foreground">{s.label}</p>
              </div>
            ))}
          </div>
        )}

        {tab === "crm" && (
          <div className="mt-8 overflow-x-auto rounded-2xl border border-border" data-testid="admin-crm">
            <table className="w-full text-left text-sm">
              <thead className="bg-card text-muted-foreground">
                <tr>
                  <th className="p-4">Client ID</th><th className="p-4">Name</th><th className="p-4">Source</th><th className="p-4">Interests</th><th className="p-4">Activity</th><th className="p-4">Bookings</th><th className="p-4">Joined</th><th className="p-4"></th>
                </tr>
              </thead>
              <tbody>
                {clients.length === 0 && <tr><td colSpan="8" className="p-8 text-center text-muted-foreground">No registered clients yet.</td></tr>}
                {clients.map((c) => (
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
        )}

        {tab === "tickets" && (
          <div className="mt-8 space-y-4" data-testid="admin-tickets">
            {tickets.length === 0 && <div className="rounded-2xl border border-dashed border-border p-10 text-center text-muted-foreground">No support tickets yet.</div>}
            {tickets.map((t) => (
              <div key={t.id} className="rounded-2xl border border-border bg-card p-5" data-testid={`admin-ticket-${t.id}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold">{t.subject}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{t.ticket_code} · {t.name} ({t.client_code || t.email}) · {t.category}</p>
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
            ))}
          </div>
        )}

        {tab === "leads" && (
          <div className="mt-8 overflow-x-auto rounded-2xl border border-border" data-testid="admin-leads">
            <table className="w-full text-left text-sm">
              <thead className="bg-card text-muted-foreground">
                <tr>
                  <th className="p-4">Name</th><th className="p-4">Contact</th><th className="p-4">Area / Package</th><th className="p-4">Message</th><th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {leads.length === 0 && <tr><td colSpan="5" className="p-8 text-center text-muted-foreground">No consultation leads yet.</td></tr>}
                {leads.map((l) => (
                  <tr key={l.id} className="border-t border-border align-top">
                    <td className="p-4 font-medium">{l.name}<div className="text-xs text-muted-foreground">{l.company}</div></td>
                    <td className="p-4 text-muted-foreground">{l.email}<div className="text-xs">{l.phone}</div></td>
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
