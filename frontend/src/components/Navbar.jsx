import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { Menu, X, ArrowUpRight } from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/context/AuthContext";

const links = [
  { label: "About", href: "/#about" },
  { label: "Services", href: "/#services" },
  { label: "Insights", href: "/insights" },
  { label: "Case Studies", href: "/#casestudies" },
  { label: "Market Pulse", href: "/#market" },
];

export function Logo() {
  return (
    <Link to="/" data-testid="logo" className="group flex items-center gap-2">
      <span className="font-display text-2xl font-black tracking-tight text-foreground">
        Sudarshan
        <span className="text-[hsl(var(--accent))]">.</span>
        <span className="text-[hsl(var(--primary))]">K</span>
      </span>
    </Link>
  );
}

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-border bg-background/70 backdrop-blur-xl">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4 lg:px-10">
        <Logo />
        <div className="hidden items-center gap-8 lg:flex">
          {links.map((l) => (
            <a
              key={l.label}
              href={l.href}
              data-testid={`nav-${l.label.toLowerCase().replace(" ", "-")}`}
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              {l.label}
            </a>
          ))}
        </div>
        <div className="hidden items-center gap-3 lg:flex">
          <ThemeToggle />
          {user ? (
            <>
              <Link
                to={user.role === "admin" ? "/admin" : "/dashboard"}
                data-testid="nav-dashboard"
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                {user.role === "admin" ? "Admin" : "Dashboard"}
              </Link>
              <button
                onClick={() => { logout(); navigate("/"); }}
                data-testid="nav-logout"
                className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
              >
                Logout
              </button>
            </>
          ) : (
            <Link
              to="/login"
              data-testid="nav-login"
              className="text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
            >
              Client Login
            </Link>
          )}
          <a
            href="/#consult"
            data-testid="nav-consult-cta"
            className="group inline-flex items-center gap-1 rounded-full bg-[hsl(var(--accent))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-0.5"
          >
            Book Consultation
            <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
          </a>
        </div>
        <button
          onClick={() => setOpen(!open)}
          data-testid="mobile-menu-toggle"
          className="grid h-10 w-10 place-items-center rounded-full border border-border lg:hidden"
        >
          {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </nav>
      {open && (
        <div className="border-t border-border bg-background px-6 py-4 lg:hidden" data-testid="mobile-menu">
          <div className="flex flex-col gap-4">
            {links.map((l) => (
              <a key={l.label} href={l.href} onClick={() => setOpen(false)} className="text-sm font-medium text-muted-foreground">
                {l.label}
              </a>
            ))}
            <div className="flex items-center gap-3 pt-2">
              <ThemeToggle />
              {user ? (
                <button onClick={() => { logout(); navigate("/"); setOpen(false); }} className="text-sm font-medium">Logout</button>
              ) : (
                <Link to="/login" onClick={() => setOpen(false)} className="text-sm font-medium">Client Login</Link>
              )}
            </div>
            <a href="/#consult" onClick={() => setOpen(false)} className="rounded-full bg-[hsl(var(--accent))] px-5 py-2.5 text-center text-sm font-semibold text-[hsl(var(--accent-foreground))]">
              Book Consultation
            </a>
          </div>
        </div>
      )}
    </header>
  );
}
