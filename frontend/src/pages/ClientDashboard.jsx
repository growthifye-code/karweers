import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { useAuth } from "@/context/AuthContext";
import { Logo } from "@/components/Navbar";
import ThemeToggle from "@/components/ThemeToggle";
import VideoCard from "@/components/VideoCard";
import api, { track } from "@/lib/api";
import {
  Sparkles, Calendar, BookOpen, GraduationCap, ArrowUpRight, LifeBuoy,
  ShieldCheck, Download, Trash2, Check, MessageSquarePlus,
} from "lucide-react";

const PRIORITIES = ["low", "medium", "high"];

function InterestPicker({ topics, current, onSave }) {
  const [sel, setSel] = useState(current || []);
  const toggle = (id) => setSel((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));
  return (
    <div className="rounded-2xl border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/5 p-8" data-testid="interest-picker">
      <div className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-[hsl(var(--primary))]" />
        <h2 className="font-display text-xl font-bold">Tell us what you care about</h2>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">Pick a few topics and we'll tailor your videos and blogs to you.</p>
      <div className="mt-5 flex flex-wrap gap-2">
        {topics.map((t) => (
          <button key={t.id} onClick={() => toggle(t.id)} data-testid={`interest-${t.id}`}
            className={`rounded-full border px-4 py-2 text-sm font-medium transition-colors ${sel.includes(t.id) ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border-border text-muted-foreground hover:border-[hsl(var(--primary))]/50"}`}>
            {sel.includes(t.id) && <Check className="mr-1 inline h-3.5 w-3.5" />}{t.label}
          </button>
        ))}
      </div>
      <button onClick={() => onSave(sel)} data-testid="save-interests"
        className="mt-6 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
        Save my interests
      </button>
    </div>
  );
}

function ServiceDesk() {
  const [tickets, setTickets] = useState([]);
  const [form, setForm] = useState({ subject: "", message: "", category: "General", priority: "medium" });
  const [reply, setReply] = useState({});
  const load = () => api.get("/tickets").then((r) => setTickets(r.data)).catch(() => {});
  useEffect(() => { load(); }, []);

  const create = async (e) => {
    e.preventDefault();
    if (!form.subject.trim() || !form.message.trim()) { toast.error("Add a subject and message."); return; }
    try {
      await api.post("/tickets", form);
      toast.success("Ticket raised — we'll get back to you.");
      setForm({ subject: "", message: "", category: "General", priority: "medium" });
      load();
    } catch { toast.error("Could not raise ticket."); }
  };
  const sendReply = async (id) => {
    if (!reply[id]?.trim()) return;
    try { await api.post(`/tickets/${id}/reply`, { message: reply[id] }); setReply((r) => ({ ...r, [id]: "" })); load(); }
    catch { toast.error("Reply failed."); }
  };

  return (
    <section className="mt-16" data-testid="service-desk">
      <div className="flex items-center gap-2">
        <LifeBuoy className="h-5 w-5 text-[hsl(var(--primary))]" />
        <h2 className="font-display text-2xl font-bold">Service Desk</h2>
      </div>
      <div className="mt-6 grid gap-6 lg:grid-cols-[1fr_1.3fr]">
        <form onSubmit={create} className="rounded-2xl border border-border bg-card p-6" data-testid="ticket-form">
          <div className="flex items-center gap-2"><MessageSquarePlus className="h-5 w-5 text-[hsl(var(--accent))]" /><h3 className="font-display font-bold">Raise a ticket</h3></div>
          <input value={form.subject} onChange={(e) => setForm({ ...form, subject: e.target.value })} placeholder="Subject" data-testid="ticket-subject" className="mt-4 w-full rounded-lg border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
          <textarea value={form.message} onChange={(e) => setForm({ ...form, message: e.target.value })} placeholder="How can we help?" rows={4} data-testid="ticket-message" className="mt-3 w-full rounded-lg border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
          <div className="mt-3 grid grid-cols-2 gap-3">
            <select value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} data-testid="ticket-category" className="rounded-lg border border-border bg-background px-3 py-2.5 text-sm">
              {["General", "Booking", "Billing", "Technical", "Advisory"].map((c) => <option key={c}>{c}</option>)}
            </select>
            <select value={form.priority} onChange={(e) => setForm({ ...form, priority: e.target.value })} data-testid="ticket-priority" className="rounded-lg border border-border bg-background px-3 py-2.5 text-sm capitalize">
              {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <button type="submit" data-testid="ticket-submit" className="mt-4 w-full rounded-full bg-[hsl(var(--accent))] px-6 py-3 text-sm font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5">Submit ticket</button>
        </form>

        <div className="space-y-4" data-testid="ticket-list">
          {tickets.length === 0 && <div className="rounded-2xl border border-dashed border-border p-8 text-center text-sm text-muted-foreground">No tickets yet. Raise one and we'll respond here.</div>}
          {tickets.map((t) => (
            <div key={t.id} className="rounded-2xl border border-border bg-card p-5" data-testid={`ticket-${t.id}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold">{t.subject}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{t.ticket_code} · {t.category} · <span className="capitalize">{t.priority}</span></p>
                </div>
                <span className={`rounded-full px-3 py-1 text-xs font-semibold capitalize ${t.status === "resolved" || t.status === "closed" ? "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]" : "bg-secondary text-muted-foreground"}`}>{t.status}</span>
              </div>
              <p className="mt-3 text-sm text-muted-foreground">{t.message}</p>
              {t.replies?.length > 0 && (
                <div className="mt-4 space-y-2 border-t border-border pt-4">
                  {t.replies.map((r, i) => (
                    <div key={i} className={`rounded-lg p-3 text-sm ${r.role === "admin" ? "bg-[hsl(var(--primary))]/10" : "bg-secondary"}`}>
                      <span className="text-xs font-semibold">{r.role === "admin" ? "Team SK" : "You"}</span>
                      <p className="mt-1 text-muted-foreground">{r.message}</p>
                    </div>
                  ))}
                </div>
              )}
              <div className="mt-3 flex gap-2">
                <input value={reply[t.id] || ""} onChange={(e) => setReply({ ...reply, [t.id]: e.target.value })} placeholder="Reply…" data-testid={`ticket-reply-input-${t.id}`} className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none" />
                <button onClick={() => sendReply(t.id)} data-testid={`ticket-reply-send-${t.id}`} className="rounded-lg border border-border px-4 py-2 text-sm font-medium hover:bg-secondary">Send</button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

export default function ClientDashboard() {
  const { user, logout } = useAuth();
  const [topics, setTopics] = useState([]);
  const [interests, setInterests] = useState(user?.interests || []);
  const [recommended, setRecommended] = useState([]);
  const [personalised, setPersonalised] = useState(false);
  const [blogs, setBlogs] = useState([]);

  const loadRecs = () => {
    api.get("/learning/recommended", { params: { limit: 4 } })
      .then((r) => { setRecommended(r.data.videos || []); setPersonalised(r.data.personalised); }).catch(() => {});
    api.get("/me/blogs", { params: { limit: 4 } }).then((r) => setBlogs(r.data.articles || [])).catch(() => {});
  };
  useEffect(() => {
    api.get("/learning/topics").then((r) => setTopics(r.data || [])).catch(() => {});
    api.get("/auth/me").then((r) => setInterests(r.data.interests || [])).catch(() => {});
    loadRecs();
  }, []);

  const saveInterests = async (sel) => {
    try {
      await api.post("/me/interests", { interests: sel });
      setInterests(sel);
      toast.success("Interests saved — your feed is now tailored.");
      setTimeout(loadRecs, 400);
    } catch { toast.error("Could not save interests."); }
  };

  const downloadData = async () => {
    try {
      const { data } = await api.get("/me/data");
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = "my-data.json"; a.click();
      URL.revokeObjectURL(url);
      toast.success("Your data was exported.");
    } catch { toast.error("Export failed."); }
  };
  const deleteAccount = async () => {
    if (!window.confirm("Permanently delete your account and all activity? This cannot be undone.")) return;
    try { await api.delete("/me"); toast.success("Account deleted."); logout(true); }
    catch { toast.error("Deletion failed."); }
  };

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Logo />
          <div className="flex items-center gap-3">
            <ThemeToggle />
            <Link to="/" className="text-sm text-muted-foreground hover:text-foreground">View site</Link>
            <button onClick={logout} data-testid="client-logout" className="rounded-full border border-border px-4 py-2 text-sm font-medium hover:bg-secondary">Logout</button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-14">
        <div className="flex items-center gap-4">
          {user?.picture && <img src={user.picture} alt={user.name} className="h-12 w-12 rounded-full border border-border object-cover" />}
          <div>
            <p className="text-sm text-muted-foreground">Client Portal {user?.client_code && <span className="ml-2 rounded-full bg-secondary px-2 py-0.5 text-xs font-semibold text-foreground" data-testid="client-code">{user.client_code}</span>}</p>
            <h1 className="mt-1 font-display text-3xl font-bold">Welcome, {user?.name} 👋</h1>
          </div>
        </div>

        <div className="mt-10 grid gap-6 md:grid-cols-3">
          <Link to="/learning" className="group rounded-2xl border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/5 p-8 transition-transform hover:-translate-y-1" data-testid="client-learning">
            <GraduationCap className="h-8 w-8 text-[hsl(var(--primary))]" />
            <h3 className="mt-4 font-display text-lg font-bold">Learning Hub</h3>
            <p className="mt-2 text-sm text-muted-foreground">Curated videos on economy, energy, technology & leadership — always fresh.</p>
          </Link>
          <Link to="/#consult" className="group rounded-2xl border border-border bg-card p-8 transition-transform hover:-translate-y-1" data-testid="client-book">
            <Calendar className="h-8 w-8 text-[hsl(var(--accent))]" />
            <h3 className="mt-4 font-display text-lg font-bold">Book a Consultation</h3>
            <p className="mt-2 text-sm text-muted-foreground">Request a premium 1:1 strategic session with Sudarshan.</p>
          </Link>
          <Link to="/insights" className="group rounded-2xl border border-border bg-card p-8 transition-transform hover:-translate-y-1" data-testid="client-insights">
            <BookOpen className="h-8 w-8 text-[hsl(var(--primary))]" />
            <h3 className="mt-4 font-display text-lg font-bold">Explore Insights</h3>
            <p className="mt-2 text-sm text-muted-foreground">News, analysis, R&D and case studies across the energy transition.</p>
          </Link>
        </div>

        {topics.length > 0 && interests.length === 0 && (
          <div className="mt-12"><InterestPicker topics={topics} current={interests} onSave={saveInterests} /></div>
        )}
        {interests.length > 0 && (
          <div className="mt-12 flex flex-wrap items-center gap-2" data-testid="my-interests">
            <span className="text-sm font-semibold text-muted-foreground">Your interests:</span>
            {interests.map((id) => <span key={id} className="rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-medium text-[hsl(var(--primary))]">{topics.find((t) => t.id === id)?.label || id}</span>)}
            <button onClick={() => setInterests([])} className="text-xs font-medium text-muted-foreground underline hover:text-foreground">edit</button>
          </div>
        )}

        {recommended.length > 0 && (
          <section className="mt-14" data-testid="dashboard-recommended">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2"><Sparkles className="h-5 w-5 text-[hsl(var(--primary))]" /><h2 className="font-display text-2xl font-bold">Recommended videos</h2></div>
              <Link to="/learning" className="group inline-flex items-center gap-1.5 text-sm font-semibold text-[hsl(var(--primary))]">View all <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" /></Link>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">{personalised ? "Based on your interests and what you've been exploring." : "Set your interests above and play a few videos to personalise this."}</p>
            <div className="mt-6 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {recommended.map((v) => <VideoCard key={v.video_id} video={v} onPlay={(topic) => { track("video", topic); setTimeout(loadRecs, 800); }} />)}
            </div>
          </section>
        )}

        {blogs.length > 0 && (
          <section className="mt-14" data-testid="dashboard-blogs">
            <div className="flex items-center gap-2"><BookOpen className="h-5 w-5 text-[hsl(var(--primary))]" /><h2 className="font-display text-2xl font-bold">Relevant blogs & insights</h2></div>
            <div className="mt-6 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
              {blogs.map((a) => (
                <Link key={a.slug} to={`/insights/${a.slug}`} onClick={() => track("insight", a.sector)} className="group overflow-hidden rounded-2xl border border-border bg-card transition-transform hover:-translate-y-1" data-testid={`blog-${a.slug}`}>
                  {a.image && <div className="aspect-[16/10] overflow-hidden"><img src={a.image} alt="" className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" /></div>}
                  <div className="p-4">
                    <p className="text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--primary))]">{a.category} · {a.sector}</p>
                    <h3 className="mt-2 line-clamp-2 text-sm font-semibold leading-snug">{a.title}</h3>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}

        <ServiceDesk />

        <section className="mt-16 rounded-2xl border border-border bg-card p-8" data-testid="privacy-controls">
          <div className="flex items-center gap-2"><ShieldCheck className="h-6 w-6 text-[hsl(var(--primary))]" /><h2 className="font-display text-xl font-bold">Your data & privacy</h2></div>
          <p className="mt-2 text-sm text-muted-foreground">In line with GDPR, you can export or permanently delete your data at any time.</p>
          <div className="mt-5 flex flex-wrap gap-3">
            <button onClick={downloadData} data-testid="download-data" className="inline-flex items-center gap-2 rounded-full border border-border px-5 py-2.5 text-sm font-medium hover:bg-secondary"><Download className="h-4 w-4" /> Download my data</button>
            <button onClick={deleteAccount} data-testid="delete-account" className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--destructive))]/40 px-5 py-2.5 text-sm font-medium text-[hsl(var(--destructive))] hover:bg-[hsl(var(--destructive))]/10"><Trash2 className="h-4 w-4" /> Delete my account</button>
          </div>
        </section>
      </main>
    </div>
  );
}
