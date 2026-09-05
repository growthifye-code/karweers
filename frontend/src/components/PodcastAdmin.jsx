import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { Mic, Sparkles, Loader2, Trash2, Eye, EyeOff, Upload, CheckCircle2, AlertCircle, Pencil, Save, BadgeCheck, X } from "lucide-react";
import api from "@/lib/api";

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS = {
  generating: { cls: "bg-amber-500/15 text-amber-500", icon: Loader2, label: "Writing script", spin: true },
  pending_review: { cls: "bg-sky-500/15 text-sky-500", icon: Pencil, label: "Needs approval" },
  generating_audio: { cls: "bg-amber-500/15 text-amber-500", icon: Loader2, label: "Recording voice", spin: true },
  published: { cls: "bg-emerald-500/15 text-emerald-500", icon: CheckCircle2, label: "Published" },
  draft: { cls: "bg-muted text-muted-foreground", icon: EyeOff, label: "Unpublished" },
  error: { cls: "bg-red-500/15 text-red-500", icon: AlertCircle, label: "Failed" },
};

function AdminEpisode({ ep, onChange }) {
  const s = STATUS[ep.status] || STATUS.draft;
  const Icon = s.icon;
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [approving, setApproving] = useState(false);
  const [form, setForm] = useState({ title: ep.title, description: ep.description || "", script: ep.script || "" });

  useEffect(() => { setForm({ title: ep.title, description: ep.description || "", script: ep.script || "" }); }, [ep.title, ep.description, ep.script]);

  const reviewable = ep.status === "pending_review" || (ep.status === "error" && ep.script);

  const save = async () => {
    setSaving(true);
    try { await api.put(`/admin/podcast/${ep.id}`, form); toast.success("Script saved"); setEditing(false); onChange(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Save failed"); }
    finally { setSaving(false); }
  };
  const approve = async () => {
    if (!window.confirm("Approve this script? It will be narrated in SK's voice and published.")) return;
    setApproving(true);
    try { await api.post(`/admin/podcast/${ep.id}/approve`); toast.success("Approved — recording voice now, then it publishes automatically."); onChange(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Approval failed"); }
    finally { setApproving(false); }
  };
  const act = async (path) => {
    try { await api.post(`/admin/podcast/${ep.id}/${path}`); toast.success("Updated"); onChange(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Action failed"); }
  };
  const del = async () => {
    if (!window.confirm("Delete this episode permanently?")) return;
    try { await api.delete(`/admin/podcast/${ep.id}`); toast.success("Deleted"); onChange(); } catch (e) { toast.error("Delete failed"); }
  };

  return (
    <div className="rounded-2xl border border-border bg-card p-5" data-testid={`podcast-admin-ep-${ep.id}`}>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${s.cls}`}>
              <Icon className={`h-3.5 w-3.5 ${s.spin ? "animate-spin" : ""}`} /> {s.label}
            </span>
            {ep.duration_min && <span className="text-xs text-muted-foreground">~{ep.duration_min} min</span>}
          </div>
          <h4 className="mt-2 font-display text-base font-bold">{ep.title}</h4>
          {ep.description && !editing && <p className="mt-1 text-sm text-muted-foreground">{ep.description}</p>}
          {ep.status === "error" && ep.error && <p className="mt-1 text-xs text-red-500">{ep.error}</p>}
        </div>
        <div className="flex shrink-0 flex-wrap items-center justify-end gap-2">
          {reviewable && !editing && (
            <button onClick={() => setEditing(true)} data-testid={`podcast-edit-${ep.id}`} className="inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 text-xs hover:bg-secondary"><Pencil className="h-3.5 w-3.5" /> Edit script</button>
          )}
          {reviewable && (
            <button onClick={approve} disabled={approving} data-testid={`podcast-approve-${ep.id}`} className="inline-flex items-center gap-1 rounded-full bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-white transition-transform hover:-translate-y-0.5 disabled:opacity-60">
              {approving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <BadgeCheck className="h-3.5 w-3.5" />} Approve &amp; publish
            </button>
          )}
          {ep.status === "published" && <button onClick={() => act("unpublish")} data-testid={`podcast-unpublish-${ep.id}`} className="inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 text-xs hover:bg-secondary"><EyeOff className="h-3.5 w-3.5" /> Unpublish</button>}
          {ep.status === "draft" && ep.has_audio && <button onClick={() => act("publish")} data-testid={`podcast-publish-${ep.id}`} className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-3 py-1.5 text-xs font-semibold text-[hsl(var(--primary-foreground))]"><Eye className="h-3.5 w-3.5" /> Publish</button>}
          <button onClick={del} data-testid={`podcast-delete-${ep.id}`} className="inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 text-xs text-red-500 hover:bg-red-500/10"><Trash2 className="h-3.5 w-3.5" /></button>
        </div>
      </div>

      {editing ? (
        <div className="mt-4 space-y-3 border-t border-border pt-4" data-testid={`podcast-edit-panel-${ep.id}`}>
          <div>
            <label className="text-xs font-semibold text-muted-foreground">Title</label>
            <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} data-testid={`podcast-edit-title-${ep.id}`}
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
          </div>
          <div>
            <label className="text-xs font-semibold text-muted-foreground">Show notes / description</label>
            <textarea value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} rows={2} data-testid={`podcast-edit-desc-${ep.id}`}
              className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
          </div>
          <div>
            <label className="text-xs font-semibold text-muted-foreground">Script (this exact text is narrated)</label>
            <textarea value={form.script} onChange={(e) => setForm({ ...form, script: e.target.value })} rows={14} data-testid={`podcast-edit-script-${ep.id}`}
              className="mt-1 w-full whitespace-pre-line rounded-lg border border-border bg-background px-3 py-2 font-mono text-xs leading-relaxed outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
          </div>
          <div className="flex items-center gap-2">
            <button onClick={save} disabled={saving} data-testid={`podcast-save-${ep.id}`} className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-xs font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-60">
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />} Save changes
            </button>
            <button onClick={() => { setEditing(false); setForm({ title: ep.title, description: ep.description || "", script: ep.script || "" }); }} className="inline-flex items-center gap-1 rounded-full border border-border px-4 py-2 text-xs hover:bg-secondary"><X className="h-3.5 w-3.5" /> Cancel</button>
          </div>
        </div>
      ) : reviewable && ep.script ? (
        <details className="mt-3 rounded-xl border border-border bg-background p-3" data-testid={`podcast-script-preview-${ep.id}`}>
          <summary className="cursor-pointer text-xs font-semibold text-[hsl(var(--primary))]">Read the script before approving</summary>
          <div className="mt-2 max-h-72 overflow-y-auto whitespace-pre-line text-sm leading-relaxed text-muted-foreground">{ep.script}</div>
        </details>
      ) : null}

      {ep.has_audio && !editing && <audio src={`${API}/api/podcast/episodes/${ep.id}/audio${ep.status !== "published" ? `?token=${encodeURIComponent(localStorage.getItem("sk_token") || "")}` : ""}`} controls preload="none" className="mt-3 w-full" />}
    </div>
  );
}

export const PodcastAdmin = () => {
  const [data, setData] = useState(null);
  const [topic, setTopic] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [suggesting, setSuggesting] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const fileRef = useRef(null);
  const pollRef = useRef(null);

  const load = () => api.get("/admin/podcast/episodes").then((r) => setData(r.data)).catch(() => {});
  useEffect(() => { load(); return () => clearTimeout(pollRef.current); }, []);

  const working = (data?.episodes || []).some((e) => e.status === "generating" || e.status === "generating_audio");
  useEffect(() => {
    clearTimeout(pollRef.current);
    if (working) pollRef.current = setTimeout(load, 5000);
    return () => clearTimeout(pollRef.current);
  }, [working, data]);

  const generate = async () => {
    setBusy(true);
    try {
      await api.post("/admin/podcast/generate", { topic });
      setTopic("");
      toast.success("Writing the script — you'll review & approve it before it publishes.");
      setTimeout(load, 1500);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start generation.");
    } finally { setBusy(false); }
  };

  const suggest = async () => {
    setSuggesting(true);
    try {
      const r = await api.post("/admin/podcast/suggest-topics");
      setSuggestions(r.data?.topics || []);
      if (!(r.data?.topics || []).length) toast.info("No topics returned — try again.");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not generate topics.");
    } finally { setSuggesting(false); }
  };

  const toggleSchedule = async () => {
    const next = !data.auto_weekly;
    try { await api.post("/admin/podcast/schedule", { enabled: next }); setData({ ...data, auto_weekly: next }); toast.success(next ? "Weekly auto-draft ON" : "Weekly auto-draft OFF"); }
    catch (e) { toast.error("Could not update schedule"); }
  };
  const uploadIntro = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append("file", file);
    try { await api.post("/admin/podcast/intro", fd, { headers: { "Content-Type": "multipart/form-data" } }); toast.success("Intro clip saved"); load(); }
    catch (e2) { toast.error(e2?.response?.data?.detail || "Upload failed"); }
    finally { setUploading(false); if (fileRef.current) fileRef.current.value = ""; }
  };
  const removeIntro = async () => {
    try { await api.delete("/admin/podcast/intro"); toast.success("Intro clip removed"); load(); } catch (e) { toast.error("Failed"); }
  };

  const episodes = data?.episodes || [];
  const pendingCount = episodes.filter((e) => e.status === "pending_review").length;

  return (
    <div data-testid="podcast-admin">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="flex items-center gap-2 font-display text-2xl font-bold"><Mic className="h-5 w-5 text-[hsl(var(--primary))]" /> The SK Strategy Brief</h2>
          <p className="mt-1 text-sm text-muted-foreground">Scripted in-house, narrated in <strong>Sudarshan's cloned voice</strong> (ElevenLabs). <strong>Every script is reviewed &amp; approved by you</strong> before the voice is recorded and the episode publishes.</p>
        </div>
        <label className="flex cursor-pointer select-none items-center gap-2 rounded-full border border-border px-4 py-2 text-sm" data-testid="podcast-schedule-toggle">
          <input type="checkbox" checked={!!data?.auto_weekly} onChange={toggleSchedule} className="accent-[hsl(var(--primary))]" />
          Auto-draft weekly (Mon)
        </label>
      </div>

      {pendingCount > 0 && (
        <div className="mt-4 flex items-center gap-2 rounded-xl border border-sky-500/30 bg-sky-500/10 px-4 py-2.5 text-sm text-sky-600 dark:text-sky-400" data-testid="podcast-pending-banner">
          <Pencil className="h-4 w-4" /> {pendingCount} script{pendingCount > 1 ? "s" : ""} waiting for your approval below.
        </div>
      )}

      <div className="mt-6 rounded-2xl border border-border bg-card p-6">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <p className="text-sm font-semibold">Generate a new episode script</p>
          <button onClick={suggest} disabled={suggesting} data-testid="podcast-suggest-btn"
            className="inline-flex items-center gap-1.5 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3.5 py-1.5 text-xs font-semibold text-[hsl(var(--primary))] transition-colors hover:bg-[hsl(var(--primary))]/20 disabled:opacity-60">
            {suggesting ? <><Loader2 className="h-3.5 w-3.5 animate-spin" /> Thinking…</> : <><Sparkles className="h-3.5 w-3.5" /> Suggest topics (AI)</>}
          </button>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">AI reads your site content, what's resonating socially, and the economic mood for small, MSME &amp; large orgs — then proposes episodes.</p>

        {suggestions.length > 0 && (
          <div className="mt-3 grid gap-2" data-testid="podcast-suggestions">
            {suggestions.map((sug, i) => (
              <button key={i} onClick={() => { setTopic(sug.topic); setSuggestions([]); }} data-testid={`podcast-suggestion-${i}`}
                className="group rounded-xl border border-border bg-background p-3 text-left transition-colors hover:border-[hsl(var(--primary))]/50 hover:bg-secondary/40">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-semibold text-foreground">{sug.topic}</p>
                  <span className="shrink-0 rounded-full bg-secondary px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-muted-foreground">{sug.segment}</span>
                </div>
                {sug.angle && <p className="mt-1 text-xs text-muted-foreground">{sug.angle}</p>}
                {sug.rationale && <p className="mt-0.5 text-[11px] italic text-muted-foreground/80">Why now: {sug.rationale}</p>}
                <span className="mt-1 inline-block text-[11px] font-medium text-[hsl(var(--primary))] opacity-0 transition-opacity group-hover:opacity-100">Use this topic →</span>
              </button>
            ))}
          </div>
        )}

        <div className="mt-3 flex flex-col gap-3 sm:flex-row">
          <input value={topic} onChange={(e) => setTopic(e.target.value)} data-testid="podcast-topic-input"
            placeholder="Optional topic (leave blank to auto-pick from your themes)…"
            className="flex-1 rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
          <button onClick={generate} disabled={busy} data-testid="podcast-generate-btn"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-[hsl(var(--accent))] px-6 py-3 text-sm font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
            {busy ? <><Loader2 className="h-4 w-4 animate-spin" /> Starting…</> : <><Sparkles className="h-4 w-4" /> Write script</>}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-border pt-4">
          <span className="text-xs text-muted-foreground">Intro music (plays before every episode). A corporate bed is set by default — replace with your own track anytime.</span>
          <input ref={fileRef} type="file" accept="audio/*" onChange={uploadIntro} className="hidden" data-testid="podcast-intro-input" />
          <button onClick={() => fileRef.current?.click()} disabled={uploading} data-testid="podcast-intro-upload" className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary disabled:opacity-60">
            {uploading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />} {data?.has_intro ? "Replace intro" : "Upload intro"}
          </button>
          {data?.has_intro && <button onClick={removeIntro} data-testid="podcast-intro-remove" className="text-xs font-medium text-red-500 hover:underline">Remove</button>}
        </div>
      </div>

      <div className="mt-6 grid gap-4">
        {episodes.length === 0 && <p className="text-sm text-muted-foreground" data-testid="podcast-admin-empty">No episodes yet. Generate your first script above.</p>}
        {episodes.map((ep) => <AdminEpisode key={ep.id} ep={ep} onChange={load} />)}
      </div>
    </div>
  );
};

export default PodcastAdmin;
