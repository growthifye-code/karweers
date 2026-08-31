import { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { useAuth, formatApiErrorDetail } from "@/context/AuthContext";
import { Logo } from "@/components/Navbar";
import ThemeToggle from "@/components/ThemeToggle";
import { Users, FileText, Inbox, Sparkles, Trash2, Wand2, Mail, LifeBuoy, UserCircle, ChevronDown, Tag, AlertTriangle, Star, Target, Package, Pencil, TrendingUp, TrendingDown, ShieldAlert, Unlock, CalendarCheck, CalendarX, RefreshCw, ClipboardCheck } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend, CartesianGrid } from "recharts";
import api, { API } from "@/lib/api";
import VaultPanel from "@/pages/VaultPanel";

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
  const [chartMetric, setChartMetric] = useState("volume");
  const [ticketReplies, setTicketReplies] = useState({});
  const [goalInput, setGoalInput] = useState("");
  const [goalEditing, setGoalEditing] = useState(false);
  const [savingGoal, setSavingGoal] = useState(false);
  const [loginAttempts, setLoginAttempts] = useState(null);
  const [security, setSecurity] = useState(null);
  const [vpnGuard, setVpnGuard] = useState(null);
  const [allowlistText, setAllowlistText] = useState("");
  const [tokenLabel, setTokenLabel] = useState("");
  const [provisioned, setProvisioned] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [calStatus, setCalStatus] = useState(null);
  const [availWeek, setAvailWeek] = useState(null);
  const [reschedule, setReschedule] = useState(null);
  const [confirming, setConfirming] = useState(null);
  const [bufferInput, setBufferInput] = useState("0");
  const [reminderSel, setReminderSel] = useState("24");
  const [cancelWin, setCancelWin] = useState("24");
  const [consentLogs, setConsentLogs] = useState(null);
  const [policyInfo, setPolicyInfo] = useState(null);
  const [newVersion, setNewVersion] = useState("");
  const [testTo, setTestTo] = useState("");
  const [cardAccent, setCardAccent] = useState("#C6F135");
  const [cardBust, setCardBust] = useState(Date.now());
  const [regenBusy, setRegenBusy] = useState(false);

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
    api.get("/admin/login-attempts").then((r) => setLoginAttempts(r.data)).catch(() => {});
    api.get("/admin/security").then((r) => {
      setSecurity(r.data);
      if (r.data.unseen > 0) {
        toast.warning(`${r.data.unseen} new security alert${r.data.unseen > 1 ? "s" : ""} — ${r.data.active_bans} IP${r.data.active_bans !== 1 ? "s" : ""} auto-blocked.`, { duration: 8000 });
        api.post("/admin/security/seen").catch(() => {});
      }
    }).catch(() => {});
    api.get("/admin/vpn-guard").then((r) => { setVpnGuard(r.data); setAllowlistText((r.data.allowlist || []).join("\n")); }).catch(() => {});
    api.get("/admin/audit-log").then((r) => setAuditLog(r.data.logs || [])).catch(() => {});
    api.get("/admin/bookings").then((r) => setBookings(r.data)).catch(() => {});
    api.get("/admin/calendar/status").then((r) => setCalStatus(r.data)).catch(() => {});
    api.get("/admin/consent-logs").then((r) => setConsentLogs(r.data)).catch(() => {});
    api.get("/admin/policy-version").then((r) => { setPolicyInfo(r.data); setNewVersion(r.data.version || ""); }).catch(() => {});
    api.get("/admin/card-style").then((r) => setCardAccent(r.data.accent || "#C6F135")).catch(() => {});
  };
  useEffect(load, []);

  const sendTestEmail = async () => {
    const to = (testTo || "").trim();
    if (!to) { toast.error("Enter an email address."); return; }
    try {
      const { data } = await api.post("/admin/email/test", { to });
      if (data.sent) toast.success(`Test email sent to ${to}.`);
      else toast.error(data.skipped === "email_not_configured" ? "Email is not configured yet." : "Could not send test email.");
    } catch (e) { toast.error(formatApiErrorDetail(e.response?.data?.detail) || "Could not send test email."); }
  };
  const previewDigest = async () => {
    try {
      const { data } = await api.get("/admin/signals-digest/preview");
      const w = window.open("", "_blank");
      if (w) { w.document.open(); w.document.write(data); w.document.close(); }
    } catch { toast.error("Could not load the digest preview."); }
  };
  const sendDigestNow = async () => {
    if (!window.confirm("Send the weekly Market Signals digest to all subscribers now?")) return;
    try {
      const { data } = await api.post("/admin/signals-digest/run");
      if (data.sent) toast.success(`Digest sent to ${data.subscribers} subscriber(s).`);
      else toast.error("Email is not configured yet.");
    } catch { toast.error("Could not send the digest."); }
  };
  const sendLibraryDigestNow = async () => {
    if (!window.confirm("Send this week's Library shelf digest to all subscribers now?")) return;
    try {
      const { data } = await api.post("/admin/library-digest/run");
      if (data.sent) toast.success(`Library digest sent to ${data.subscribers} subscriber(s).`);
      else toast.error("Email is not configured yet.");
    } catch { toast.error("Could not send the library digest."); }
  };
  const saveCardAccent = async (accent) => {
    try {
      await api.post("/admin/card-style", { accent });
      setCardAccent(accent);
      setCardBust(Date.now());
      toast.success("Share card accent updated.");
    } catch (e) { toast.error(formatApiErrorDetail(e.response?.data?.detail) || "Could not update accent."); }
  };

  const bumpPolicy = async () => {
    const v = (newVersion || "").trim();
    if (!v) { toast.error("Enter a version."); return; }
    if (!window.confirm(`Set policy version to "${v}"? Every client will be asked to re-agree on their next visit.`)) return;
    try {
      await api.post("/admin/policy-version", { version: v });
      const r = await api.get("/admin/policy-version");
      setPolicyInfo(r.data);
      toast.success(`Policy version set to ${v}. Clients will re-agree on next visit.`);
    } catch (e) {
      toast.error(formatApiErrorDetail(e.response?.data?.detail) || "Could not update policy version.");
    }
  };

  const regenerateHome = async () => {
    setRegenBusy(true);
    try {
      await api.post("/admin/home/regenerate");
      toast.success("Homepage content regenerated. Refresh the site to see it.");
    } catch (e) {
      toast.error(formatApiErrorDetail(e.response?.data?.detail) || "Could not regenerate — try again shortly.");
    } finally {
      setRegenBusy(false);
    }
  };
  const exportConsent = async () => {
    try {
      const res = await api.get("/admin/consent-logs/export", { responseType: "blob" });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement("a");
      a.href = url; a.download = "consent-log.csv"; a.click();
      window.URL.revokeObjectURL(url);
    } catch { toast.error("Could not export consent log."); }
  };

  useEffect(() => {
    const p = new URLSearchParams(window.location.search).get("calendar");
    if (p === "connected") { toast.success("Google Calendar connected — confirmed sessions will sync automatically."); window.history.replaceState({}, "", "/admin"); }
    else if (p === "error") { toast.error("Could not connect Google Calendar. Please try again."); window.history.replaceState({}, "", "/admin"); }
  }, []);

  const calWarnedRef = useRef(false);
  useEffect(() => {
    if (calStatus?.connected && calStatus.healthy === false && !calWarnedRef.current) {
      calWarnedRef.current = true;
      toast.warning("Google Calendar needs reconnecting — session syncing is paused. Open the Bookings tab to reconnect.", { duration: 9000 });
    }
  }, [calStatus?.healthy, calStatus?.connected]);


  const connectCalendar = async () => {
    try { const { data } = await api.get("/admin/calendar/oauth/start"); window.location.href = data.authorization_url; }
    catch (e) { toast.error(formatApiErrorDetail(e.response?.data?.detail) || "Calendar not configured."); }
  };
  const disconnectCalendar = async () => {
    try { await api.post("/admin/calendar/disconnect"); setCalStatus((s) => ({ ...s, connected: false, email: null })); toast.success("Google Calendar disconnected."); }
    catch { toast.error("Could not disconnect."); }
  };

  const leadsToKey = (l) => { const s = (l || []).slice().sort((a, b) => a - b).join(","); return s === "2,24" ? "both" : s === "24" ? "24" : s === "2" ? "2" : "off"; };
  const keyToLeads = (k) => k === "both" ? [2, 24] : k === "24" ? [24] : k === "2" ? [2] : [];
  const loadAvailability = (ws) => {
    api.get("/admin/availability", { params: ws ? { week_start: ws } : {} })
      .then((r) => { setAvailWeek(r.data); setBufferInput(String(r.data.buffer_minutes ?? 0)); setReminderSel(leadsToKey(r.data.reminder_leads)); setCancelWin(String(r.data.cancel_cutoff_hours ?? 24)); }).catch(() => {});
  };
  useEffect(() => { loadAvailability(); }, []);

  const saveCancelWindow = async (hours) => {
    try { await api.post("/admin/availability/cancel-window", { hours: Number(hours) }); toast.success(Number(hours) > 0 ? `Clients can't cancel online within ${hours}h of a session.` : "Online cancellation window removed."); loadAvailability(availWeek?.week_start); }
    catch { toast.error("Could not save cancellation window."); }
  };

  const saveBuffer = async (mins) => {
    try { await api.post("/admin/availability/buffer", { minutes: Number(mins) }); toast.success(Number(mins) > 0 ? `Buffer set to ${mins} min between sessions.` : "Buffer removed."); loadAvailability(availWeek?.week_start); }
    catch { toast.error("Could not save buffer."); }
  };
  const saveReminders = async (key) => {
    try { await api.post("/admin/availability/reminders", { leads: keyToLeads(key) }); toast.success(key === "off" ? "Client reminders turned off." : "Reminder timing saved."); loadAvailability(availWeek?.week_start); }
    catch { toast.error("Could not save reminder timing."); }
  };

  const upcomingCount = (() => {
    const now = new Date();
    const in48 = new Date(now.getTime() + 48 * 3600 * 1000);
    return bookings.filter((b) => {
      if (b.status !== "confirmed" || !b.slot_date || !b.slot_time) return false;
      const dt = new Date(`${b.slot_date}T${b.slot_time}:00+05:30`);
      return dt >= now && dt <= in48;
    }).length;
  })();

  const renderAgenda = () => {
    const now = new Date();
    const in48 = new Date(now.getTime() + 48 * 3600 * 1000);
    const agenda = bookings
      .filter((b) => b.status === "confirmed" && b.slot_date && b.slot_time)
      .map((b) => ({ ...b, dt: new Date(`${b.slot_date}T${b.slot_time}:00+05:30`) }))
      .filter((b) => b.dt >= now && b.dt <= in48)
      .sort((a, b) => a.dt - b.dt);
    return (
      <div className="mb-4 rounded-2xl border border-border bg-card p-4" data-testid="today-agenda">
        <p className="flex items-center gap-2 text-sm font-semibold"><CalendarCheck className="h-4 w-4 text-[hsl(var(--primary))]" /> Next 24–48 hours <span className="text-xs font-normal text-muted-foreground">· upcoming confirmed sessions</span></p>
        {agenda.length === 0 ? (
          <p className="mt-2 text-xs text-muted-foreground" data-testid="agenda-empty">No confirmed sessions in the next 48 hours.</p>
        ) : (
          <div className="mt-3 flex gap-3 overflow-x-auto pb-1">
            {agenda.map((b) => (
              <div key={b.id} data-testid={`agenda-${b.id}`} className="min-w-[210px] rounded-xl border border-[hsl(var(--primary))]/30 bg-[hsl(var(--primary))]/5 p-3">
                <p className="text-xs font-semibold text-[hsl(var(--primary))]">{b.dt.toLocaleString("en-GB", { timeZone: "Asia/Kolkata", weekday: "short", day: "numeric", month: "short" })} · {b.slot_time} IST</p>
                <p className="mt-1 text-sm font-medium">{b.name}</p>
                <p className="text-xs text-muted-foreground">{b.package}</p>
                {b.meeting_link && <a href={b.meeting_link} target="_blank" rel="noreferrer" className="mt-1 inline-block text-xs font-medium text-[hsl(var(--primary))] underline">Join →</a>}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  const shiftWeek = (deltaDays) => {
    if (!availWeek) return;
    const d = new Date(availWeek.week_start + "T00:00:00");
    d.setDate(d.getDate() + deltaDays);
    loadAvailability(d.toISOString().slice(0, 10));
  };
  const toggleSlot = async (date, time, state) => {
    if (state === "booked") { toast.info("This slot is already booked."); return; }
    try {
      await api.post("/admin/availability/toggle", { date, time, blocked: state !== "blocked" });
      loadAvailability(availWeek?.week_start);
    } catch { toast.error("Could not update slot."); }
  };
  const blockDay = async (date, blocked) => {
    try { await api.post("/admin/availability/block-day", { date, blocked }); loadAvailability(availWeek?.week_start); }
    catch { toast.error("Could not update day."); }
  };
  const publishWeek = async () => {
    if (!availWeek) return;
    try {
      await api.post("/admin/availability/publish", { week_start: availWeek.week_start });
      toast.success("Week published — visitors can now book these slots.");
      loadAvailability(availWeek.week_start);
    } catch { toast.error("Publish failed."); }
  };
  const bookingAction = async (id, action, payload) => {
    try {
      await api.post(`/admin/bookings/${id}/${action}`, payload || {});
      toast.success(action === "confirm" ? "Booking confirmed — client notified." : action === "decline" ? "Booking declined." : "Rescheduled — client notified.");
      setReschedule(null);
      setConfirming(null);
      api.get("/admin/bookings").then((r) => setBookings(r.data)).catch(() => {});
      loadAvailability(availWeek?.week_start);
    } catch (e) { toast.error(formatApiErrorDetail(e.response?.data?.detail) || "Action failed."); }
  };

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

  const exportAnalytics = async () => {
    try {
      const res = await api.get("/admin/lead-analytics/export", { responseType: "blob" });
      const url = URL.createObjectURL(res.data);
      const a = document.createElement("a"); a.href = url; a.download = "lead-source-analytics.csv"; a.click();
      URL.revokeObjectURL(url);
      toast.success("Analytics exported.");
    } catch { toast.error("Export failed."); }
  };
  const emailReport = async () => {
    try {
      const { data } = await api.post("/admin/report/run");
      if (data.sent) toast.success(`Report emailed to ${data.to}.`);
      else toast.info("Email isn't configured yet — add a Gmail App Password to enable monthly reports.");
    } catch { toast.error("Could not send report."); }
  };
  const saveGoal = async () => {
    const target = parseInt(goalInput, 10);
    if (isNaN(target) || target < 0) { toast.error("Enter a valid target amount."); return; }
    setSavingGoal(true);
    try {
      await api.post("/admin/revenue-goal", { target });
      setAnalytics((a) => a ? { ...a, revenue_goal: target } : a);
      setGoalEditing(false);
      toast.success("Monthly revenue goal updated.");
    } catch { toast.error("Could not save goal."); }
    finally { setSavingGoal(false); }
  };
  const unlockLogin = async (ip, email) => {
    try {
      await api.post("/admin/login-attempts/unlock", { ip, email });
      const r = await api.get("/admin/login-attempts");
      setLoginAttempts(r.data);
      toast.success(`Cleared lockout for ${email || ip}.`);
    } catch { toast.error("Could not clear lockout."); }
  };
  const unbanIp = async (ip) => {
    try {
      await api.post("/admin/security/unban", { ip });
      const r = await api.get("/admin/security");
      setSecurity(r.data);
      toast.success(`Unblocked ${ip}.`);
    } catch { toast.error("Could not unblock IP."); }
  };
  const banIp = async (ip) => {
    try {
      await api.post("/admin/security/ban", { ip });
      const r = await api.get("/admin/security"); setSecurity(r.data);
      toast.success(`Blocked ${ip}.`);
    } catch { toast.error("Could not block IP."); }
  };
  const banRange = async (subnet) => {
    try {
      await api.post("/admin/security/ban-range", { subnet });
      const r = await api.get("/admin/security"); setSecurity(r.data);
      toast.success(`Blocked range ${subnet}.`);
    } catch { toast.error("Could not block range."); }
  };
  const toggleVpnGuard = async () => {
    try {
      const next = !vpnGuard?.enabled;
      const { data } = await api.post("/admin/vpn-guard/toggle", { enabled: next });
      setVpnGuard((g) => ({ ...g, enabled: data.enabled }));
      toast.success(`VPN guard ${data.enabled ? "enabled" : "disabled"}.`);
    } catch { toast.error("Could not update VPN guard."); }
  };
  const saveVpnAllowlist = async () => {
    try {
      const ips = allowlistText.split(/[\n,]/).map((s) => s.trim()).filter(Boolean);
      const { data } = await api.post("/admin/vpn-guard/allowlist", { ips });
      setVpnGuard((g) => ({ ...g, allowlist: data.ips }));
      toast.success("Trusted IP allowlist saved.");
    } catch { toast.error("Could not save allowlist."); }
  };
  const addVpnToken = async () => {
    try {
      const { data } = await api.post("/admin/vpn-guard/token", { label: tokenLabel || "Trusted token" });
      setProvisioned(data);
      setTokenLabel("");
      const r = await api.get("/admin/vpn-guard"); setVpnGuard(r.data);
      toast.success("Trusted token created — scan the QR now.");
    } catch { toast.error("Could not create token."); }
  };
  const delVpnToken = async (id) => {
    try {
      await api.delete(`/admin/vpn-guard/token/${id}`);
      const r = await api.get("/admin/vpn-guard"); setVpnGuard(r.data);
      toast.success("Token removed.");
    } catch { toast.error("Could not remove token."); }
  };
  const blockCountry = async (code, country) => {
    try {
      await api.post("/admin/security/block-country", { code, country });
      const r = await api.get("/admin/security"); setSecurity(r.data);
      toast.success(`Blocked ${country || code}.`);
    } catch (e) { toast.error(e?.response?.data?.detail || "Could not block country."); }
  };
  const unblockCountry = async (code) => {
    try {
      await api.post("/admin/security/unblock-country", { code });
      const r = await api.get("/admin/security"); setSecurity(r.data);
      toast.success(`Unblocked ${code}.`);
    } catch { toast.error("Could not unblock country."); }
  };

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
    if (!aiTopic.trim()) { toast.error("Enter a topic to draft an article about."); return; }
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
      toast.success("Draft generated — review and publish.");
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Generation failed");
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
          {["overview", "crm", "leads", "bookings", "availability", "tickets", "articles", "create", "subscribers", "consent", "vault"].map((t) => (
            <button key={t} onClick={() => setTab(t)} data-testid={`admin-tab-${t}`}
              className={`rounded-full px-4 py-2 text-sm font-medium capitalize transition-colors ${tab === t ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border border-border text-muted-foreground hover:bg-secondary"}`}>
              {t === "create" ? "Create" : t === "crm" ? "CRM" : t === "tickets" ? "Service Desk" : t === "consent" ? "Consent Log" : t}
              {t === "bookings" && upcomingCount > 0 && <span data-testid="bookings-badge" className={`ml-1.5 rounded-full px-1.5 py-0.5 text-[10px] font-bold normal-case ${tab === t ? "bg-[hsl(var(--primary-foreground))] text-[hsl(var(--primary))]" : "bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]"}`}>{upcomingCount} in 48h</span>}
            </button>
          ))}
        </div>

        {tab === "overview" && (
          <div className="mt-8 space-y-8" data-testid="admin-overview">
            {renderAgenda()}
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-border bg-card p-5" data-testid="ai-home-card">
              <div className="flex items-start gap-3">
                <Sparkles className="mt-0.5 h-5 w-5 text-[hsl(var(--primary))]" />
                <div>
                  <p className="font-display text-base font-bold">Homepage Content</p>
                  <p className="text-xs text-muted-foreground">Hero copy, insight blurbs & the Market Signals feed refresh automatically every 24h. Force a fresh set anytime.</p>
                </div>
              </div>
              <button onClick={regenerateHome} disabled={regenBusy} data-testid="regenerate-home"
                className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
                <RefreshCw className={`h-4 w-4 ${regenBusy ? "animate-spin" : ""}`} /> {regenBusy ? "Regenerating…" : "Regenerate now"}
              </button>
            </div>

            <div className="grid gap-6 lg:grid-cols-2" data-testid="email-share-tools">
              <div className="rounded-2xl border border-border bg-card p-5">
                <p className="flex items-center gap-2 font-display text-base font-bold"><Mail className="h-4 w-4 text-[hsl(var(--primary))]" /> Email & deliverability</p>
                <p className="mt-1 text-xs text-muted-foreground">Send a test email (run it through mail-tester.com to check SPF/DKIM/DMARC).</p>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  <input value={testTo} onChange={(e) => setTestTo(e.target.value)} data-testid="test-email-input" placeholder="you@example.com"
                    className="min-w-[200px] flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]" />
                  <button onClick={sendTestEmail} data-testid="send-test-email" className="rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">Send test</button>
                </div>
                <div className="mt-5 border-t border-border pt-4">
                  <p className="text-sm font-semibold">Weekly signals digest</p>
                  <p className="mt-1 text-xs text-muted-foreground">Preview it exactly as subscribers see it, or send it now.</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button onClick={previewDigest} data-testid="preview-digest" className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2 text-sm font-medium hover:bg-secondary"><FileText className="h-4 w-4" /> Preview</button>
                    <button onClick={sendDigestNow} data-testid="send-digest" className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2 text-sm font-medium hover:bg-secondary"><Mail className="h-4 w-4" /> Send now</button>
                  </div>
                </div>
                <div className="mt-5 border-t border-border pt-4">
                  <p className="text-sm font-semibold">Weekly library digest</p>
                  <p className="mt-1 text-xs text-muted-foreground">Email subscribers this week's fresh Leadership Library shelf (auto-sends Mondays).</p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <button onClick={sendLibraryDigestNow} data-testid="send-library-digest" className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2 text-sm font-medium hover:bg-secondary"><Mail className="h-4 w-4" /> Send now</button>
                  </div>
                </div>
              </div>

              <div className="rounded-2xl border border-border bg-card p-5" data-testid="card-style-tool">
                <p className="flex items-center gap-2 font-display text-base font-bold"><Sparkles className="h-4 w-4 text-[hsl(var(--primary))]" /> Signals share card</p>
                <p className="mt-1 text-xs text-muted-foreground">Pick the accent colour for the auto-generated daily share images.</p>
                <div className="mt-3 flex flex-wrap items-center gap-2">
                  {["#C6F135", "#22D3EE", "#F59E0B", "#A78BFA", "#34D399", "#F87171"].map((c) => (
                    <button key={c} onClick={() => saveCardAccent(c)} data-testid={`accent-${c.slice(1)}`} title={c}
                      className={`h-8 w-8 rounded-full border-2 transition-transform hover:scale-110 ${cardAccent.toLowerCase() === c.toLowerCase() ? "border-white" : "border-transparent"}`}
                      style={{ backgroundColor: c }} />
                  ))}
                  <input type="color" value={cardAccent} onChange={(e) => setCardAccent(e.target.value)} onBlur={(e) => saveCardAccent(e.target.value)}
                    data-testid="accent-picker" className="h-8 w-10 cursor-pointer rounded border border-border bg-transparent" />
                </div>
                <div className="mt-4 overflow-hidden rounded-xl border border-border">
                  <img src={`${API}/signals/og/${new Date().toISOString().slice(0, 10)}.png?v=${cardBust}`} alt="Share card preview"
                    data-testid="card-preview" className="w-full" />
                </div>
              </div>
            </div>
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
              <>
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-2xl border border-border bg-card p-6" data-testid="revenue-goal-card">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="flex items-center gap-2 font-display text-lg font-bold"><Target className="h-4 w-4 text-[hsl(var(--primary))]" /> Revenue Goal</h3>
                      <p className="text-sm text-muted-foreground">{analytics.month_label} target vs progress</p>
                    </div>
                    {!goalEditing && (
                      <button onClick={() => { setGoalInput(String(analytics.revenue_goal || "")); setGoalEditing(true); }}
                        data-testid="edit-revenue-goal"
                        className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-2 text-xs font-medium hover:bg-secondary">
                        <Pencil className="h-3.5 w-3.5" /> {analytics.revenue_goal ? "Edit" : "Set goal"}
                      </button>
                    )}
                  </div>
                  {goalEditing ? (
                    <div className="mt-5 flex flex-wrap items-center gap-2">
                      <div className="relative flex-1 min-w-[140px]">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground">$</span>
                        <input type="number" min="0" value={goalInput} onChange={(e) => setGoalInput(e.target.value)}
                          data-testid="revenue-goal-input" placeholder="e.g. 5000"
                          className="w-full rounded-xl border border-border bg-background py-2.5 pl-7 pr-3 text-sm outline-none focus:border-[hsl(var(--primary))]" />
                      </div>
                      <button onClick={saveGoal} disabled={savingGoal} data-testid="save-revenue-goal"
                        className="rounded-xl bg-[hsl(var(--primary))] px-4 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-60">
                        {savingGoal ? "Saving…" : "Save"}
                      </button>
                      <button onClick={() => setGoalEditing(false)} data-testid="cancel-revenue-goal"
                        className="rounded-xl border border-border px-4 py-2.5 text-sm font-medium hover:bg-secondary">Cancel</button>
                    </div>
                  ) : analytics.revenue_goal > 0 ? (
                    <div className="mt-5" data-testid="revenue-goal-progress">
                      {(() => {
                        const rev = analytics.month_revenue || 0;
                        const goal = analytics.revenue_goal;
                        const now = new Date();
                        const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
                        const expected = goal * (now.getDate() / daysInMonth);
                        const reached = rev >= goal;
                        const onTrack = rev >= expected;
                        const badge = reached
                          ? { cls: "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]", label: "Goal reached" }
                          : onTrack
                            ? { cls: "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]", label: "On track" }
                            : { cls: "bg-amber-500/15 text-amber-500", label: "Behind pace" };
                        return (
                          <div className="mb-3 flex items-center gap-2" data-testid="revenue-goal-pace">
                            <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-semibold ${badge.cls}`}>
                              {reached || onTrack ? <TrendingUp className="h-3.5 w-3.5" /> : <TrendingDown className="h-3.5 w-3.5" />}
                              {badge.label}
                            </span>
                            {!reached && (
                              <span className="text-xs text-muted-foreground">
                                pace target today ${Math.round(expected).toLocaleString()}
                              </span>
                            )}
                          </div>
                        );
                      })()}
                      <div className="flex items-end justify-between">
                        <span className="font-display text-3xl font-black text-[hsl(var(--primary))]">${(analytics.month_revenue || 0).toLocaleString()}</span>
                        <span className="text-sm text-muted-foreground">of ${analytics.revenue_goal.toLocaleString()}</span>
                      </div>
                      {(() => {
                        const pct = Math.min(100, Math.round(100 * (analytics.month_revenue || 0) / analytics.revenue_goal));
                        return (
                          <>
                            <div className="mt-3 h-3 w-full overflow-hidden rounded-full bg-secondary">
                              <div className="h-full rounded-full bg-[hsl(var(--primary))] transition-all" style={{ width: `${pct}%` }} data-testid="revenue-goal-bar" />
                            </div>
                            <p className="mt-2 text-xs text-muted-foreground">
                              <span className="font-semibold text-foreground">{pct}%</span> reached ·
                              {" "}${Math.max(0, analytics.revenue_goal - (analytics.month_revenue || 0)).toLocaleString()} to go
                            </p>
                          </>
                        );
                      })()}
                    </div>
                  ) : (
                    <p className="mt-6 text-sm text-muted-foreground" data-testid="revenue-goal-empty">
                      No goal set yet. This month's revenue: <span className="font-semibold text-foreground">${(analytics.month_revenue || 0).toLocaleString()}</span>.
                    </p>
                  )}
                </div>

                <div className="rounded-2xl border border-border bg-card p-6" data-testid="best-package-card">
                  <h3 className="flex items-center gap-2 font-display text-lg font-bold"><Package className="h-4 w-4 text-[hsl(var(--accent))]" /> Best Package</h3>
                  <p className="text-sm text-muted-foreground">Revenue by consultation package (all-time)</p>
                  {analytics.packages?.length > 0 ? (
                    <div className="mt-5 space-y-3" data-testid="best-package-list">
                      {(() => {
                        const max = analytics.packages[0].revenue || 1;
                        return analytics.packages.map((p, i) => (
                          <div key={p.package} data-testid={`package-row-${i}`}>
                            <div className="flex items-center justify-between text-sm">
                              <span className="inline-flex items-center gap-2 font-medium">
                                {i === 0 && <Star className="h-3.5 w-3.5 text-[hsl(var(--primary))]" />}{p.package}
                              </span>
                              <span className="font-display font-black text-[hsl(var(--accent))]">${p.revenue.toLocaleString()}</span>
                            </div>
                            <div className="mt-1.5 h-2.5 w-full overflow-hidden rounded-full bg-secondary">
                              <div className="h-full rounded-full bg-[hsl(var(--accent))]" style={{ width: `${Math.round(100 * p.revenue / max)}%` }} />
                            </div>
                          </div>
                        ));
                      })()}
                    </div>
                  ) : (
                    <p className="mt-6 text-sm text-muted-foreground" data-testid="best-package-empty">No paid consultations yet — package revenue will appear here.</p>
                  )}
                </div>
              </div>

              {loginAttempts && (
                <div className="mt-6 rounded-2xl border border-border bg-card p-6" data-testid="login-attempts-card">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="flex items-center gap-2 font-display text-lg font-bold"><ShieldAlert className="h-4 w-4 text-amber-500" /> Login Security</h3>
                      <p className="text-sm text-muted-foreground">Recent blocked / failed sign-in attempts ({loginAttempts.max_attempts} fails = {loginAttempts.lockout_minutes}-min lockout)</p>
                    </div>
                    {loginAttempts.locked_now > 0 ? (
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-red-500/15 px-3 py-1.5 text-xs font-semibold text-red-500" data-testid="locked-now-badge">
                        <AlertTriangle className="h-3.5 w-3.5" /> {loginAttempts.locked_now} locked now
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))]/15 px-3 py-1.5 text-xs font-semibold text-[hsl(var(--primary))]">
                        <ShieldAlert className="h-3.5 w-3.5" /> No active lockouts
                      </span>
                    )}
                  </div>
                  {security && security.trend && security.trend.some((d) => d.total > 0) && (
                    <div className="mt-5" data-testid="threat-trend">
                      <h4 className="text-sm font-bold">Blocked attacks — last 14 days</h4>
                      <div className="mt-3 h-40 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                          <BarChart data={security.trend} margin={{ top: 4, right: 8, left: -22, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                            <XAxis dataKey="day" tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} interval={1} />
                            <YAxis allowDecimals={false} tick={{ fontSize: 10, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                            <Tooltip contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, fontSize: 12 }} cursor={{ fill: "hsl(var(--secondary))", opacity: 0.4 }} />
                            <Bar dataKey="high" stackId="t" name="Critical" fill="#ef4444" />
                            <Bar dataKey="medium" stackId="t" name="Lockouts" fill="#f59e0b" radius={[3, 3, 0, 0]} />
                          </BarChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}
                  {security && security.banned.filter((b) => b.active).length > 0 && (
                    <div className="mt-5" data-testid="blocked-ips">
                      <h4 className="flex items-center gap-2 text-sm font-bold text-red-500"><AlertTriangle className="h-4 w-4" /> Auto-blocked IPs — attack stopped</h4>
                      <div className="mt-3 space-y-2">
                        {security.banned.filter((b) => b.active).map((b, i) => (
                          <div key={b.ip} className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-3" data-testid={`blocked-ip-${i}`}>
                            <div>
                              <span className="font-mono text-sm font-semibold">{b.ip}</span>
                              <span className="ml-2 text-xs text-muted-foreground">{b.reason}{b.detail ? ` · ${b.detail}` : ""}</span>
                            </div>
                            <button onClick={() => unbanIp(b.ip)} data-testid={`unban-ip-${i}`}
                              className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary">
                              <Unlock className="h-3.5 w-3.5" /> Unblock
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {security && security.alerts.length > 0 && (
                    <div className="mt-5" data-testid="security-alerts">
                      <h4 className="text-sm font-bold">Recent security events</h4>
                      <div className="mt-3 space-y-1.5">
                        {security.alerts.slice(0, 6).map((a) => (
                          <div key={a.id} className="flex items-center gap-3 text-xs" data-testid={`security-alert-${a.id}`}>
                            <span className={`inline-block h-2 w-2 rounded-full ${a.severity === "high" ? "bg-red-500" : a.severity === "medium" ? "bg-amber-500" : "bg-[hsl(var(--primary))]"}`} />
                            <span className="font-medium">{a.reason}</span>
                            <span className="font-mono text-muted-foreground">{a.ip}</span>
                            <span className="ml-auto text-muted-foreground">{a.created_at ? new Date(a.created_at).toLocaleString() : ""}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  {security && security.offenders && security.offenders.length > 0 && (
                    <div className="mt-5" data-testid="top-offenders">
                      <h4 className="text-sm font-bold">Top offenders — most persistent probes</h4>
                      {security.blocked_countries && security.blocked_countries.length > 0 && (
                        <div className="mt-2 flex flex-wrap items-center gap-2" data-testid="blocked-countries">
                          <span className="text-xs font-semibold text-red-500">Blocked countries:</span>
                          {security.blocked_countries.map((cc) => (
                            <span key={cc} className="inline-flex items-center gap-1.5 rounded-full bg-red-500/15 px-2.5 py-1 text-xs font-semibold text-red-500" data-testid={`blocked-country-${cc}`}>
                              {cc}
                              <button onClick={() => unblockCountry(cc)} data-testid={`unblock-country-${cc}`} className="hover:text-foreground" aria-label={`Unblock ${cc}`}>×</button>
                            </span>
                          ))}
                        </div>
                      )}
                      {security.countries && security.countries.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-2" data-testid="offender-countries">
                          {security.countries.map((c) => (
                            <span key={c.country} className="inline-flex items-center gap-1.5 rounded-full bg-secondary px-2.5 py-1 text-xs">
                              {c.country} <span className="font-semibold text-foreground">{c.count}</span>
                            </span>
                          ))}
                        </div>
                      )}
                      <div className="mt-3 overflow-x-auto">
                        <table className="w-full text-left text-sm" data-testid="offenders-table">
                          <thead>
                            <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                              <th className="pb-2 pr-4 font-semibold">IP</th>
                              <th className="pb-2 pr-4 font-semibold">Country</th>
                              <th className="pb-2 pr-4 font-semibold">Network</th>
                              <th className="pb-2 pr-4 font-semibold">Events</th>
                              <th className="pb-2 font-semibold text-right">Action</th>
                            </tr>
                          </thead>
                          <tbody>
                            {security.offenders.map((o, i) => (
                              <tr key={o.ip} className="border-b border-border/50" data-testid={`offender-row-${i}`}>
                                <td className="py-2.5 pr-4 font-mono text-xs">{o.ip}</td>
                                <td className="py-2.5 pr-4">{o.country}</td>
                                <td className="py-2.5 pr-4 font-mono text-xs text-muted-foreground">{o.subnet}</td>
                                <td className="py-2.5 pr-4"><span className="font-semibold text-red-500">{o.count}</span></td>
                                <td className="py-2.5">
                                  <div className="flex items-center justify-end gap-2">
                                    {o.banned ? (
                                      <span className="rounded-full bg-red-500/15 px-2.5 py-1 text-xs font-semibold text-red-500">Blocked</span>
                                    ) : (
                                      <button onClick={() => banIp(o.ip)} data-testid={`block-ip-${i}`}
                                        className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1.5 text-xs font-medium hover:bg-secondary">Block IP</button>
                                    )}
                                    <button onClick={() => banRange(o.subnet)} data-testid={`block-range-${i}`}
                                      className="inline-flex items-center gap-1 rounded-full border border-red-500/40 px-2.5 py-1.5 text-xs font-medium text-red-500 hover:bg-red-500/10">Block {o.subnet.split("/")[1] ? "/" + o.subnet.split("/")[1] : "range"}</button>
                                    {o.cc && (
                                      <button onClick={() => blockCountry(o.cc, o.country)} data-testid={`block-country-${i}`}
                                        className="inline-flex items-center gap-1 rounded-full border border-red-500/40 px-2.5 py-1.5 text-xs font-medium text-red-500 hover:bg-red-500/10">Block {o.cc}</button>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>
                  )}
                  {loginAttempts.attempts.length > 0 ? (
                    <div className="mt-4 overflow-x-auto">
                      <table className="w-full text-left text-sm" data-testid="login-attempts-table">
                        <thead>
                          <tr className="border-b border-border text-xs uppercase tracking-wider text-muted-foreground">
                            <th className="pb-2 pr-4 font-semibold">Email</th>
                            <th className="pb-2 pr-4 font-semibold">IP</th>
                            <th className="pb-2 pr-4 font-semibold">Fails</th>
                            <th className="pb-2 pr-4 font-semibold">Last attempt</th>
                            <th className="pb-2 pr-4 font-semibold">Status</th>
                            <th className="pb-2 font-semibold text-right">Action</th>
                          </tr>
                        </thead>
                        <tbody>
                          {loginAttempts.attempts.map((a, i) => (
                            <tr key={i} className="border-b border-border/50" data-testid={`login-attempt-row-${i}`}>
                              <td className="py-2.5 pr-4 font-medium">{a.email || "—"}</td>
                              <td className="py-2.5 pr-4 font-mono text-xs text-muted-foreground">{a.ip}</td>
                              <td className="py-2.5 pr-4">{a.total_fails}</td>
                              <td className="py-2.5 pr-4 text-xs text-muted-foreground">{a.updated_at ? new Date(a.updated_at).toLocaleString() : "—"}</td>
                              <td className="py-2.5">
                                {a.locked ? (
                                  <span className="inline-flex items-center gap-1 rounded-full bg-red-500/15 px-2.5 py-1 text-xs font-semibold text-red-500">Locked</span>
                                ) : (
                                  <span className="inline-flex items-center gap-1 rounded-full bg-secondary px-2.5 py-1 text-xs font-medium text-muted-foreground">Cleared</span>
                                )}
                              </td>
                              <td className="py-2.5 text-right">
                                <button onClick={() => unlockLogin(a.ip, a.email)} data-testid={`unlock-login-${i}`}
                                  className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5 text-xs font-medium hover:bg-secondary">
                                  <Unlock className="h-3.5 w-3.5" /> {a.locked ? "Unlock" : "Clear"}
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="mt-5 text-sm text-muted-foreground" data-testid="login-attempts-empty">No failed sign-in attempts recorded — all quiet.</p>
                  )}
                </div>
              )}

              {vpnGuard && (
                <div className="mt-6 rounded-2xl border border-border bg-card p-6" data-testid="vpn-guard-card">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <h3 className="flex items-center gap-2 font-display text-lg font-bold"><ShieldAlert className="h-4 w-4 text-[hsl(var(--primary))]" /> VPN / Proxy Guard</h3>
                      <p className="text-sm text-muted-foreground">Block browsing &amp; login from VPNs/proxies unless allowlisted or verified by access code{!vpnGuard.provider_configured && " · detection key not set"}</p>
                    </div>
                    <button onClick={toggleVpnGuard} data-testid="vpn-guard-toggle"
                      className={`relative h-7 w-12 rounded-full transition-colors ${vpnGuard.enabled ? "bg-[hsl(var(--primary))]" : "bg-secondary"}`}>
                      <span className={`absolute top-1 h-5 w-5 rounded-full bg-white transition-transform ${vpnGuard.enabled ? "translate-x-6" : "translate-x-1"}`} />
                    </button>
                  </div>
                  <span className={`mt-2 inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${vpnGuard.enabled ? "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]" : "bg-secondary text-muted-foreground"}`} data-testid="vpn-guard-state">
                    {vpnGuard.enabled ? "Active — VPN visitors are blocked" : "Off — no VPN blocking"}
                  </span>

                  <div className="mt-5 grid gap-6 lg:grid-cols-2">
                    <div>
                      <h4 className="text-sm font-bold">Trusted IP allowlist</h4>
                      <p className="text-xs text-muted-foreground">One IP per line — these always get through.</p>
                      <textarea value={allowlistText} onChange={(e) => setAllowlistText(e.target.value)}
                        data-testid="vpn-allowlist-input" rows={4} placeholder="203.0.113.5&#10;198.51.100.10"
                        className="mt-2 w-full rounded-xl border border-border bg-background px-3 py-2 text-sm font-mono outline-none focus:border-[hsl(var(--primary))]" />
                      <button onClick={saveVpnAllowlist} data-testid="vpn-allowlist-save"
                        className="mt-2 rounded-full bg-[hsl(var(--accent))] px-4 py-2 text-xs font-semibold text-[hsl(var(--accent-foreground))]">Save allowlist</button>
                    </div>
                    <div>
                      <h4 className="text-sm font-bold">Trusted access codes (TOTP)</h4>
                      <p className="text-xs text-muted-foreground">Provision a rotating 6-digit code for a trusted user to bypass the VPN block.</p>
                      <div className="mt-2 flex gap-2">
                        <input value={tokenLabel} onChange={(e) => setTokenLabel(e.target.value)}
                          data-testid="vpn-token-label" placeholder="e.g. Sudarshan's phone"
                          className="flex-1 rounded-xl border border-border bg-background px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]" />
                        <button onClick={addVpnToken} data-testid="vpn-token-add"
                          className="rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-xs font-semibold text-[hsl(var(--primary-foreground))]">Create</button>
                      </div>
                      <div className="mt-3 space-y-2" data-testid="vpn-token-list">
                        {(vpnGuard.tokens || []).map((t) => (
                          <div key={t.id} className="flex items-center justify-between rounded-lg border border-border px-3 py-2 text-sm">
                            <span>{t.label}</span>
                            <button onClick={() => delVpnToken(t.id)} data-testid={`vpn-token-del-${t.id}`}
                              className="text-xs text-red-500 hover:underline">Remove</button>
                          </div>
                        ))}
                        {(vpnGuard.tokens || []).length === 0 && <p className="text-xs text-muted-foreground">No trusted codes yet.</p>}
                      </div>
                    </div>
                  </div>

                  {provisioned && (
                    <div className="mt-5 rounded-xl border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/5 p-4" data-testid="vpn-token-qr">
                      <p className="text-sm font-semibold">Scan this in Google Authenticator / Authy — shown once</p>
                      <div className="mt-3 flex flex-wrap items-center gap-4">
                        <img src={provisioned.qr} alt="TOTP QR" className="h-40 w-40 rounded-lg bg-white p-2" />
                        <div className="text-xs">
                          <p className="text-muted-foreground">Manual key:</p>
                          <code className="break-all font-mono text-foreground">{provisioned.secret}</code>
                        </div>
                      </div>
                      <button onClick={() => setProvisioned(null)} className="mt-3 text-xs text-muted-foreground hover:text-foreground">Done — hide</button>
                    </div>
                  )}
                </div>
              )}

              {auditLog.length > 0 && (
                <div className="mt-6 rounded-2xl border border-border bg-card p-6" data-testid="audit-log-card">
                  <h3 className="flex items-center gap-2 font-display text-lg font-bold"><FileText className="h-4 w-4 text-muted-foreground" /> Admin audit trail</h3>
                  <p className="text-sm text-muted-foreground">Every sensitive admin action, logged.</p>
                  <div className="mt-3 space-y-1.5" data-testid="audit-log-list">
                    {auditLog.slice(0, 12).map((l) => (
                      <div key={l.id} className="flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs">
                        <span className="font-mono text-muted-foreground">{l.at ? new Date(l.at).toLocaleString() : ""}</span>
                        <span className="font-semibold">{l.actor}</span>
                        <span className="rounded-full bg-secondary px-2 py-0.5 font-medium">{l.action}</span>
                        {l.target && <span className="font-mono text-muted-foreground">{l.target}{l.meta ? ` (${l.meta})` : ""}</span>}
                        <span className="ml-auto font-mono text-muted-foreground">{l.ip}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <div className="mt-6 rounded-2xl border border-border bg-card p-6" data-testid="lead-source-chart">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h3 className="font-display text-lg font-bold">{chartMetric === "revenue" ? "Revenue by source" : "Lead volume by source"}</h3>
                    <p className="text-sm text-muted-foreground">{chartMetric === "revenue" ? "Paid consultation revenue over time" : "Where your enquiries come from"}</p>
                  </div>
                  <div className="flex flex-wrap items-center gap-2">
                  <div className="flex gap-1 rounded-full border border-border p-1" data-testid="chart-metric-toggle">
                    {[["volume", "Leads"], ["revenue", "Revenue"]].map(([v, l]) => (
                      <button key={v} onClick={() => setChartMetric(v)} data-testid={`metric-${v}`}
                        className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${chartMetric === v ? "bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]" : "text-muted-foreground hover:bg-secondary"}`}>{l}</button>
                    ))}
                  </div>
                  <div className="flex gap-1 rounded-full border border-border p-1" data-testid="chart-period-toggle">
                    {[["8w", "8 weeks"], ["3m", "3 months"], ["12m", "12 months"]].map(([v, l]) => (
                      <button key={v} onClick={() => setChartPeriod(v)} data-testid={`period-${v}`}
                        className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${chartPeriod === v ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "text-muted-foreground hover:bg-secondary"}`}>{l}</button>
                    ))}
                  </div>
                  <button onClick={exportAnalytics} data-testid="export-analytics"
                    className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-2 text-xs font-medium hover:bg-secondary">
                    <FileText className="h-3.5 w-3.5" /> Export CSV
                  </button>
                  <button onClick={emailReport} data-testid="email-report"
                    className="inline-flex items-center gap-1.5 rounded-full border border-border px-3 py-2 text-xs font-medium hover:bg-secondary">
                    <Mail className="h-3.5 w-3.5" /> Email report
                  </button>
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
                    <BarChart data={chartMetric === "revenue" ? analytics.revenue : analytics.weeks} margin={{ top: 4, right: 8, left: -18, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                      <XAxis dataKey="week" tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                      <YAxis allowDecimals={false} tickFormatter={(v) => chartMetric === "revenue" ? `$${v}` : v} tick={{ fontSize: 11, fill: "hsl(var(--muted-foreground))" }} tickLine={false} axisLine={false} />
                      <Tooltip formatter={(v, n) => [chartMetric === "revenue" ? `$${Number(v).toLocaleString()}` : v, n]} contentStyle={{ background: "hsl(var(--card))", border: "1px solid hsl(var(--border))", borderRadius: 12, fontSize: 12 }} cursor={{ fill: "hsl(var(--secondary))", opacity: 0.4 }} />
                      {analytics.sources.map((s) => (
                        <Bar key={s} dataKey={s} stackId="a" name={SOURCE_LABELS[s]} fill={SOURCE_COLORS[s]} radius={s === "other" ? [4, 4, 0, 0] : 0} />
                      ))}
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                {analytics.conversion && (
                  <div className="mt-6 border-t border-border pt-5" data-testid="conversion-view">
                    <h4 className="font-display text-sm font-bold">Conversion & revenue by source</h4>
                    <p className="text-xs text-muted-foreground">Paid consultations and revenue per channel (all-time) — ranked by value</p>
                    {analytics.ranked?.length > 0 && analytics.ranked[0].revenue > 0 && (
                      <p className="mt-3 inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))]/10 px-3 py-1.5 text-xs font-semibold text-[hsl(var(--primary))]" data-testid="top-channel">
                        <Star className="h-3.5 w-3.5" /> Most valuable channel: {SOURCE_LABELS[analytics.ranked[0].source]} · ${analytics.ranked[0].revenue.toLocaleString()}
                      </p>
                    )}
                    <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                      {(analytics.ranked || []).map((c) => (
                        <div key={c.source} className="rounded-xl border border-border p-4" data-testid={`conversion-${c.source}`}>
                          <div className="flex items-center justify-between">
                            <span className="inline-flex items-center gap-1.5 text-sm font-medium">
                              <span className="h-2.5 w-2.5 rounded-full" style={{ background: SOURCE_COLORS[c.source] }} />{SOURCE_LABELS[c.source]}
                            </span>
                            <span className="font-display text-lg font-black text-[hsl(var(--primary))]">${(c.revenue || 0).toLocaleString()}</span>
                          </div>
                          <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-secondary">
                            <div className="h-full rounded-full" style={{ width: `${c.rate}%`, background: SOURCE_COLORS[c.source] }} />
                          </div>
                          <p className="mt-2 text-xs text-muted-foreground">{c.rate}% converted · {c.paid} paid of {c.total} lead{c.total > 1 ? "s" : ""}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
              </>
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
                <h3 className="font-display text-lg font-bold">Article Studio</h3>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">Describe a topic — Karweer's writing engine drafts a full article for you to review and publish.</p>
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
        {tab === "consent" && (
          <div className="mt-8 space-y-4" data-testid="admin-consent">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="flex items-center gap-2 font-display text-xl font-bold"><ClipboardCheck className="h-5 w-5 text-[hsl(var(--primary))]" /> Consent Log</h2>
                <p className="text-sm text-muted-foreground">
                  Every Terms &amp; Conditions + Privacy Policy agreement captured at sign-in / sign-up.
                  {consentLogs?.policy_version && <> Current policy version <span className="font-medium text-foreground">{consentLogs.policy_version}</span>.</>}
                </p>
              </div>
              <button onClick={exportConsent} data-testid="export-consent"
                className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-2.5 text-sm font-medium hover:bg-secondary">
                <FileText className="h-4 w-4" /> Export CSV
              </button>
            </div>
            <div className="flex flex-wrap items-end justify-between gap-4 rounded-2xl border border-border bg-card p-5" data-testid="policy-version-card">
              <div>
                <p className="flex items-center gap-2 font-display text-base font-bold"><ShieldAlert className="h-4 w-4 text-[hsl(var(--primary))]" /> Policy version control</p>
                <p className="mt-1 text-xs text-muted-foreground">
                  Bumping the version prompts every client to re-read &amp; re-agree on their next visit.
                  {policyInfo && <> Currently <span className="font-semibold text-foreground">{policyInfo.users_on_current}</span> of <span className="font-semibold text-foreground">{policyInfo.users_total}</span> users are on version <span className="font-semibold text-foreground">{policyInfo.version}</span>.</>}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <input value={newVersion} onChange={(e) => setNewVersion(e.target.value)} data-testid="policy-version-input"
                  placeholder="e.g. 2026-07-01" className="w-40 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]" />
                <button onClick={bumpPolicy} data-testid="policy-version-save"
                  className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                  Update &amp; prompt everyone
                </button>
              </div>
            </div>
            {policyInfo?.history?.length > 0 && (
              <div className="rounded-2xl border border-border bg-card p-5" data-testid="policy-history">
                <p className="text-sm font-semibold">Version history</p>
                <ul className="mt-3 space-y-2">
                  {policyInfo.history.map((h, i) => (
                    <li key={i} className="flex flex-wrap items-center justify-between gap-2 border-b border-border pb-2 text-xs text-muted-foreground last:border-0 last:pb-0">
                      <span className="font-semibold text-foreground">v{h.version}</span>
                      <span>{h.at ? new Date(h.at).toLocaleString() : ""}{h.by ? ` · ${h.by}` : ""}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
            <div className="overflow-x-auto rounded-2xl border border-border">
              <table className="w-full text-left text-sm">
                <thead className="bg-card text-muted-foreground">
                  <tr>
                    <th className="p-4">When (UTC)</th><th className="p-4">Name</th><th className="p-4">Email</th>
                    <th className="p-4">Method</th><th className="p-4">Agreed</th><th className="p-4">Version</th><th className="p-4">IP</th>
                  </tr>
                </thead>
                <tbody>
                  {(!consentLogs || consentLogs.logs.length === 0) && <tr><td colSpan="7" className="p-8 text-center text-muted-foreground">No consent records yet.</td></tr>}
                  {consentLogs?.logs.map((l) => (
                    <tr key={l.id} className="border-t border-border" data-testid={`consent-row-${l.id}`}>
                      <td className="p-4 text-muted-foreground">{l.created_at ? new Date(l.created_at).toLocaleString() : "—"}</td>
                      <td className="p-4 font-medium">{l.name || "—"}</td>
                      <td className="p-4">{l.email}</td>
                      <td className="p-4"><span className="rounded-full bg-secondary px-2.5 py-1 text-xs font-medium capitalize">{l.action}</span></td>
                      <td className="p-4"><span className="inline-flex items-center gap-1 text-xs font-semibold text-[hsl(var(--primary))]"><ClipboardCheck className="h-3.5 w-3.5" /> {l.agreed ? "Yes" : "No"}</span></td>
                      <td className="p-4 text-xs text-muted-foreground">T&amp;C {l.terms_version} · Privacy {l.privacy_version}</td>
                      <td className="p-4 text-xs text-muted-foreground">{l.ip}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {tab === "bookings" && (
          <div className="mt-8" data-testid="admin-bookings">
            {calStatus && (
              <div className="mb-4 flex flex-wrap items-center gap-3 rounded-2xl border border-border bg-card p-4" data-testid="calendar-connect-card">
                <CalendarCheck className={`h-5 w-5 ${calStatus.connected && calStatus.healthy ? "text-[hsl(var(--primary))]" : calStatus.connected ? "text-amber-500" : "text-muted-foreground"}`} />
                <div className="mr-auto">
                  <p className="text-sm font-semibold">Google Calendar sync</p>
                  <p className="text-xs text-muted-foreground">
                    {!calStatus.configured ? "Not configured on the server."
                      : calStatus.connected && !calStatus.healthy ? <span className="font-medium text-amber-500" data-testid="calendar-unhealthy">⚠ Reconnect needed — Google access expired, so syncing is paused. Reconnect to resume.</span>
                      : calStatus.connected ? <>Connected as <span className="font-medium text-foreground">{calStatus.email}</span> · confirmed sessions sync automatically</>
                      : "Connect once to auto-add every confirmed session to your calendar."}
                  </p>
                </div>
                {calStatus.configured && (calStatus.connected
                  ? (!calStatus.healthy
                    ? <button onClick={connectCalendar} data-testid="calendar-reconnect" className="inline-flex items-center gap-1.5 rounded-full bg-amber-500 px-4 py-2 text-xs font-semibold text-black"><CalendarCheck className="h-4 w-4" /> Reconnect</button>
                    : <button onClick={disconnectCalendar} data-testid="calendar-disconnect" className="inline-flex items-center gap-1.5 rounded-full border border-border px-4 py-2 text-xs font-medium hover:bg-secondary"><CalendarX className="h-4 w-4" /> Disconnect</button>)
                  : <button onClick={connectCalendar} data-testid="calendar-connect" className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-xs font-semibold text-[hsl(var(--primary-foreground))]"><CalendarCheck className="h-4 w-4" /> Connect Google Calendar</button>)}
              </div>
            )}
            {renderAgenda()}
            <div className="overflow-x-auto rounded-2xl border border-border">
              <table className="w-full text-left text-sm">
                <thead className="bg-card text-muted-foreground">
                  <tr><th className="p-4">Client</th><th className="p-4">Package</th><th className="p-4">Requested slot</th><th className="p-4">Status</th><th className="p-4">Actions</th></tr>
                </thead>
                <tbody>
                  {bookings.length === 0 && <tr><td colSpan="5" className="p-8 text-center text-muted-foreground">No session bookings yet.</td></tr>}
                  {bookings.map((b) => {
                    const badge = b.status === "confirmed" ? "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]" : (b.status === "declined" || b.status === "cancelled") ? "bg-red-500/15 text-red-500" : "bg-amber-500/15 text-amber-500";
                    return (
                      <tr key={b.id} className="border-t border-border align-top">
                        <td className="p-4 font-medium">{b.name}<div className="text-xs text-muted-foreground">{b.email}</div><div className="text-xs text-muted-foreground">{b.phone}</div></td>
                        <td className="p-4 text-muted-foreground">{b.package}<div className="text-xs">{b.minutes} min · ${b.amount}</div></td>
                        <td className="p-4 text-muted-foreground">
                          <div className="font-medium text-foreground">{b.slot_date}</div>
                          <div className="text-xs">{b.slot_time} IST</div>
                          {b.meeting_link && <a href={b.meeting_link} target="_blank" rel="noreferrer" data-testid={`booking-link-${b.id}`} className="mt-1 block text-xs font-medium text-[hsl(var(--primary))] underline truncate max-w-[180px]">🔗 Meeting link</a>}
                          {b.area && <div className="mt-1 text-xs">{b.area}</div>}
                        </td>
                        <td className="p-4"><span className={`rounded-full px-2.5 py-1 text-[11px] font-semibold capitalize ${badge}`} data-testid={`booking-status-${b.id}`}>{(b.status || "").replace(/_/g, " ")}</span>
                          {b.reschedule_requested && b.status !== "cancelled" && <span data-testid={`reschedule-flag-${b.id}`} className="mt-1.5 block rounded bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-amber-500" title={b.reschedule_note || ""}>↻ Reschedule requested</span>}
                        </td>
                        <td className="p-4">
                          {reschedule?.id === b.id ? (
                            <div className="flex flex-col gap-2" data-testid={`reschedule-form-${b.id}`}>
                              <input type="date" value={reschedule.date} onChange={(e) => setReschedule({ ...reschedule, date: e.target.value })} data-testid={`reschedule-date-${b.id}`} className="rounded-lg border border-border bg-background px-2 py-1 text-xs" />
                              <select value={reschedule.time} onChange={(e) => setReschedule({ ...reschedule, time: e.target.value })} data-testid={`reschedule-time-${b.id}`} className="rounded-lg border border-border bg-background px-2 py-1 text-xs">
                                {(availWeek?.slot_times || []).map((t) => <option key={t} value={t}>{t}</option>)}
                              </select>
                              <input value={reschedule.link} onChange={(e) => setReschedule({ ...reschedule, link: e.target.value })} placeholder="Meeting link (optional)" data-testid={`reschedule-link-${b.id}`} className="w-44 rounded-lg border border-border bg-background px-2 py-1 text-xs" />
                              <div className="flex gap-2">
                                <button onClick={() => bookingAction(b.id, "reschedule", { date: reschedule.date, time: reschedule.time, meeting_link: reschedule.link })} data-testid={`reschedule-save-${b.id}`} className="rounded-full bg-[hsl(var(--primary))] px-3 py-1 text-xs font-semibold text-[hsl(var(--primary-foreground))]">Save</button>
                                <button onClick={() => setReschedule(null)} className="rounded-full border border-border px-3 py-1 text-xs">Cancel</button>
                              </div>
                            </div>
                          ) : confirming?.id === b.id ? (
                            <div className="flex flex-col gap-2" data-testid={`confirm-form-${b.id}`}>
                              <input value={confirming.link} onChange={(e) => setConfirming({ ...confirming, link: e.target.value })} placeholder="Meeting/video link (optional)" data-testid={`confirm-link-${b.id}`} className="w-48 rounded-lg border border-border bg-background px-2 py-1 text-xs" />
                              <div className="flex gap-2">
                                <button onClick={() => bookingAction(b.id, "confirm", { meeting_link: confirming.link })} data-testid={`confirm-save-${b.id}`} className="rounded-full bg-[hsl(var(--primary))] px-3 py-1 text-xs font-semibold text-[hsl(var(--primary-foreground))]">Confirm session</button>
                                <button onClick={() => setConfirming(null)} className="rounded-full border border-border px-3 py-1 text-xs">Cancel</button>
                              </div>
                            </div>
                          ) : (
                            <div className="flex flex-wrap gap-2">
                              {b.status !== "confirmed" && <button onClick={() => setConfirming({ id: b.id, link: b.meeting_link || "" })} data-testid={`confirm-booking-${b.id}`} className="rounded-full bg-[hsl(var(--primary))] px-3 py-1 text-xs font-semibold text-[hsl(var(--primary-foreground))]">Confirm</button>}
                              <button onClick={() => setReschedule({ id: b.id, date: b.slot_date, time: b.slot_time, link: b.meeting_link || "" })} data-testid={`reschedule-booking-${b.id}`} className="rounded-full border border-border px-3 py-1 text-xs font-medium hover:bg-secondary">Reschedule</button>
                              {b.status !== "declined" && <button onClick={() => bookingAction(b.id, "decline", { reason: "" })} data-testid={`decline-booking-${b.id}`} className="rounded-full border border-border px-3 py-1 text-xs font-medium text-red-500 hover:bg-secondary">Decline</button>}
                            </div>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {tab === "availability" && availWeek && (
          <div className="mt-8 space-y-5" data-testid="admin-availability">
            <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-border bg-card p-4">
              <button onClick={() => shiftWeek(-7)} data-testid="avail-prev-week" className="rounded-full border border-border px-3 py-1.5 text-sm hover:bg-secondary">← Prev</button>
              <div className="font-display text-lg font-bold">Week of {availWeek.week_start}</div>
              <button onClick={() => shiftWeek(7)} data-testid="avail-next-week" className="rounded-full border border-border px-3 py-1.5 text-sm hover:bg-secondary">Next →</button>
              {availWeek.is_published
                ? <span className="rounded-full bg-[hsl(var(--primary))]/15 px-3 py-1 text-xs font-semibold text-[hsl(var(--primary))]" data-testid="avail-published-badge">Published to visitors</span>
                : <button onClick={publishWeek} data-testid="publish-week" className="rounded-full bg-[hsl(var(--accent))] px-4 py-1.5 text-sm font-semibold text-[hsl(var(--accent-foreground))]">Publish this week</button>}
              <span className="ml-auto text-xs text-muted-foreground">Mon–Fri · 09:30–19:00 · 30-min slots. Click a slot to block/open it.</span>
            </div>
            <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-border bg-card p-4" data-testid="buffer-control">
              <span className="text-sm font-semibold">Buffer between sessions</span>
              <select value={bufferInput} onChange={(e) => { setBufferInput(e.target.value); saveBuffer(e.target.value); }} data-testid="buffer-select" className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm">
                {[0, 15, 30, 45, 60].map((m) => <option key={m} value={m}>{m === 0 ? "No buffer" : `${m} min`}</option>)}
              </select>
              <span className="text-xs text-muted-foreground">Automatically keeps a gap after each booked session so slots never sit back-to-back.</span>
            </div>
            <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-border bg-card p-4" data-testid="reminder-control">
              <span className="text-sm font-semibold">Client reminders</span>
              <select value={reminderSel} onChange={(e) => { setReminderSel(e.target.value); saveReminders(e.target.value); }} data-testid="reminder-select" className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm">
                <option value="24">1 day before</option>
                <option value="2">2 hours before</option>
                <option value="both">Both (1 day + 2 hours)</option>
                <option value="off">Off</option>
              </select>
              <span className="text-xs text-muted-foreground">Confirmed clients get an automatic email reminder at the times you choose.</span>
            </div>
            <div className="flex flex-wrap items-center gap-2 rounded-2xl border border-border bg-card p-4" data-testid="cancel-window-control">
              <span className="text-sm font-semibold">No online cancellations within</span>
              <select value={cancelWin} onChange={(e) => { setCancelWin(e.target.value); saveCancelWindow(e.target.value); }} data-testid="cancel-window-select" className="rounded-lg border border-border bg-background px-3 py-1.5 text-sm">
                {[0, 12, 24, 48].map((h) => <option key={h} value={h}>{h === 0 ? "Always allowed" : `${h} hours`}</option>)}
              </select>
              <span className="text-xs text-muted-foreground">Within this window clients must contact you directly instead of cancelling online.</span>
            </div>
            <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
              <span className="inline-flex items-center gap-1.5"><span className="h-3 w-3 rounded border border-border bg-background" /> Available</span>
              <span className="inline-flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-muted-foreground/30" /> Blocked</span>
              <span className="inline-flex items-center gap-1.5"><span className="h-3 w-3 rounded bg-[hsl(var(--primary))]" /> Booked</span>
            </div>
            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {availWeek.days.map((d) => {
                const allBlocked = d.slots.every((s) => s.state !== "available");
                return (
                  <div key={d.date} className="rounded-2xl border border-border bg-card p-4" data-testid={`avail-day-${d.date}`}>
                    <div className="flex items-center justify-between">
                      <p className="text-sm font-semibold">{d.label}</p>
                      <button onClick={() => blockDay(d.date, !allBlocked)} data-testid={`avail-blockday-${d.date}`} className="rounded-full border border-border px-2.5 py-1 text-[11px] font-medium hover:bg-secondary">{allBlocked ? "Open day" : "Block day"}</button>
                    </div>
                    <div className="mt-3 grid grid-cols-4 gap-1.5">
                      {d.slots.map((s) => {
                        const cls = s.state === "booked" ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] cursor-not-allowed" : s.state === "blocked" ? "bg-muted-foreground/25 text-muted-foreground line-through" : "border border-border hover:bg-secondary";
                        return (
                          <button key={s.time} onClick={() => toggleSlot(d.date, s.time, s.state)} data-testid={`avail-slot-${d.date}-${s.time}`} className={`rounded-md px-1 py-1 text-[11px] ${cls}`}>{s.time}</button>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {tab === "vault" && <VaultPanel />}
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
