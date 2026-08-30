import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Logo } from "@/components/Navbar";
import { useAuth, formatApiErrorDetail } from "@/context/AuthContext";
import { SK_PHOTOS } from "@/lib/assets";
import Captcha from "@/components/Captcha";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [captcha, setCaptcha] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    if (!captcha) { setError("Please complete the captcha."); return; }
    setBusy(true);
    setError("");
    try {
      const user = await login(email, password, captcha);
      toast.success("Welcome back!");
      navigate(user.role === "admin" ? "/admin" : "/dashboard");
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="grid min-h-screen bg-background text-foreground lg:grid-cols-2">
      <div className="relative hidden overflow-hidden lg:block">
        <img src={SK_PHOTOS.walking} alt="Sudarshan Karweer" className="h-full w-full object-cover" />
        <div className="absolute inset-0 bg-[hsl(var(--primary))]/70" />
        <div className="absolute bottom-12 left-12 right-12 text-[hsl(var(--primary-foreground))]">
          <h2 className="font-display text-4xl font-black leading-tight">The energy transition, engineered for growth.</h2>
          <p className="mt-4 opacity-80">Client & advisor portal · Sudarshan Karweer</p>
        </div>
      </div>
      <div className="flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm">
          <Logo />
          <h1 className="mt-10 font-display text-3xl font-bold">Sign in</h1>
          <p className="mt-2 text-sm text-muted-foreground">Access your client dashboard or admin panel.</p>
          <form onSubmit={submit} className="mt-8 space-y-4" data-testid="login-form">
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="Email" data-testid="login-email" className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" placeholder="Password" data-testid="login-password" className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            {error && <p className="text-sm text-[hsl(var(--destructive))]" data-testid="login-error">{error}</p>}
            <Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} />
            <button type="submit" disabled={busy} data-testid="login-submit" className="w-full rounded-full bg-[hsl(var(--accent))] px-6 py-3.5 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
              {busy ? "Signing in…" : "Sign in"}
            </button>
          </form>
          <p className="mt-6 text-sm text-muted-foreground">
            New client? <Link to="/register" className="font-semibold text-[hsl(var(--primary))]">Create an account</Link>
          </p>
          <Link to="/" className="mt-3 inline-block text-sm text-muted-foreground hover:text-foreground">← Back to site</Link>
        </div>
      </div>
    </div>
  );
}
