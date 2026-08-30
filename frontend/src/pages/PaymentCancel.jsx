import { Link } from "react-router-dom";
import { XCircle } from "lucide-react";
import { Logo } from "@/components/Navbar";

export default function PaymentCancel() {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <header className="border-b border-border">
        <div className="mx-auto max-w-6xl px-6 py-4"><Logo /></div>
      </header>
      <div className="mx-auto grid max-w-lg place-items-center px-6 py-32 text-center" data-testid="payment-cancel">
        <XCircle className="h-16 w-16 text-muted-foreground" />
        <h1 className="mt-6 font-display text-3xl font-bold">Payment cancelled</h1>
        <p className="mt-3 text-muted-foreground">No charge was made. You can pick a session again whenever you're ready.</p>
        <Link to="/#consult" className="mt-8 rounded-full bg-[hsl(var(--accent))] px-6 py-3 font-semibold text-[hsl(var(--accent-foreground))]">Back to consultations</Link>
      </div>
    </div>
  );
}
