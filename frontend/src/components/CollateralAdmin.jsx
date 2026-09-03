import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import {
  FileText, Upload, Wand2, Globe, Eye, Pencil, Trash2, Plus, X, Search,
  Radio, RadioTower, FileDown, Video, Music, Loader2, MapPin, RefreshCw,
  Lock, Unlock, Trophy, Download,
} from "lucide-react";
import api, { API } from "@/lib/api";

const BACKEND = API.replace(/\/api$/, "");
const fullUrl = (u) => (!u ? "" : u.startsWith("http") ? u : `${BACKEND}${u}`);

const KIND_ICON = { pdf: FileText, ebook: FileText, doc: FileText, video: Video, audio: Music };
const CAT_ORDER = ["Strategy Tool", "Digital Product", "Lead Magnet", "Video", "Audio", "Custom"];

function Field({ label, children }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-semibold text-muted-foreground">{label}</span>
      {children}
    </label>
  );
}
const inputCls =
  "w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]";

function Modal({ title, onClose, children, testid }) {
  useEffect(() => {
    const onKey = (e) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4" data-testid={testid}>
      <div className="w-full max-w-lg rounded-2xl border border-border bg-card p-6 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-display text-lg font-bold">{title}</h3>
          <button onClick={onClose} data-testid="modal-close" className="rounded-full p-1 hover:bg-secondary"><X className="h-5 w-5" /></button>
        </div>
        {children}
      </div>
    </div>
  );
}

export default function CollateralAdmin() {
  const [items, setItems] = useState([]);
  const [counts, setCounts] = useState({});
  const [leaderboard, setLeaderboard] = useState([]);
  const [totalDownloads, setTotalDownloads] = useState(0);
  const [refresh, setRefresh] = useState({ running: false, total: 0, done: 0 });
  const [loading, setLoading] = useState(true);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState("");
  const [editing, setEditing] = useState(null);
  const [aiFor, setAiFor] = useState(null);
  const [aiInstr, setAiInstr] = useState("");
  const [publishFor, setPublishFor] = useState(null);
  const [notify, setNotify] = useState(false);
  const [creating, setCreating] = useState(false);
  const uploadRefs = useRef({});
  const pollRef = useRef(null);
  const refreshPollRef = useRef(null);

  const load = () => {
    setLoading(true);
    api.get("/admin/collateral")
      .then((r) => {
        setItems(r.data.items); setCounts(r.data.counts);
        setLeaderboard(r.data.leaderboard || []); setTotalDownloads(r.data.total_downloads || 0);
        if (r.data.refresh) setRefresh(r.data.refresh);
      })
      .catch(() => toast.error("Couldn't load collateral — please re-login."))
      .finally(() => setLoading(false));
  };
  useEffect(() => { load(); return () => { clearInterval(pollRef.current); clearInterval(refreshPollRef.current); }; }, []);

  // Poll bulk-refresh progress while running.
  useEffect(() => {
    clearInterval(refreshPollRef.current);
    if (refresh.running) {
      refreshPollRef.current = setInterval(() => {
        api.get("/admin/collateral/ai-refresh-status").then((r) => {
          setRefresh(r.data);
          if (!r.data.running) { clearInterval(refreshPollRef.current); toast.success("Toolkit refreshed — fresh AI PDFs are live."); load(); }
        }).catch(() => {});
      }, 5000);
    }
    return () => clearInterval(refreshPollRef.current);
  }, [refresh.running]);

  const toggleGate = async (item) => {
    setBusy(item.id);
    try {
      await api.post(`/admin/collateral/${item.id}/gate`, { gated: !item.gated });
      toast.success(!item.gated ? "Email now required before download." : "Download is now open (no email).");
      load();
    } catch { toast.error("Couldn't update gate"); } finally { setBusy(""); }
  };

  const bulkRefresh = async () => {
    if (!window.confirm("Regenerate AND publish fresh AI PDFs for all 14 strategy tools? This uses your AI credits and takes a few minutes.")) return;
    try {
      await api.post("/admin/collateral/ai-refresh-all");
      setRefresh({ running: true, total: 14, done: 0 });
      toast.message("Refreshing the whole toolkit with AI…");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Couldn't start refresh");
    }
  };

  const [scheduled, setScheduled] = useState(false);
  useEffect(() => {
    api.get("/admin/collateral/ai-refresh-status").then((r) => setScheduled(!!r.data.scheduled)).catch(() => {});
  }, []);
  const toggleSchedule = async () => {
    try {
      const r = await api.post("/admin/collateral/ai-refresh-schedule", { enabled: !scheduled });
      setScheduled(r.data.scheduled);
      toast.success(r.data.scheduled ? "Monthly auto-refresh ON — runs on the 1st of each month." : "Monthly auto-refresh OFF.");
    } catch { toast.error("Couldn't update schedule"); }
  };

  // Poll while any AI generation is running.
  useEffect(() => {
    const anyRunning = items.some((i) => i.gen_status === "running");
    clearInterval(pollRef.current);
    if (anyRunning) {
      pollRef.current = setInterval(() => {
        api.get("/admin/collateral").then((r) => {
          setItems(r.data.items); setCounts(r.data.counts);
          const stillRunning = r.data.items.some((i) => i.gen_status === "running");
          if (!stillRunning) {
            clearInterval(pollRef.current);
            const done = r.data.items.find((i) => i.gen_status === "done");
            if (done) toast.success("AI document generated — review & publish it.");
          }
        }).catch(() => {});
      }, 4000);
    }
    return () => clearInterval(pollRef.current);
  }, [items]);

  const grouped = useMemo(() => {
    const f = q.trim().toLowerCase();
    const list = f
      ? items.filter((i) => `${i.title} ${i.description} ${i.category}`.toLowerCase().includes(f))
      : items;
    const g = {};
    list.forEach((i) => { (g[i.category] = g[i.category] || []).push(i); });
    return CAT_ORDER.filter((c) => g[c]).map((c) => [c, g[c]]);
  }, [items, q]);

  const uploadFile = async (item, file) => {
    if (!file) return;
    setBusy(item.id);
    const fd = new FormData();
    fd.append("file", file);
    try {
      await api.post(`/admin/collateral/${item.id}/upload`, fd, { headers: { "Content-Type": "multipart/form-data" } });
      toast.success("File uploaded — publish it to push live.");
      load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Upload failed");
    } finally { setBusy(""); }
  };

  const doPublish = async () => {
    const item = publishFor;
    setBusy(item.id);
    try {
      await api.post(`/admin/collateral/${item.id}/publish`, { notify });
      toast.success(notify ? "Published live & subscribers notified." : "Published live.");
      setPublishFor(null); setNotify(false); load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Publish failed");
    } finally { setBusy(""); }
  };

  const unpublish = async (item) => {
    setBusy(item.id);
    try { await api.post(`/admin/collateral/${item.id}/unpublish`); toast.success("Taken offline — website now serves the default."); load(); }
    catch { toast.error("Couldn't unpublish"); } finally { setBusy(""); }
  };

  const runAi = async () => {
    const item = aiFor;
    setBusy(item.id);
    try {
      await api.post(`/admin/collateral/${item.id}/ai-generate`, { instructions: aiInstr });
      toast.message("Generating with AI… this takes ~30–60s.");
      setAiFor(null); setAiInstr(""); load();
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Couldn't start generation");
    } finally { setBusy(""); }
  };

  const del = async (item) => {
    if (!window.confirm(`Delete "${item.title}"? This removes the custom collateral.`)) return;
    setBusy(item.id);
    try { await api.delete(`/admin/collateral/${item.id}`); toast.success("Deleted"); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Couldn't delete"); } finally { setBusy(""); }
  };

  if (loading) return <div className="mt-8 flex items-center gap-2 text-sm text-muted-foreground" data-testid="collateral-loading"><Loader2 className="h-4 w-4 animate-spin" /> Loading collateral…</div>;

  return (
    <div className="mt-8 space-y-8" data-testid="admin-collateral">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="font-display text-2xl font-bold">Collateral & Downloads</h2>
          <p className="mt-1 max-w-2xl text-sm text-muted-foreground">
            Every downloadable on the site in one place — see where each appears, download the current file,
            upload a new one, generate with AI, then push it live (optionally notifying subscribers).
          </p>
        </div>
        <button onClick={() => setCreating(true)} data-testid="collateral-add-btn"
          className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
          <Plus className="h-4 w-4" /> Add collateral
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="rounded-2xl border border-border bg-card p-5 lg:col-span-1" data-testid="collateral-refresh-panel">
          <p className="flex items-center gap-2 font-display text-sm font-bold"><Wand2 className="h-4 w-4 text-[hsl(var(--primary))]" /> Bulk AI refresh</p>
          <p className="mt-1 text-xs text-muted-foreground">Regenerate & publish fresh AI PDFs for all 14 strategy tools in one click.</p>
          {refresh.running ? (
            <div className="mt-3" data-testid="collateral-refresh-progress">
              <div className="flex items-center justify-between text-xs font-medium"><span>Refreshing…</span><span>{refresh.done}/{refresh.total}</span></div>
              <div className="mt-1.5 h-2 w-full overflow-hidden rounded-full bg-secondary">
                <div className="h-full bg-[hsl(var(--primary))] transition-all" style={{ width: `${refresh.total ? (refresh.done / refresh.total) * 100 : 0}%` }} />
              </div>
            </div>
          ) : (
            <button onClick={bulkRefresh} data-testid="collateral-bulk-refresh"
              className="mt-3 inline-flex items-center gap-2 rounded-full border border-border px-4 py-2 text-xs font-semibold hover:bg-secondary">
              <RefreshCw className="h-3.5 w-3.5" /> Regenerate all toolkit PDFs
            </button>
          )}
          <label className="mt-3 flex items-center gap-2 text-xs cursor-pointer" data-testid="collateral-schedule-toggle">
            <input type="checkbox" checked={scheduled} onChange={toggleSchedule} className="h-4 w-4 accent-[hsl(var(--primary))]" />
            <span>Auto-refresh monthly (1st of each month)</span>
          </label>
        </div>
        <div className="rounded-2xl border border-border bg-card p-5 lg:col-span-2" data-testid="collateral-leaderboard">
          <div className="flex items-center justify-between">
            <p className="flex items-center gap-2 font-display text-sm font-bold"><Trophy className="h-4 w-4 text-[hsl(var(--accent))]" /> Top downloaded</p>
            <span className="text-xs text-muted-foreground">{totalDownloads.toLocaleString()} total downloads</span>
          </div>
          {leaderboard.length === 0 ? (
            <p className="mt-3 text-xs text-muted-foreground">No downloads yet — once visitors grab your resources, the winners show up here.</p>
          ) : (
            <ol className="mt-3 space-y-1.5">
              {leaderboard.map((l, i) => (
                <li key={l.id} className="flex items-center justify-between text-sm" data-testid={`leaderboard-row-${l.id}`}>
                  <span className="flex items-center gap-2 truncate"><span className="grid h-5 w-5 shrink-0 place-items-center rounded-full bg-secondary text-[11px] font-bold">{i + 1}</span><span className="truncate">{l.title}</span></span>
                  <span className="shrink-0 text-xs font-semibold">{l.downloads.toLocaleString()} <span className="font-normal text-muted-foreground">({l.downloads_week} this wk)</span></span>
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[220px]">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <input value={q} onChange={(e) => setQ(e.target.value)} data-testid="collateral-search"
            placeholder="Search collateral…" className={`${inputCls} pl-9`} />
        </div>
        {Object.entries(counts).map(([c, n]) => (
          <span key={c} className="rounded-full border border-border bg-secondary px-3 py-1 text-xs font-medium">{c}: {n}</span>
        ))}
      </div>

      {grouped.map(([cat, list]) => (
        <section key={cat} data-testid={`collateral-group-${cat.toLowerCase().replace(/\s+/g, "-")}`}>
          <h3 className="mb-3 font-display text-sm font-bold uppercase tracking-wide text-muted-foreground">{cat}</h3>
          <div className="grid gap-4 md:grid-cols-2">
            {list.map((item) => {
              const Icon = KIND_ICON[item.kind] || FileText;
              const canAi = ["pdf", "ebook", "doc"].includes(item.kind);
              const running = item.gen_status === "running";
              return (
                <div key={item.id} data-testid={`collateral-card-${item.id}`}
                  className="flex flex-col rounded-2xl border border-border bg-card p-5">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3">
                      <span className="mt-0.5 rounded-lg bg-secondary p-2"><Icon className="h-4 w-4 text-[hsl(var(--primary))]" /></span>
                      <div>
                        <p className="font-display text-base font-bold leading-tight">{item.title}</p>
                        <p className="mt-0.5 text-xs text-muted-foreground">{item.description}</p>
                      </div>
                    </div>
                    {item.live ? (
                      <span data-testid={`collateral-status-${item.id}`} className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--accent))] px-2.5 py-1 text-[10px] font-bold uppercase text-[hsl(var(--accent-foreground))]"><Radio className="h-3 w-3" /> Live</span>
                    ) : (
                      <span data-testid={`collateral-status-${item.id}`} className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[10px] font-bold uppercase text-muted-foreground">Offline</span>
                    )}
                  </div>

                  <div className="mt-3 flex flex-wrap gap-1.5 text-[11px]">
                    <span className="rounded bg-secondary px-2 py-0.5 font-medium capitalize">{item.kind}</span>
                    {typeof item.price === "number" && <span className="rounded bg-secondary px-2 py-0.5 font-medium">₹{item.price}</span>}
                    <span className="rounded bg-secondary px-2 py-0.5 font-medium">v{item.version}</span>
                    <span className="inline-flex items-center gap-1 rounded bg-secondary px-2 py-0.5 font-medium"><Download className="h-3 w-3" /> {item.downloads} ({item.downloads_week} wk)</span>
                    {item.gatable && (item.gated
                      ? <span className="inline-flex items-center gap-1 rounded bg-[hsl(var(--accent))]/20 px-2 py-0.5 font-medium text-[hsl(var(--accent-foreground))]"><Lock className="h-3 w-3" /> Email-gated</span>
                      : <span className="inline-flex items-center gap-1 rounded bg-secondary px-2 py-0.5 font-medium"><Unlock className="h-3 w-3" /> Open</span>)}
                    {item.has_file && <span className="rounded bg-secondary px-2 py-0.5 font-medium">{item.serving_managed_file ? "Serving uploaded file" : "File ready"}</span>}
                    {running && <span className="inline-flex items-center gap-1 rounded bg-[hsl(var(--primary))]/15 px-2 py-0.5 font-medium text-[hsl(var(--primary))]"><Loader2 className="h-3 w-3 animate-spin" /> Generating…</span>}
                    {item.gen_status === "error" && <span className="rounded bg-red-500/15 px-2 py-0.5 font-medium text-red-500">Generation failed</span>}
                  </div>

                  <div className="mt-3">
                    <p className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-wide text-muted-foreground"><MapPin className="h-3 w-3" /> Where it's used</p>
                    <ul className="mt-1 space-y-0.5">
                      {(item.locations || []).length === 0 && <li className="text-xs text-muted-foreground">Not linked to a page yet</li>}
                      {(item.locations || []).map((loc, i) => (
                        <li key={i} className="text-xs">
                          <a href={fullUrl(loc.page)} target="_blank" rel="noreferrer" className="text-[hsl(var(--primary))] hover:underline">{loc.label || loc.page}</a>
                          {loc.cta && <span className="text-muted-foreground"> · “{loc.cta}”</span>}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-border pt-4">
                    {item.live_url && (
                      <a href={fullUrl(item.live_url)} target="_blank" rel="noreferrer" data-testid={`collateral-view-${item.id}`}
                        className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary">
                        {item.kind === "video" || item.kind === "audio" ? <Eye className="h-3.5 w-3.5" /> : <FileDown className="h-3.5 w-3.5" />}
                        {item.serving_managed_file ? "Download live file" : "View current"}
                      </a>
                    )}
                    <button onClick={() => setEditing({ ...item })} data-testid={`collateral-edit-${item.id}`}
                      className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary"><Pencil className="h-3.5 w-3.5" /> Edit</button>
                    {item.gatable && (
                      <button onClick={() => toggleGate(item)} disabled={busy === item.id} data-testid={`collateral-gate-${item.id}`}
                        className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary disabled:opacity-50">
                        {item.gated ? <><Unlock className="h-3.5 w-3.5" /> Remove gate</> : <><Lock className="h-3.5 w-3.5" /> Require email</>}
                      </button>
                    )}
                    <input type="file" hidden ref={(el) => (uploadRefs.current[item.id] = el)}
                      onChange={(e) => { uploadFile(item, e.target.files?.[0]); e.target.value = ""; }} />
                    <button onClick={() => uploadRefs.current[item.id]?.click()} disabled={busy === item.id} data-testid={`collateral-upload-${item.id}`}
                      className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary disabled:opacity-50"><Upload className="h-3.5 w-3.5" /> Upload</button>
                    {canAi && (
                      <button onClick={() => { setAiFor(item); setAiInstr(""); }} disabled={busy === item.id || running} data-testid={`collateral-ai-${item.id}`}
                        className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary disabled:opacity-50"><Wand2 className="h-3.5 w-3.5" /> AI generate</button>
                    )}
                    {item.live ? (
                      <button onClick={() => unpublish(item)} disabled={busy === item.id} data-testid={`collateral-unpublish-${item.id}`}
                        className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary disabled:opacity-50"><Globe className="h-3.5 w-3.5" /> Take offline</button>
                    ) : (
                      <button onClick={() => { setPublishFor(item); setNotify(false); }} disabled={busy === item.id || (!item.has_file && !item.external_url)} data-testid={`collateral-publish-${item.id}`}
                        title={!item.has_file && !item.external_url ? "Upload a file or set an external URL first" : ""}
                        className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-3 py-1.5 text-xs font-semibold text-[hsl(var(--primary-foreground))] hover:-translate-y-0.5 disabled:opacity-50"><RadioTower className="h-3.5 w-3.5" /> Push live</button>
                    )}
                    {item.origin === "custom" && (
                      <button onClick={() => del(item)} disabled={busy === item.id} data-testid={`collateral-delete-${item.id}`}
                        className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium text-red-500 hover:bg-red-500/10 disabled:opacity-50"><Trash2 className="h-3.5 w-3.5" /></button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      ))}

      {editing && (
        <Modal title="Edit collateral" testid="collateral-edit-modal" onClose={() => setEditing(null)}>
          <div className="space-y-3">
            <Field label="Title"><input className={inputCls} data-testid="edit-title" value={editing.title} onChange={(e) => setEditing({ ...editing, title: e.target.value })} /></Field>
            <Field label="Description"><textarea rows={2} className={inputCls} data-testid="edit-desc" value={editing.description} onChange={(e) => setEditing({ ...editing, description: e.target.value })} /></Field>
            <Field label="CTA label"><input className={inputCls} data-testid="edit-cta" value={editing.cta_label} onChange={(e) => setEditing({ ...editing, cta_label: e.target.value })} /></Field>
            {typeof editing.price === "number" && (
              <Field label="Price (₹)"><input type="number" className={inputCls} data-testid="edit-price" value={editing.price} onChange={(e) => setEditing({ ...editing, price: Number(e.target.value) })} /></Field>
            )}
            {(editing.kind === "video" || editing.kind === "audio" || editing.external_url) && (
              <Field label="External URL (video/audio/link)"><input className={inputCls} data-testid="edit-external" value={editing.external_url || ""} onChange={(e) => setEditing({ ...editing, external_url: e.target.value })} /></Field>
            )}
            <div className="flex justify-end gap-2 pt-2">
              <button onClick={() => setEditing(null)} className="rounded-full border border-border px-4 py-2 text-sm">Cancel</button>
              <button data-testid="edit-save" onClick={async () => {
                try {
                  await api.patch(`/admin/collateral/${editing.id}`, {
                    title: editing.title, description: editing.description, cta_label: editing.cta_label,
                    price: typeof editing.price === "number" ? editing.price : undefined,
                    external_url: editing.external_url,
                  });
                  toast.success("Saved"); setEditing(null); load();
                } catch { toast.error("Couldn't save"); }
              }} className="rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-sm font-semibold text-[hsl(var(--primary-foreground))]">Save</button>
            </div>
          </div>
        </Modal>
      )}

      {aiFor && (
        <Modal title={`AI generate: ${aiFor.title}`} testid="collateral-ai-modal" onClose={() => setAiFor(null)}>
          <p className="mb-3 text-sm text-muted-foreground">Claude will write a premium, consultant-grade document and produce a branded PDF. Add any specific angle, audience or structure below (optional).</p>
          <textarea rows={4} value={aiInstr} onChange={(e) => setAiInstr(e.target.value)} data-testid="ai-instructions"
            placeholder="e.g. Focus on Indian mid-market manufacturers; include a 90-day action checklist." className={inputCls} />
          <div className="mt-4 flex justify-end gap-2">
            <button onClick={() => setAiFor(null)} className="rounded-full border border-border px-4 py-2 text-sm">Cancel</button>
            <button onClick={runAi} disabled={busy === aiFor.id} data-testid="ai-run"
              className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-50"><Wand2 className="h-4 w-4" /> Generate</button>
          </div>
        </Modal>
      )}

      {publishFor && (
        <Modal title="Push live" testid="collateral-publish-modal" onClose={() => setPublishFor(null)}>
          <p className="text-sm text-muted-foreground">This makes “{publishFor.title}” live on the website immediately — visitors will get {publishFor.has_file ? "the uploaded/generated file" : "the linked resource"}.</p>
          <label className="mt-4 flex items-start gap-2 text-sm">
            <input type="checkbox" checked={notify} onChange={(e) => setNotify(e.target.checked)} data-testid="publish-notify" className="mt-0.5" />
            <span>Notify newsletter subscribers that an updated version is available.</span>
          </label>
          <div className="mt-4 flex justify-end gap-2">
            <button onClick={() => setPublishFor(null)} className="rounded-full border border-border px-4 py-2 text-sm">Cancel</button>
            <button onClick={doPublish} disabled={busy === publishFor.id} data-testid="publish-confirm"
              className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-50"><RadioTower className="h-4 w-4" /> Publish live</button>
          </div>
        </Modal>
      )}

      {creating && <CreateModal onClose={() => setCreating(false)} onCreated={() => { setCreating(false); load(); }} />}
    </div>
  );
}

function CreateModal({ onClose, onCreated }) {
  const [f, setF] = useState({ title: "", category: "Custom", kind: "doc", description: "", cta_label: "Download", price: "", external_url: "", page: "" });
  const [saving, setSaving] = useState(false);
  const set = (k, v) => setF((p) => ({ ...p, [k]: v }));
  const submit = async () => {
    if (!f.title.trim()) { toast.error("Title is required"); return; }
    setSaving(true);
    try {
      await api.post("/admin/collateral", {
        title: f.title, category: f.category, kind: f.kind, description: f.description,
        cta_label: f.cta_label, external_url: f.external_url, page: f.page,
        price: f.price === "" ? undefined : Number(f.price),
      });
      toast.success("Collateral added — upload a file or generate with AI, then push live.");
      onCreated();
    } catch (e) { toast.error(e?.response?.data?.detail || "Couldn't create"); } finally { setSaving(false); }
  };
  return (
    <Modal title="Add collateral" testid="collateral-create-modal" onClose={onClose}>
      <div className="space-y-3">
        <Field label="Title"><input className={inputCls} data-testid="create-title" value={f.title} onChange={(e) => set("title", e.target.value)} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Category">
            <select className={inputCls} data-testid="create-category" value={f.category} onChange={(e) => set("category", e.target.value)}>
              {CAT_ORDER.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </Field>
          <Field label="Type">
            <select className={inputCls} data-testid="create-kind" value={f.kind} onChange={(e) => set("kind", e.target.value)}>
              {["pdf", "ebook", "doc", "video", "audio"].map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </Field>
        </div>
        <Field label="Description"><textarea rows={2} className={inputCls} data-testid="create-desc" value={f.description} onChange={(e) => set("description", e.target.value)} /></Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="CTA label"><input className={inputCls} data-testid="create-cta" value={f.cta_label} onChange={(e) => set("cta_label", e.target.value)} /></Field>
          <Field label="Price (₹, optional)"><input type="number" className={inputCls} data-testid="create-price" value={f.price} onChange={(e) => set("price", e.target.value)} /></Field>
        </div>
        <Field label="Website page it appears on (optional)"><input className={inputCls} data-testid="create-page" placeholder="/products" value={f.page} onChange={(e) => set("page", e.target.value)} /></Field>
        <Field label="External URL (for video/audio/link, optional)"><input className={inputCls} data-testid="create-external" placeholder="https://…" value={f.external_url} onChange={(e) => set("external_url", e.target.value)} /></Field>
        <div className="flex justify-end gap-2 pt-2">
          <button onClick={onClose} className="rounded-full border border-border px-4 py-2 text-sm">Cancel</button>
          <button onClick={submit} disabled={saving} data-testid="create-save" className="rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-50">Add</button>
        </div>
      </div>
    </Modal>
  );
}
