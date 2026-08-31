import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Logo } from "@/components/Navbar";
import { useAuth, formatApiErrorDetail } from "@/context/AuthContext";
import { SK_PHOTOS } from "@/lib/assets";
import Captcha from "@/components/Captcha";

function GoogleIcon() {
  return (
    <svg className="h-5 w-5" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1Z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84A11 11 0 0 0 12 23Z" />
      <path fill="#FBBC05" d="M5.84 14.1a6.6 6.6 0 0 1 0-4.22V7.04H2.18a11 11 0 0 0 0 9.9l3.66-2.84Z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.04l3.66 2.84C6.71 7.31 9.14 5.38 12 5.38Z" />
    </svg>
  );
}

export default function Register() {
  const { register, loginWithGoogle } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ name: "", email: "", password: "" });
  const [captcha, setCaptcha] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    if (!captcha) { setError("Please complete the captcha."); return; }
    setBusy(true);
    setError("");
    try {
      await register(form.name, form.email, form.password, captcha);
      toast.success("Account created!");
      navigate("/dashboard");
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || "Registration failed");
    } finally {
      setBusy(false);
    }
  };

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const googleRegister = async () => {
    if (!captcha) { setError("Please complete the captcha before continuing with Google."); return; }
    setBusy(true);
    setError("");
    try {
      await loginWithGoogle(captcha);
    } catch (err) {
      setError(formatApiErrorDetail(err.response?.data?.detail) || "Google sign-in failed");
      setBusy(false);
    }
  };

  return (
    <div className="grid min-h-screen bg-background text-foreground lg:grid-cols-2">
      <div className="flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-sm">
          <Logo />
          <h1 className="mt-10 font-display text-3xl font-bold">Create your account</h1>
          <p className="mt-2 text-sm text-muted-foreground">Join to save insights and manage your consultations.</p>
          <form onSubmit={submit} className="mt-8 space-y-4" data-testid="register-form">
            <input value={form.name} onChange={set("name")} placeholder="Full name" data-testid="register-name" className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            <input value={form.email} onChange={set("email")} type="email" placeholder="Email" data-testid="register-email" className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            <input value={form.password} onChange={set("password")} type="password" placeholder="Password" data-testid="register-password" className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            {error && <p className="text-sm text-[hsl(var(--destructive))]" data-testid="register-error">{error}</p>}
            <Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} />
            <button type="submit" disabled={busy} data-testid="register-submit" className="w-full rounded-full bg-[hsl(var(--accent))] px-6 py-3.5 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
              {busy ? "Creating…" : "Create account"}
            </button>
          </form>

          <div className="my-6 flex items-center gap-4">
            <span className="h-px flex-1 bg-border" />
            <span className="text-xs uppercase tracking-widest text-muted-foreground">or</span>
            <span className="h-px flex-1 bg-border" />
          </div>
          <button onClick={googleRegister} type="button" disabled={busy || !captcha} data-testid="google-register-btn"
            className="flex w-full items-center justify-center gap-3 rounded-full border border-border bg-background px-6 py-3.5 text-sm font-semibold transition-colors hover:bg-secondary disabled:opacity-60 disabled:cursor-not-allowed">
            <GoogleIcon /> Continue with Google
          </button>
          <p className="mt-3 text-center text-xs text-muted-foreground">{captcha ? "Google sign-in unlocks personalised recommendations & your Learning Hub." : "Complete the captcha above to continue with Google."}</p>
          <p className="mt-6 text-sm text-muted-foreground">
            Already have an account? <Link to="/login" className="font-semibold text-[hsl(var(--primary))]">Sign in</Link>
          </p>
          <Link to="/" className="mt-3 inline-block text-sm text-muted-foreground hover:text-foreground">← Back to site</Link>
        </div>
      </div>
      <div className="relative hidden overflow-hidden lg:block">
        <img src={SK_PHOTOS.armsCrossed} alt="Sudarshan Karweer" className="h-full w-full object-cover" />
        <div className="absolute inset-0 bg-[hsl(var(--primary))]/70" />
        <div className="absolute bottom-12 left-12 right-12 text-[hsl(var(--primary-foreground))]">
          <h2 className="font-display text-4xl font-black leading-tight">23+ years. 60+ projects. One trusted advisor.</h2>
        </div>
      </div>
    </div>
  );
}
