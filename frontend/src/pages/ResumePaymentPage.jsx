import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, CheckCircle2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import api from "@/lib/api";

function loadRazorpay() {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const s = document.createElement("script");
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.body.appendChild(s);
  });
}

const inr = (v) => "\u20b9" + Number(v || 0).toLocaleString("en-IN", { maximumFractionDigits: 2 });

export default function ResumePaymentPage() {
  const { bid } = useParams();
  const navigate = useNavigate();
  const [state, setState] = useState("loading"); // loading | ready | done | gone
  const [info, setInfo] = useState(null);

  useEffect(() => {
    api.get(`/payments/resume/${bid}`)
      .then((r) => { setInfo(r.data); setState("ready"); })
      .catch(() => setState("gone"));
  }, [bid]);

  const pay = async () => {
    const ok = await loadRazorpay();
    if (!ok) { toast.error("Couldn't load the payment window. Please retry."); return; }
    const rzp = new window.Razorpay({
      key: info.key_id, amount: info.amount, currency: info.currency,
      name: "Sudarshan Karweer", description: `${info.package} · ${info.slot_date} ${info.slot_time} IST`,
      order_id: info.order_id, prefill: info.prefill, theme: { color: "#0A0A0A" },
      handler: async (resp) => {
        try {
          await api.post("/payments/verify", {
            booking_id: bid, razorpay_order_id: resp.razorpay_order_id,
            razorpay_payment_id: resp.razorpay_payment_id, razorpay_signature: resp.razorpay_signature,
          });
          setState("done");
          toast.success("Payment received! Your slot is reserved.");
        } catch { toast.error("We couldn't verify the payment. Any deducted amount is auto-refunded."); }
      },
      modal: { ondismiss: () => toast("Payment window closed.") },
    });
    rzp.on("payment.failed", () => toast.error("Payment failed. Please try again."));
    rzp.open();
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Navbar />
      <div className="mx-auto flex min-h-[70vh] max-w-lg flex-col items-center justify-center px-6 py-24 text-center" data-testid="resume-payment">
        {state === "loading" && <Loader2 className="h-8 w-8 animate-spin text-[hsl(var(--primary))]" />}
        {state === "gone" && (
          <>
            <h1 className="font-display text-3xl font-bold">This booking is no longer pending</h1>
            <p className="mt-3 text-muted-foreground">It may already be paid, or the held slot was released. You're welcome to book a fresh slot.</p>
            <button onClick={() => navigate("/")} data-testid="resume-home" className="mt-6 rounded-full bg-[hsl(var(--primary))] px-6 py-3 font-semibold text-[hsl(var(--primary-foreground))]">Book a new slot</button>
          </>
        )}
        {state === "ready" && info && (
          <>
            <h1 className="font-display text-3xl font-bold">Complete your booking</h1>
            <p className="mt-3 text-muted-foreground">{info.package} · {info.slot_date} at {info.slot_time} IST</p>
            <p className="mt-6 font-display text-4xl font-extrabold text-[hsl(var(--primary))]">{inr(info.breakdown?.total)}</p>
            <p className="text-xs text-muted-foreground">incl. {info.breakdown?.gst_pct}% GST · paid securely via Razorpay</p>
            <button onClick={pay} data-testid="resume-pay" className="mt-6 rounded-full bg-[hsl(var(--accent))] px-8 py-3.5 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5">Pay {inr(info.breakdown?.total)} & book</button>
          </>
        )}
        {state === "done" && (
          <>
            <CheckCircle2 className="h-14 w-14 text-[hsl(var(--primary))]" />
            <h1 className="mt-4 font-display text-3xl font-bold">Payment received</h1>
            <p className="mt-3 text-muted-foreground">Your slot is reserved and pending confirmation — we'll confirm your session and send a calendar invite shortly.</p>
            <button onClick={() => navigate("/")} className="mt-6 rounded-full border border-border px-6 py-3 font-semibold hover:bg-secondary">Back to home</button>
          </>
        )}
      </div>
      <Footer />
    </div>
  );
}
