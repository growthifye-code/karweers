import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { useAuth, formatApiErrorDetail } from "@/context/AuthContext";
import { Logo } from "@/components/Navbar";
import ThemeToggle from "@/components/ThemeToggle";
import { Users, FileText, Inbox, Sparkles, Trash2, Wand2 } from "lucide-react";
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

  const [form, setForm] = useState({ title: "", category: "news", sector: SECTORS[0], summary: "", content: "", tags: "", image: DEFAULT_IMG, featured: false });
  const [aiTopic, setAiTopic] = useState("");
  const [aiBusy, setAiBusy] = useState(false);
  const [saving, setSaving] = useState(false);

  const load = () => {
    api.get("/admin/stats").then((r) => setStats(r.data)).catch(() => {});
    api.get("/consultations").then((r) => setLeads(r.data)).catch(() => {});
    api.get("/articles").then((r) => setArticles(r.data)).catch(() => {});
  };
  useEffect(load, []);

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
          {["overview", "leads", "articles", "create"].map((t) => (
            <button key={t} onClick={() => setTab(t)} data-testid={`admin-tab-${t}`}
              className={`rounded-full px-4 py-2 text-sm font-medium capitalize transition-colors ${tab === t ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border border-border text-muted-foreground hover:bg-secondary"}`}>
              {t === "create" ? "Create + AI" : t}
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

        {tab === "leads" && (
          <div className="mt-8 overflow-x-auto rounded-2xl border border-border" data-testid="admin-leads">
            <table className="w-full text-left text-sm">
              <thead className="bg-card text-muted-foreground">
                <tr>
                  <th className="p-4">Name</th><th className="p-4">Contact</th><th className="p-4">Area</th><th className="p-4">Message</th><th className="p-4">Status</th>
                </tr>
              </thead>
              <tbody>
                {leads.length === 0 && <tr><td colSpan="5" className="p-8 text-center text-muted-foreground">No consultation leads yet.</td></tr>}
                {leads.map((l) => (
                  <tr key={l.id} className="border-t border-border align-top">
                    <td className="p-4 font-medium">{l.name}<div className="text-xs text-muted-foreground">{l.company}</div></td>
                    <td className="p-4 text-muted-foreground">{l.email}<div className="text-xs">{l.phone}</div></td>
                    <td className="p-4 text-muted-foreground">{l.area}</td>
                    <td className="p-4 max-w-xs text-muted-foreground">{l.message}</td>
                    <td className="p-4">
                      <select value={l.status} onChange={(e) => setLeadStatus(l.id, e.target.value)} data-testid={`lead-status-${l.id}`} className="rounded-lg border border-border bg-background px-2 py-1 text-xs">
                        <option value="new">New</option>
                        <option value="contacted">Contacted</option>
                        <option value="scheduled">Scheduled</option>
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
      </div>
    </div>
  );
}
