import api, { API } from "@/lib/api";
import { toast } from "sonner";
import { formatApiErrorDetail } from "@/context/AuthContext";

export function loadRazorpay() {
  return new Promise((resolve) => {
    if (window.Razorpay) return resolve(true);
    const s = document.createElement("script");
    s.src = "https://checkout.razorpay.com/v1/checkout.js";
    s.onload = () => resolve(true);
    s.onerror = () => resolve(false);
    document.body.appendChild(s);
  });
}

function resolveUrl(url) {
  if (!url) return "";
  if (url.startsWith("/api/")) return `${API}${url.slice(4)}`;
  return url;
}

// Starts a Razorpay checkout for a product or cohort seat.
// order payload: { kind, ref_id, name, email, phone, captcha_token, meta? }
// onDone(result) is called after a verified payment.
export async function startCommerceCheckout(order, onDone) {
  let data;
  try {
    ({ data } = await api.post("/commerce/order", order));
  } catch (err) {
    toast.error(formatApiErrorDetail(err.response?.data?.detail) || "Could not start the payment.");
    return { ok: false };
  }
  if (data.waitlist) {
    toast.message(data.message);
    return { ok: false, waitlist: true };
  }
  const ok = await loadRazorpay();
  if (!ok) {
    toast.error("Couldn't load the secure payment window. Please try again.");
    return { ok: false };
  }
  const rzp = new window.Razorpay({
    key: data.key_id,
    amount: data.amount,
    currency: data.currency,
    name: "Sudarshan Karweer",
    description: data.item,
    order_id: data.order_id,
    prefill: data.prefill,
    theme: { color: "#0A0A0A" },
    handler: async (resp) => {
      try {
        const v = await api.post("/commerce/verify", {
          our_order_id: data.our_order_id,
          razorpay_order_id: resp.razorpay_order_id,
          razorpay_payment_id: resp.razorpay_payment_id,
          razorpay_signature: resp.razorpay_signature,
        });
        toast.success(v.data.message || "Payment received!");
        onDone && onDone({ ...v.data, download_url: resolveUrl(v.data.download_url) });
      } catch (e) {
        toast.error("We couldn't verify the payment. If any amount was deducted, it is automatically refunded.");
      }
    },
    modal: { ondismiss: () => toast("Payment cancelled.") },
  });
  rzp.on("payment.failed", () => toast.error("Payment failed. Please try again or use another method."));
  rzp.open();
  return { ok: true };
}
