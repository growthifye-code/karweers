import { Link } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";
import { Logo } from "@/components/Navbar";
import ThemeToggle from "@/components/ThemeToggle";
import { Sparkles, Calendar, BookOpen } from "lucide-react";

export default function ClientDashboard() {
  const { user, logout } = useAuth();

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
        <p className="text-sm text-muted-foreground">Client Portal</p>
        <h1 className="mt-2 font-display text-3xl font-bold">Welcome, {user?.name} 👋</h1>
        <p className="mt-2 text-muted-foreground">Your space for insights, consultations and the Karweer AI engine.</p>

        <div className="mt-10 grid gap-6 md:grid-cols-3">
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
          <div className="rounded-2xl border border-border bg-card p-8">
            <Sparkles className="h-8 w-8 text-[hsl(var(--accent))]" />
            <h3 className="mt-4 font-display text-lg font-bold">Karweer AI</h3>
            <p className="mt-2 text-sm text-muted-foreground">Use the AI engine (bottom-right) for instant advisory intelligence.</p>
          </div>
        </div>
      </main>
    </div>
  );
}
