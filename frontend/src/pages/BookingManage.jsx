import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { toast } from "sonner";
import { CalendarClock, XCircle, CheckCircle2, RefreshCw } from "lucide-react";
import api from "@/lib/api";
import { formatApiErrorDetail } from "@/context/AuthContext";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

export default function BookingManage() {
  const [params] = useSearchParams();
  const token = params.get("token") || "";
  const [booking, setBooking] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState("");
  const [showResched, setShowResched] = useState(false);
  const [note, setNote] = useState("");

  useEffect(() => {
    if (!token) { setError("This link is invalid or has expired."); return; }
    api.get("/booking/manage", { params: { token } })
      .then((r) => setBooking(r.data))
      .catch((e) => setError(formatApiErrorDetail(e.response?.data?.detail) || "This link is invalid or has expired."));
  }, [token]);

  const cancel = async () => {
    if (!window.confirm("Cancel this session? This frees the slot for someone else.")) return;
    setBusy(true);
    try { await api.post("/booking/cancel", { token }); setDone("cancelled"); toast.success("Your session has been cancelled."); }
    catch (e) { toast.error(formatApiErrorDetail(e.response?.data?.detail) || "Could not cancel."); }
    finally { setBusy(false); }
  };

  const requestReschedule = async () => {
    setBusy(true);
    try { await api.post("/booking/reschedule-request", { token, message: note }); setDone("reschedule"); toast.success("Reschedule request sent — we'll be in touch shortly."); }
    catch (e) { toast.error(formatApiErrorDetail(e.response?.data?.detail) || "Could not send request."); }
    finally { setBusy(false); }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <div className="mx-auto max-w-xl px-6 py-24" data-testid="booking-manage">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Manage your booking</p>

        {error && <div className="mt-6 rounded-2xl border border-red-500/30 bg-red-500/5 p-6 text-sm text-red-500" data-testid="manage-error">{error}</div>}

        {!error && !booking && <p className="mt-6 text-sm text-muted-foreground">Loading your booking…</p>}

        {booking && (
          <div className="mt-6 rounded-2xl border border-border bg-card p-7">
            <h1 className="font-display text-2xl font-bold">{booking.package}</h1>
            <p className="mt-2 flex items-center gap-2 text-sm text-muted-foreground"><CalendarClock className="h-4 w-4 text-[hsl(var(--primary))]" /> {booking.slot_date} at {booking.slot_time} IST</p>
            <p className="mt-1 text-xs capitalize text-muted-foreground">Status: {(booking.status || "").replace(/_/g, " ")}</p>

            {done === "cancelled" || booking.status === "cancelled" ? (
              <div className="mt-6 flex items-start gap-3 rounded-xl border border-border bg-secondary p-4" data-testid="manage-cancelled">
                <XCircle className="mt-0.5 h-5 w-5 text-red-500" />
                <p className="text-sm">This session is cancelled. If this was a mistake, please book again from the website.</p>
              </div>
            ) : done === "reschedule" ? (
              <div className="mt-6 flex items-start gap-3 rounded-xl border border-[hsl(var(--primary))]/30 bg-[hsl(var(--primary))]/5 p-4" data-testid="manage-resched-done">
                <CheckCircle2 className="mt-0.5 h-5 w-5 text-[hsl(var(--primary))]" />
                <p className="text-sm">Thanks — your reschedule request has been sent. Sudarshan's team will reach out with new times.</p>
              </div>
            ) : (
              <div className="mt-6 space-y-3">
                {!showResched ? (
                  <div className="flex flex-wrap gap-3">
                    <button onClick={() => setShowResched(true)} disabled={busy} data-testid="request-reschedule-btn" className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-60"><RefreshCw className="h-4 w-4" /> Request a reschedule</button>
                    <button onClick={cancel} disabled={busy} data-testid="cancel-booking-btn" className="inline-flex items-center gap-2 rounded-full border border-border px-5 py-3 text-sm font-semibold text-red-500 hover:bg-secondary disabled:opacity-60"><XCircle className="h-4 w-4" /> Cancel session</button>
                  </div>
                ) : (
                  <div>
                    <textarea value={note} onChange={(e) => setNote(e.target.value)} rows={3} placeholder="Any preferred days/times? (optional)" data-testid="reschedule-note" className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
                    <div className="mt-3 flex gap-3">
                      <button onClick={requestReschedule} disabled={busy} data-testid="send-reschedule-btn" className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] disabled:opacity-60">Send request</button>
                      <button onClick={() => setShowResched(false)} className="rounded-full border border-border px-5 py-2.5 text-sm">Back</button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
