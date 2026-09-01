import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { Plus, Pencil, Trash2, X, Package, Users, FileText, Quote, Receipt, Tag, Link2 as LinkIcon } from "lucide-react";
import api from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";

const inr = (v) => "\u20b9" + Number(v || 0).toLocaleString("en-IN");
const slugify = (s) => (s || "").toLowerCase().trim().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");

const COLLECTIONS = {
  products: {
    label: "Products", icon: Package, key: "slug",
    columns: [["title", "Title"], ["price", "Price", inr], ["type", "Type"], ["active", "Active"]],
    fields: [
      { key: "title", label: "Title", type: "text" },
      { key: "slug", label: "Slug (URL id)", type: "text", auto: "title" },
      { key: "subtitle", label: "Subtitle", type: "text" },
      { key: "description", label: "Description", type: "textarea" },
      { key: "price", label: "Price (INR)", type: "number" },
      { key: "type", label: "Type", type: "select", options: ["playbook", "template", "blueprint", "guide"] },
      { key: "download_url", label: "Download URL (leave blank for Blueprint)", type: "text" },
      { key: "sort", label: "Sort order", type: "number" },
      { key: "active", label: "Active", type: "bool" },
    ],
  },
  cohorts: {
    label: "Cohorts", icon: Users, key: "slug",
    columns: [["title", "Title"], ["price", "Price", inr], ["seats_total", "Seats"], ["active", "Active"]],
    fields: [
      { key: "title", label: "Title", type: "text" },
      { key: "slug", label: "Slug (URL id)", type: "text", auto: "title" },
      { key: "subtitle", label: "Subtitle", type: "text" },
      { key: "description", label: "Description", type: "textarea" },
      { key: "price", label: "Price (INR)", type: "number" },
      { key: "seats_total", label: "Total seats", type: "number" },
      { key: "schedule", label: "Schedule", type: "text" },
      { key: "start_date", label: "Start date", type: "text" },
      { key: "sort", label: "Sort order", type: "number" },
      { key: "active", label: "Active", type: "bool" },
    ],
  },
  "case-studies": {
    label: "Case Studies", icon: FileText, key: "slug",
    columns: [["headline", "Headline"], ["sector", "Sector"], ["active", "Active"]],
    fields: [
      { key: "headline", label: "Headline", type: "text" },
      { key: "slug", label: "Slug (URL id)", type: "text", auto: "headline" },
      { key: "client", label: "Client (e.g. Confidential · Renewables IPP)", type: "text" },
      { key: "sector", label: "Sector", type: "text" },
      { key: "challenge", label: "Challenge", type: "textarea" },
      { key: "approach", label: "Approach", type: "textarea" },
      { key: "result", label: "Result", type: "textarea" },
      { key: "metrics", label: "Metrics (Label|Value, one per line)", type: "metrics" },
      { key: "quote", label: "Client quote", type: "textarea" },
      { key: "sort", label: "Sort order", type: "number" },
      { key: "active", label: "Active", type: "bool" },
    ],
  },
  testimonials: {
    label: "Testimonials", icon: Quote, key: "id",
    columns: [["name", "Name"], ["role", "Role"], ["featured", "Featured"]],
    fields: [
      { key: "quote", label: "Quote", type: "textarea" },
      { key: "name", label: "Name / Title", type: "text" },
      { key: "role", label: "Role / Sector", type: "text" },
      { key: "company", label: "Company (optional)", type: "text" },
      { key: "sort", label: "Sort order", type: "number" },
      { key: "featured", label: "Featured", type: "bool" },
    ],
  },
  "promo-codes": {
    label: "Promo Codes", icon: Tag, key: "code",
    columns: [["code", "Code"], ["type", "Type"], ["value", "Value"], ["used_count", "Used"], ["active", "Active"]],
    fields: [
      { key: "code", label: "Code (e.g. LAUNCH20)", type: "text" },
      { key: "type", label: "Discount type", type: "select", options: ["percent", "flat"] },
      { key: "value", label: "Value (% or ₹ off)", type: "number" },
      { key: "applies_to", label: "Applies to", type: "select", options: ["all", "product", "cohort"] },
      { key: "min_amount", label: "Min order amount (₹, 0 = none)", type: "number" },
      { key: "max_uses", label: "Max uses (0 = unlimited)", type: "number" },
      { key: "expires_at", label: "Expires (YYYY-MM-DD, blank = never)", type: "text" },
      { key: "active", label: "Active", type: "bool" },
    ],
  },
};

function metricsToText(m) {
  if (!Array.isArray(m)) return "";
  return m.map((x) => `${x.label}|${x.value}`).join("\n");
}
function textToMetrics(t) {
  return (t || "").split("\n").map((l) => l.trim()).filter(Boolean).map((l) => {
    const [label, value] = l.split("|");
    return { label: (label || "").trim(), value: (value || "").trim() };
  });
}

function EditModal({ collection, item, onClose, onSaved }) {
  const cfg = COLLECTIONS[collection];
  const [form, setForm] = useState(() => {
    const init = { ...(item || {}) };
    if (init.metrics) init.metrics = metricsToText(init.metrics);
    if (!item?.id) {
      if (init.active === undefined) init.active = true;
      if (collection === "testimonials" && init.featured === undefined) init.featured = true;
    }
    return init;
  });
  const [busy, setBusy] = useState(false);
  const set = (k, v) => setForm((f) => {
    const next = { ...f, [k]: v };
    const autoField = cfg.fields.find((fl) => fl.auto === k);
    if (autoField && !item?.id && !f[autoField.key]) next[autoField.key] = slugify(v);
    return next;
  });

  const save = async () => {
    const payload = { ...form };
    cfg.fields.forEach((fl) => {
      if (fl.type === "number") payload[fl.key] = Number(payload[fl.key] || 0);
      if (fl.type === "metrics") payload[fl.key] = textToMetrics(payload[fl.key]);
      if (fl.type === "bool") payload[fl.key] = !!payload[fl.key];
    });
    if (cfg.key === "slug" && !payload.slug) { toast.error("Slug is required."); return; }
    setBusy(true);
    try {
      await api.post(`/admin/cms/${collection}`, payload);
      toast.success("Saved.");
      onSaved();
      onClose();
    } catch (err) {
      toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Save failed.");
    } finally { setBusy(false); }
  };

  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-black/70 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className="max-h-[88vh] w-full max-w-lg overflow-y-auto rounded-3xl border border-border bg-card p-7 shadow-2xl" onClick={(e) => e.stopPropagation()} data-testid="cms-edit-modal">
        <div className="flex items-center justify-between">
          <h3 className="font-display text-lg font-bold">{item?.id ? "Edit" : "New"} · {cfg.label}</h3>
          <button onClick={onClose} className="grid h-9 w-9 place-items-center rounded-full border border-border hover:bg-secondary"><X className="h-4 w-4" /></button>
        </div>
        <div className="mt-5 space-y-3">
          {cfg.fields.map((fl) => (
            <div key={fl.key}>
              <label className="text-xs font-semibold text-muted-foreground">{fl.label}</label>
              {fl.type === "textarea" || fl.type === "metrics" ? (
                <textarea value={form[fl.key] || ""} onChange={(e) => set(fl.key, e.target.value)} rows={fl.type === "metrics" ? 3 : 3}
                  data-testid={`cms-field-${fl.key}`} className="mt-1 w-full rounded-xl border border-border bg-background px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]" />
              ) : fl.type === "bool" ? (
                <label className="mt-1 flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={!!form[fl.key]} onChange={(e) => set(fl.key, e.target.checked)} data-testid={`cms-field-${fl.key}`} /> Enabled
                </label>
              ) : fl.type === "select" ? (
                <select value={form[fl.key] || fl.options[0]} onChange={(e) => set(fl.key, e.target.value)} data-testid={`cms-field-${fl.key}`}
                  className="mt-1 w-full rounded-xl border border-border bg-background px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]">
                  {fl.options.map((o) => <option key={o}>{o}</option>)}
                </select>
              ) : (
                <input type={fl.type === "number" ? "number" : "text"} value={form[fl.key] ?? ""} onChange={(e) => set(fl.key, e.target.value)}
                  data-testid={`cms-field-${fl.key}`} className="mt-1 w-full rounded-xl border border-border bg-background px-3 py-2 text-sm outline-none focus:border-[hsl(var(--primary))]" />
              )}
            </div>
          ))}
        </div>
        <button onClick={save} disabled={busy} data-testid="cms-save" className="mt-6 w-full rounded-full bg-[hsl(var(--primary))] px-5 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-60">{busy ? "Saving…" : "Save"}</button>
      </div>
    </div>
  );
}

function CollectionPanel({ collection }) {
  const cfg = COLLECTIONS[collection];
  const [rows, setRows] = useState([]);
  const [editing, setEditing] = useState(null);
  const load = useCallback(() => {
    api.get(`/admin/cms/${collection}`).then((r) => setRows(r.data)).catch(() => {});
  }, [collection]);
  useEffect(() => { load(); }, [load]);

  const del = async (item) => {
    if (!window.confirm("Delete this item?")) return;
    try { await api.delete(`/admin/cms/${collection}/${item.id}`); toast.success("Deleted."); load(); }
    catch { toast.error("Delete failed."); }
  };

  return (
    <div data-testid={`cms-panel-${collection}`}>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{rows.length} item(s)</p>
        <button onClick={() => setEditing({})} data-testid={`cms-new-${collection}`} className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-sm font-semibold text-[hsl(var(--primary-foreground))]"><Plus className="h-4 w-4" /> New</button>
      </div>
      <div className="overflow-hidden rounded-2xl border border-border">
        <table className="w-full text-sm">
          <thead className="bg-secondary/50 text-left text-xs uppercase text-muted-foreground">
            <tr>{cfg.columns.map(([, label]) => <th key={label} className="px-4 py-2.5 font-semibold">{label}</th>)}<th className="px-4 py-2.5" /></tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-border" data-testid={`cms-row-${r[cfg.key]}`}>
                {cfg.columns.map(([k, , fmt]) => (
                  <td key={k} className="px-4 py-3">{typeof r[k] === "boolean" ? (r[k] ? "Yes" : "No") : fmt ? fmt(r[k]) : String(r[k] ?? "")}</td>
                ))}
                <td className="px-4 py-3 text-right">
                  <button onClick={() => setEditing(r)} data-testid={`cms-edit-${r[cfg.key]}`} className="mr-2 inline-grid h-8 w-8 place-items-center rounded-full border border-border hover:bg-secondary"><Pencil className="h-3.5 w-3.5" /></button>
                  <button onClick={() => del(r)} data-testid={`cms-delete-${r[cfg.key]}`} className="inline-grid h-8 w-8 place-items-center rounded-full border border-border text-destructive hover:bg-destructive/10"><Trash2 className="h-3.5 w-3.5" /></button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={cfg.columns.length + 1} className="px-4 py-8 text-center text-muted-foreground">No items yet.</td></tr>}
          </tbody>
        </table>
      </div>
      {editing && <EditModal collection={collection} item={editing.id ? editing : null} onClose={() => setEditing(null)} onSaved={load} />}
    </div>
  );
}

function OrdersPanel() {
  const [orders, setOrders] = useState([]);
  useEffect(() => { api.get("/admin/commerce/orders").then((r) => setOrders(r.data)).catch(() => {}); }, []);
  const revenue = orders.filter((o) => o.paid).reduce((s, o) => s + Number(o.amount || 0), 0);
  return (
    <div data-testid="cms-panel-orders">
      <div className="mb-4 grid grid-cols-3 gap-3">
        <div className="rounded-2xl border border-border bg-card p-4"><p className="text-xs text-muted-foreground">Orders</p><p className="font-display text-2xl font-bold">{orders.length}</p></div>
        <div className="rounded-2xl border border-border bg-card p-4"><p className="text-xs text-muted-foreground">Paid</p><p className="font-display text-2xl font-bold">{orders.filter((o) => o.paid).length}</p></div>
        <div className="rounded-2xl border border-border bg-card p-4"><p className="text-xs text-muted-foreground">Revenue</p><p className="font-display text-2xl font-bold text-[hsl(var(--primary))]">{inr(revenue)}</p></div>
      </div>
      <div className="overflow-hidden rounded-2xl border border-border">
        <table className="w-full text-sm">
          <thead className="bg-secondary/50 text-left text-xs uppercase text-muted-foreground">
            <tr><th className="px-4 py-2.5">Item</th><th className="px-4 py-2.5">Buyer</th><th className="px-4 py-2.5">Kind</th><th className="px-4 py-2.5">Amount</th><th className="px-4 py-2.5">Status</th></tr>
          </thead>
          <tbody>
            {orders.map((o) => (
              <tr key={o.id} className="border-t border-border" data-testid={`order-row-${o.id}`}>
                <td className="px-4 py-3">{o.ref_title}</td>
                <td className="px-4 py-3">{o.name}<div className="text-xs text-muted-foreground">{o.email}</div></td>
                <td className="px-4 py-3 capitalize">{o.kind}</td>
                <td className="px-4 py-3">{inr(o.amount)}</td>
                <td className="px-4 py-3"><span className={`rounded-full px-2.5 py-1 text-xs font-semibold ${o.paid ? "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]" : "bg-secondary text-muted-foreground"}`}>{o.paid ? "Paid" : o.status}</span></td>
              </tr>
            ))}
            {orders.length === 0 && <tr><td colSpan={5} className="px-4 py-8 text-center text-muted-foreground">No orders yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function PromoPanel() {
  const [rows, setRows] = useState([]);
  const [editing, setEditing] = useState(null);
  const load = useCallback(() => { api.get("/admin/promo/analytics").then((r) => setRows(r.data)).catch(() => {}); }, []);
  useEffect(() => { load(); }, [load]);

  const del = async (item) => {
    if (!window.confirm("Delete this code?")) return;
    try { await api.delete(`/admin/cms/promo-codes/${item.id}`); toast.success("Deleted."); load(); }
    catch { toast.error("Delete failed."); }
  };
  const copyLink = (r) => {
    const page = r.applies_to === "cohort" ? "cohorts" : "products";
    const link = `${window.location.origin}/${page}?code=${encodeURIComponent(r.code)}`;
    navigator.clipboard.writeText(link).then(() => toast.success("Campaign link copied!")).catch(() => toast.error("Copy failed."));
  };
  const totalRevenue = rows.reduce((s, r) => s + Number(r.revenue || 0), 0);
  const totalUses = rows.reduce((s, r) => s + Number(r.uses || 0), 0);

  return (
    <div data-testid="cms-panel-promo-codes">
      <div className="mb-4 grid grid-cols-3 gap-3">
        <div className="rounded-2xl border border-border bg-card p-4"><p className="text-xs text-muted-foreground">Active codes</p><p className="font-display text-2xl font-bold">{rows.filter((r) => r.active).length}</p></div>
        <div className="rounded-2xl border border-border bg-card p-4"><p className="text-xs text-muted-foreground">Redemptions</p><p className="font-display text-2xl font-bold">{totalUses}</p></div>
        <div className="rounded-2xl border border-border bg-card p-4"><p className="text-xs text-muted-foreground">Revenue via codes</p><p className="font-display text-2xl font-bold text-[hsl(var(--primary))]">{inr(totalRevenue)}</p></div>
      </div>
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm text-muted-foreground">{rows.length} code(s)</p>
        <button onClick={() => setEditing({})} data-testid="cms-new-promo-codes" className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-4 py-2 text-sm font-semibold text-[hsl(var(--primary-foreground))]"><Plus className="h-4 w-4" /> New code</button>
      </div>
      <div className="overflow-x-auto rounded-2xl border border-border">
        <table className="w-full text-sm">
          <thead className="bg-secondary/50 text-left text-xs uppercase text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5 font-semibold">Code</th><th className="px-4 py-2.5 font-semibold">Discount</th>
              <th className="px-4 py-2.5 font-semibold">Started</th><th className="px-4 py-2.5 font-semibold">Uses</th>
              <th className="px-4 py-2.5 font-semibold">Conv.</th><th className="px-4 py-2.5 font-semibold">Revenue</th>
              <th className="px-4 py-2.5 font-semibold">Active</th><th className="px-4 py-2.5" />
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-t border-border" data-testid={`cms-row-${r.code}`}>
                <td className="px-4 py-3 font-mono font-semibold">{r.code}</td>
                <td className="px-4 py-3">{r.type === "flat" ? inr(r.value) : `${r.value}%`}<span className="ml-1 text-xs text-muted-foreground">· {r.applies_to}</span></td>
                <td className="px-4 py-3">{r.started}</td>
                <td className="px-4 py-3">{r.uses}{r.max_uses > 0 && <span className="text-muted-foreground">/{r.max_uses}</span>}</td>
                <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${r.conversion_rate >= 50 ? "bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))]" : "bg-secondary text-muted-foreground"}`}>{r.conversion_rate}%</span></td>
                <td className="px-4 py-3 font-semibold">{inr(r.revenue)}</td>
                <td className="px-4 py-3">{r.active ? "Yes" : "No"}</td>
                <td className="px-4 py-3 text-right whitespace-nowrap">
                  <button onClick={() => copyLink(r)} data-testid={`promo-copy-${r.code}`} title="Copy campaign link" className="mr-2 inline-grid h-8 w-8 place-items-center rounded-full border border-border hover:bg-secondary"><LinkIcon className="h-3.5 w-3.5" /></button>
                  <button onClick={() => setEditing(r)} data-testid={`cms-edit-${r.code}`} className="mr-2 inline-grid h-8 w-8 place-items-center rounded-full border border-border hover:bg-secondary"><Pencil className="h-3.5 w-3.5" /></button>
                  <button onClick={() => del(r)} data-testid={`cms-delete-${r.code}`} className="inline-grid h-8 w-8 place-items-center rounded-full border border-border text-destructive hover:bg-destructive/10"><Trash2 className="h-3.5 w-3.5" /></button>
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={8} className="px-4 py-8 text-center text-muted-foreground">No promo codes yet. Create one to run a launch offer.</td></tr>}
          </tbody>
        </table>
      </div>
      {editing && <EditModal collection="promo-codes" item={editing.id ? editing : null} onClose={() => setEditing(null)} onSaved={load} />}
    </div>
  );
}

export default function RevenueAdmin() {
  const [sub, setSub] = useState("products");
  const tabs = [...Object.keys(COLLECTIONS), "orders"];
  return (
    <div className="mt-8" data-testid="admin-revenue">
      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map((t) => {
          const Icon = COLLECTIONS[t]?.icon || Receipt;
          return (
            <button key={t} onClick={() => setSub(t)} data-testid={`revenue-subtab-${t}`}
              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-medium capitalize transition-colors ${sub === t ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border border-border text-muted-foreground hover:bg-secondary"}`}>
              <Icon className="h-3.5 w-3.5" /> {COLLECTIONS[t]?.label || "Orders"}
            </button>
          );
        })}
      </div>
      {sub === "orders" ? <OrdersPanel /> : sub === "promo-codes" ? <PromoPanel /> : <CollectionPanel collection={sub} />}
    </div>
  );
}
