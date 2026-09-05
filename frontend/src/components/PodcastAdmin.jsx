import { useState, useEffect, useRef } from "react";
import { toast } from "sonner";
import { Mic, Sparkles, Loader2, Trash2, Eye, EyeOff, Upload, CheckCircle2, AlertCircle } from "lucide-react";
import api from "@/lib/api";

const STATUS = {
  generating: { cls: "bg-amber-500/15 text-amber-500", icon: Loader2, label: "Generating", spin: true },
  published: { cls: "bg-emerald-500/15 text-emerald-500", icon: CheckCircle2, label: "Published" },
  draft: { cls: "bg-muted text-muted-foreground", icon: EyeOff, label: "Draft" },
  error: { cls: "bg-red-500/15 text-red-500", icon: AlertCircle, label: "Failed" },
};

export const PodcastAdmin = () => {
  const [data, setData] = useState(null);
  const [topic, setTopic] = useState("");
  const [busy, setBusy] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef(null);
  const pollRef = useRef(null);

  const load = () => api.get("/admin/podcast/episodes").then((r) => setData(r.data)).catch(() => {});
  useEffect(() => { load(); return () => clearTimeout(pollRef.current); }, []);

  const generating = (data?.episodes || []).some((e) => e.status === "generating");
  useEffect(() => {
    clearTimeout(pollRef.current);
    if (generating) pollRef.current = setTimeout(load, 5000);
    return () => clearTimeout(pollRef.current);
  }, [generating, data]);

  const generate = async () => {
    setBusy(true);
    try {
      await api.post("/admin/podcast/generate", { topic });
      setTopic("");
      toast.success("Generating a new episode — script + narration takes ~1 min.");
      setTimeout(load, 1500);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Could not start generation.");
    } finally { setBusy(false); }
  };

  const act = async (id, path) => {
    try { await api.post(`/admin/podcast/${id}/${path}`); toast.success("Updated"); load(); }
    catch (e) { toast.error(e?.response?.data?.detail || "Action failed"); }
  };
  const del = async (id) => {
    if (!window.confirm("Delete this episode permanently?")) return;
    try { await api.delete(`/admin/podcast/${id}`); toast.success("Deleted"); load(); } catch (e) { toast.error("Delete failed"); }
  };
  const toggleSchedule = async () => {
    const next = !data.auto_weekly;
    try { await api.post("/admin/podcast/schedule", { enabled: next }); setData({ ...data, auto_weekly: next }); toast.success(next ? "Weekly auto-publish ON" : "Weekly auto-publish OFF"); }
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

  return (
    <div data-testid="podcast-admin">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h2 className="flex items-center gap-2 font-display text-2xl font-bold"><Mic className="h-5 w-5 text-[hsl(var(--primary))]" /> The SK Strategy Brief</h2>
          <p className="mt-1 text-sm text-muted-foreground">AI-scripted, Onyx-narrated weekly podcast. Each episode opens in your voice, then delivers a rich take.</p>
        </div>
        <label className="flex cursor-pointer select-none items-center gap-2 rounded-full border border-border px-4 py-2 text-sm" data-testid="podcast-schedule-toggle">
          <input type="checkbox" checked={!!data?.auto_weekly} onChange={toggleSchedule} className="accent-[hsl(var(--primary))]" />
          Auto-publish weekly (Mon)
        </label>
      </div>

      <div className="mt-6 rounded-2xl border border-border bg-card p-6">
        <p className="text-sm font-semibold">Generate a new episode</p>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row">
          <input value={topic} onChange={(e) => setTopic(e.target.value)} data-testid="podcast-topic-input"
            placeholder="Optional topic (leave blank to auto-pick from your themes)…"
            className="flex-1 rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
          <button onClick={generate} disabled={busy} data-testid="podcast-generate-btn"
            className="inline-flex items-center justify-center gap-2 rounded-full bg-[hsl(var(--accent))] px-6 py-3 text-sm font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
            {busy ? <><Loader2 className="h-4 w-4 animate-spin" /> Starting…</> : <><Sparkles className="h-4 w-4" /> Generate episode</>}
          </button>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-border pt-4">
          <span className="text-xs text-muted-foreground">Optional: your recorded intro clip (played before every episode).</span>
          <input ref={fileRef} type="file" accept="audio/*" onChange={uploadIntro} className="hidden" data-testid="podcast-intro-input" />
          <button onClick={() => fileRef.current?.click()} disabled={uploading} data-testid="podcast-intro-upload" className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary disabled:opacity-60">
            {uploading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />} {data?.has_intro ? "Replace intro" : "Upload intro"}
          </button>
          {data?.has_intro && <button onClick={removeIntro} data-testid="podcast-intro-remove" className="text-xs font-medium text-red-500 hover:underline">Remove</button>}
        </div>
      </div>

      <div className="mt-6 grid gap-4">
        {episodes.length === 0 && <p className="text-sm text-muted-foreground" data-testid="podcast-admin-empty">No episodes yet. Generate your first one above.</p>}
        {episodes.map((ep) => {
          const s = STATUS[ep.status] || STATUS.draft;
          const Icon = s.icon;
          return (
            <div key={ep.id} className="rounded-2xl border border-border bg-card p-5" data-testid={`podcast-admin-ep-${ep.id}`}>
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold ${s.cls}`}>
                      <Icon className={`h-3.5 w-3.5 ${s.spin ? "animate-spin" : ""}`} /> {s.label}
                    </span>
                    {ep.duration_min && <span className="text-xs text-muted-foreground">{ep.duration_min} min</span>}
                  </div>
                  <h4 className="mt-2 font-display text-base font-bold">{ep.title}</h4>
                  {ep.description && <p className="mt-1 text-sm text-muted-foreground">{ep.description}</p>}
                  {ep.status === "error" && ep.error && <p className="mt-1 text-xs text-red-500">{ep.error}</p>}
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {ep.status === "published" && <button onClick={() => act(ep.id, "unpublish")} data-testid={`podcast-unpublish-${ep.id}`} className="inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 text-xs hover:bg-secondary"><EyeOff className="h-3.5 w-3.5" /> Unpublish</button>}
                  {(ep.status === "draft") && ep.has_audio && <button onClick={() => act(ep.id, "publish")} data-testid={`podcast-publish-${ep.id}`} className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-3 py-1.5 text-xs font-semibold text-[hsl(var(--primary-foreground))]"><Eye className="h-3.5 w-3.5" /> Publish</button>}
                  <button onClick={() => del(ep.id)} data-testid={`podcast-delete-${ep.id}`} className="inline-flex items-center gap-1 rounded-full border border-border px-3 py-1.5 text-xs text-red-500 hover:bg-red-500/10"><Trash2 className="h-3.5 w-3.5" /></button>
                </div>
              </div>
              {ep.has_audio && <audio src={`${process.env.REACT_APP_BACKEND_URL}/api/podcast/episodes/${ep.id}/audio`} controls preload="none" className="mt-3 w-full" />}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PodcastAdmin;
