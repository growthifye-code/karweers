import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Star, RefreshCw, Pencil, History, Mail, Eye, Share2, X, Search, TrendingUp } from "lucide-react";
import api from "@/lib/api";

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="rounded-2xl border border-border bg-card p-4">
      <div className="flex items-center gap-2 text-muted-foreground"><Icon className="h-4 w-4" /><span className="text-xs">{label}</span></div>
      <p className="mt-1 font-display text-2xl font-bold">{value}</p>
    </div>
  );
}

function EditModal({ blog, onClose, onSaved }) {
  const [form, setForm] = useState({ title: blog.title, dek: blog.dek || "", category: blog.category, sort: blog.sort, read_time: blog.read_time || "", hero_image: blog.hero_image || "" });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));
  const save = async () => {
    if (form.sort === "" || isNaN(Number(form.sort))) { toast.error("Order must be a number"); return; }
    setSaving(true);
    try {
      await api.patch(`/admin/service-insights/${blog.slug}`, { ...form, sort: Number(form.sort) });
      toast.success("Insight updated"); onSaved();
    } catch { toast.error("Couldn't save"); } finally { setSaving(false); }
  };
  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/50" onClick={onClose} data-testid="insight-edit-modal">
      <div className="h-full w-full max-w-lg overflow-y-auto bg-background p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between"><h3 className="font-display text-xl font-bold">Edit insight</h3><button onClick={onClose}><X className="h-5 w-5" /></button></div>
        <div className="mt-6 space-y-4">
          {[["title", "Title"], ["dek", "Standfirst (dek)"], ["read_time", "Read time"], ["hero_image", "Hero image URL"]].map(([k, l]) => (
            <label key={k} className="block"><span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{l}</span>
              {k === "dek"
                ? <textarea value={form[k]} onChange={(e) => set(k, e.target.value)} rows={3} data-testid={`edit-${k}`} className="mt-1.5 w-full rounded-xl border border-border bg-card px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]" />
                : <input value={form[k]} onChange={(e) => set(k, e.target.value)} data-testid={`edit-${k}`} className="mt-1.5 w-full rounded-xl border border-border bg-card px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]" />}
            </label>
          ))}
          <div className="grid grid-cols-2 gap-3">
            <label className="block"><span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Category</span>
              <input value={form.category} onChange={(e) => set("category", e.target.value)} data-testid="edit-category" className="mt-1.5 w-full rounded-xl border border-border bg-card px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]" /></label>
            <label className="block"><span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Sort (order)</span>
              <input type="number" value={form.sort} onChange={(e) => set("sort", e.target.value)} data-testid="edit-sort" className="mt-1.5 w-full rounded-xl border border-border bg-card px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]" /></label>
          </div>
          <button onClick={save} disabled={saving} data-testid="edit-save" className="w-full rounded-full bg-[hsl(var(--primary))] px-5 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-60">{saving ? "Saving…" : "Save changes"}</button>
        </div>
      </div>
    </div>
  );
}

function EditionsModal({ blog, onClose }) {
  const [editions, setEditions] = useState([]);
  useEffect(() => { api.get(`/admin/service-insights/${blog.slug}/editions`).then((r) => setEditions(r.data)).catch(() => {}); }, [blog.slug]);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4" onClick={onClose} data-testid="insight-editions-modal">
      <div className="max-h-[80vh] w-full max-w-lg overflow-y-auto rounded-2xl bg-background p-6 shadow-2xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-start justify-between"><h3 className="font-display text-lg font-bold">Archived editions — {blog.title}</h3><button onClick={onClose}><X className="h-5 w-5" /></button></div>
        {editions.length === 0 ? <p className="mt-6 text-sm text-muted-foreground">No earlier editions archived yet. Editions accumulate each time this insight is refreshed.</p> : (
          <ul className="mt-5 space-y-3">
            {editions.map((e) => (
              <li key={e.archive_id} className="rounded-xl border border-border bg-card p-4">
                <div className="flex items-center justify-between"><span className="text-xs font-semibold text-muted-foreground">v{e.version} · {new Date(e.archived_at).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}</span>
                  <a href={`/archive/edition/${e.archive_id}`} target="_blank" rel="noopener noreferrer" className="text-xs font-semibold text-[hsl(var(--primary))]">Read →</a></div>
                <p className="mt-1.5 line-clamp-2 text-sm text-muted-foreground">{e.dek}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default function InsightsAdmin() {
  const [blogs, setBlogs] = useState([]);
  const [analytics, setAnalytics] = useState(null);
  const [queue, setQueue] = useState([]);
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState(null);
  const [editions, setEditions] = useState(null);
  const [busy, setBusy] = useState("");
  const [sending, setSending] = useState(false);

  const load = () => {
    api.get("/admin/service-insights").then((r) => setBlogs(r.data)).catch(() => toast.error("Couldn't load insights — please re-login."));
    api.get("/admin/insights/analytics").then((r) => setAnalytics(r.data)).catch(() => {});
    api.get("/admin/featured-queue").then((r) => setQueue(r.data.queue || [])).catch(() => {});
  };
  useEffect(() => { load(); }, []);

  const feature = async (slug) => {
    try { await api.post(`/admin/service-insights/${slug}/feature`); toast.success("Pinned as featured"); load(); }
    catch { toast.error("Couldn't feature"); }
  };
  const refresh = async (slug) => {
    setBusy(slug);
    try { const { data } = await api.post(`/admin/service-insights/${slug}/refresh`); toast.success(data.message || "Refreshed"); load(); }
    catch { toast.error("Refresh failed — try again"); } finally { setBusy(""); }
  };
  const sendNewsletter = async () => {
    setSending(true);
    try {
      const { data } = await api.post("/admin/insights-newsletter/run");
      if (data.sent) toast.success(`Newsletter sent to ${data.subscribers} subscriber(s)`);
      else toast.message("Email isn't configured yet — nothing sent.");
    } catch { toast.error("Couldn't send newsletter"); } finally { setSending(false); }
  };

  const term = q.trim().toLowerCase();
  const shown = useMemo(() => blogs.filter((b) => !term || [b.title, b.service_title, b.category].some((v) => String(v || "").toLowerCase().includes(term))), [blogs, term]);
  const maxThemeReads = Math.max(1, ...((analytics?.by_theme || []).map((t) => t.reads)));

  return (
    <div data-testid="insights-admin">
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl font-bold">SK Insights</h2>
          <p className="text-sm text-muted-foreground">{blogs.length} insights · edit, reorder, feature, refresh and track performance.</p>
        </div>
        <button onClick={sendNewsletter} disabled={sending} data-testid="send-newsletter" className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-60"><Mail className="h-4 w-4" />{sending ? "Sending…" : "Send newsletter now"}</button>
      </div>

      {analytics && (
        <div className="mb-8 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <div className="grid grid-cols-2 gap-3">
              <StatCard icon={Eye} label="Total reads" value={analytics.total_reads} />
              <StatCard icon={Share2} label="Total shares" value={analytics.total_shares} />
            </div>
            <div className="mt-3 rounded-2xl border border-border bg-card p-4">
              <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground"><TrendingUp className="h-4 w-4" /> Reads by theme</p>
              <div className="mt-3 space-y-2" data-testid="analytics-by-theme">
                {(analytics.by_theme || []).length === 0 && <p className="text-sm text-muted-foreground">No reads yet.</p>}
                {(analytics.by_theme || []).map((t) => (
                  <div key={t.theme}>
                    <div className="flex justify-between text-xs"><span>{t.theme}</span><span className="text-muted-foreground">{t.reads}</span></div>
                    <div className="mt-1 h-2 overflow-hidden rounded-full bg-secondary"><div className="h-full rounded-full bg-[hsl(var(--primary))]" style={{ width: `${(t.reads / maxThemeReads) * 100}%` }} /></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
          <div className="rounded-2xl border border-border bg-card p-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Most read</p>
            <ol className="mt-3 space-y-2" data-testid="analytics-top-read">
              {(analytics.top_read || []).length === 0 && <p className="text-sm text-muted-foreground">No reads yet.</p>}
              {(analytics.top_read || []).map((r, i) => (
                <li key={r.slug} className="flex items-center justify-between gap-3 text-sm"><span className="line-clamp-1"><span className="text-muted-foreground">{i + 1}.</span> {r.title}</span><span className="shrink-0 font-semibold text-[hsl(var(--primary))]">{r.reads}</span></li>
              ))}
            </ol>
          </div>
          <div className="rounded-2xl border border-border bg-card p-5">
            <p className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Most shared</p>
            <ol className="mt-3 space-y-2" data-testid="analytics-top-shared">
              {(analytics.top_shared || []).length === 0 && <p className="text-sm text-muted-foreground">No shares yet.</p>}
              {(analytics.top_shared || []).map((r, i) => (
                <li key={r.slug} className="flex items-center justify-between gap-3 text-sm"><span className="line-clamp-1"><span className="text-muted-foreground">{i + 1}.</span> {r.title}</span><span className="shrink-0 font-semibold text-[hsl(var(--primary))]">{r.shares}</span></li>
              ))}
            </ol>
          </div>
        </div>
      )}

      <div className="relative mb-4 max-w-md">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search insights…" data-testid="insights-admin-search" className="w-full rounded-full border border-border bg-card pl-10 pr-4 py-2.5 text-sm outline-none focus:border-[hsl(var(--primary))]" />
      </div>

      <div className="mb-6 rounded-2xl border border-border bg-card p-5" data-testid="featured-queue-panel">
        <div className="flex items-center gap-2"><Star className="h-4 w-4 fill-[hsl(var(--primary))] text-[hsl(var(--primary))]" /><h3 className="font-display text-base font-bold">Featured rotation</h3></div>
        <p className="mt-1 text-xs text-muted-foreground">Star insights below to queue them. The homepage & hub auto-rotate through the queue weekly (Mondays). {queue.length === 0 ? "Queue is empty — the freshest insight shows by default." : `${queue.length} queued.`}</p>
        {queue.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-2">
            {queue.map((item) => (
              <span key={item.slug} className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium ${item.current ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))]/10 text-[hsl(var(--primary))]" : "border-border"}`} data-testid={`queue-${item.slug}`}>
                {item.current && <span className="text-[10px] font-bold uppercase">Live</span>}{item.title.length > 40 ? item.title.slice(0, 40) + "…" : item.title}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="overflow-hidden rounded-2xl border border-border">
        <table className="w-full text-left text-sm">
          <thead className="bg-secondary/50 text-xs uppercase tracking-wider text-muted-foreground">
            <tr><th className="px-4 py-3">Insight</th><th className="px-3 py-3">Category</th><th className="px-3 py-3 text-center">Order</th><th className="px-3 py-3 text-center">Reads</th><th className="px-3 py-3 text-center">Shares</th><th className="px-3 py-3 text-center">Editions</th><th className="px-3 py-3 text-right">Actions</th></tr>
          </thead>
          <tbody data-testid="insights-admin-table">
            {shown.map((b) => (
              <tr key={b.slug} className="border-t border-border hover:bg-secondary/30" data-testid={`insight-row-${b.slug}`}>
                <td className="px-4 py-3"><div className="flex items-center gap-2">{b.featured && <Star className="h-4 w-4 flex-shrink-0 fill-[hsl(var(--primary))] text-[hsl(var(--primary))]" />}<div><p className="line-clamp-1 font-medium">{b.title}</p><p className="text-xs text-muted-foreground">{b.service_title} · v{b.version}</p></div></div></td>
                <td className="px-3 py-3 text-xs">{b.category}</td>
                <td className="px-3 py-3 text-center">{b.sort}</td>
                <td className="px-3 py-3 text-center font-semibold">{b.reads}</td>
                <td className="px-3 py-3 text-center font-semibold">{b.shares}</td>
                <td className="px-3 py-3 text-center">{b.editions}</td>
                <td className="px-3 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <button onClick={() => feature(b.slug)} title="Feature" data-testid={`feature-${b.slug}`} className={`grid h-8 w-8 place-items-center rounded-full border border-border hover:border-[hsl(var(--primary))] ${b.featured ? "text-[hsl(var(--primary))]" : "text-muted-foreground"}`}><Star className={`h-4 w-4 ${b.featured ? "fill-[hsl(var(--primary))]" : ""}`} /></button>
                    <button onClick={() => setEditing(b)} title="Edit" data-testid={`edit-${b.slug}`} className="grid h-8 w-8 place-items-center rounded-full border border-border text-muted-foreground hover:border-[hsl(var(--primary))] hover:text-[hsl(var(--primary))]"><Pencil className="h-4 w-4" /></button>
                    <button onClick={() => refresh(b.slug)} disabled={busy === b.slug} title="Refresh" data-testid={`refresh-${b.slug}`} className="grid h-8 w-8 place-items-center rounded-full border border-border text-muted-foreground hover:border-[hsl(var(--primary))] hover:text-[hsl(var(--primary))] disabled:opacity-50"><RefreshCw className={`h-4 w-4 ${busy === b.slug ? "animate-spin" : ""}`} /></button>
                    <button onClick={() => setEditions(b)} title="Editions" data-testid={`editions-${b.slug}`} className="grid h-8 w-8 place-items-center rounded-full border border-border text-muted-foreground hover:border-[hsl(var(--primary))] hover:text-[hsl(var(--primary))]"><History className="h-4 w-4" /></button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && <EditModal blog={editing} onClose={() => setEditing(null)} onSaved={() => { setEditing(null); load(); }} />}
      {editions && <EditionsModal blog={editions} onClose={() => setEditions(null)} />}
    </div>
  );
}
