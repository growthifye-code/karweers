import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Logo } from "@/components/Navbar";
import { useAuth, formatApiErrorDetail } from "@/context/AuthContext";
import { SK_PHOTOS } from "@/lib/assets";
import Captcha from "@/components/Captcha";

export default function Register() {
  const { register } = useAuth();
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
