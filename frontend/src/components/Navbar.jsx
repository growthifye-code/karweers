import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { Menu, X, ArrowUpRight, ChevronDown, Phone, Mail } from "lucide-react";
import ThemeToggle from "@/components/ThemeToggle";
import { useAuth } from "@/context/AuthContext";
import { CONTACT } from "@/lib/assets";
import { ADMIN_PATH } from "@/config";

export const SERVICE_LINKS = [
  { slug: "business-strategy", label: "Business & Growth Strategy" },
  { slug: "ma-advisory", label: "M&A Advisory" },
  { slug: "fund-raising", label: "Fund Raising & Capital" },
  { slug: "premium-consultation", label: "Premium 1:1 Consultation" },
  { slug: "business-coaching", label: "Business Coaching" },
  { slug: "re-storage-hydrogen", label: "RE, Storage & Green Hydrogen" },
  { slug: "green-climate-financing", label: "Green & Climate Financing" },
  { slug: "asset-monetisation", label: "Government Asset Monetisation" },
];

export const PROGRAM_LINKS = [
  { to: "/products", label: "Digital Downloads" },
  { to: "/cohorts", label: "Cohorts & Masterclasses" },
  { to: "/corporate", label: "Corporate & Enterprise" },
];

const PODCAST_EMBLEM = "https://static.prod-images.emergentagent.com/jobs/69d54eb7-07e1-4ffd-ad08-8725f9f9829e/images/a09b8b2f1be637508ef78c38659a1ba5388d54e23e2c4150d7b98bf1a2775ce8.jpeg";

const NAV = [
  { label: "About", to: "/about" },
  { label: "Explore", to: "/explore" },
  { label: "Insights", to: "/insights-hub" },
  { label: "Podcast", to: "/podcast" },
  { label: "Cases", to: "/case-studies" },
];

export const MORE_LINKS = [
  { label: "Leadership Lab", to: "/leadership-lab" },
  { label: "Learning", to: "/learning" },
  { label: "Archive", to: "/archive" },
  { label: "Market", to: "/market" },
  { label: "Deals", to: "/deals" },
];

export function Logo({ light = false }) {
  return (
    <Link to="/" data-testid="logo" className="group flex items-center gap-3">
      <span className={`font-logo text-[30px] font-bold leading-none tracking-[-0.02em] transition-opacity group-hover:opacity-80 ${light ? "text-white" : "text-foreground"}`}>
        S<span className="text-[hsl(var(--primary))]">K.</span>
      </span>
      <span className="hidden h-8 w-px bg-border sm:block" />
      <span className="hidden flex-col leading-none sm:flex">
        <span className={`text-sm font-semibold tracking-tight ${light ? "text-white/90" : "text-foreground/90"}`}>Sudarshan Karweer</span>
        <span className="mt-1 text-[10px] font-semibold uppercase tracking-[0.28em] text-[hsl(var(--primary))]">Business Coach · Advisor</span>
      </span>
    </Link>
  );
}

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const [svcOpen, setSvcOpen] = useState(false);
  const [progOpen, setProgOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="fixed inset-x-0 top-0 z-50">
      <div className="hidden border-b border-white/10 bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] lg:block">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-10 py-1.5 text-xs font-medium">
          <span>Strategic advisory & coaching · Renewable Energy · Storage · Green Hydrogen · Climate Finance</span>
          <div className="flex items-center gap-5">
            <a href={`tel:${CONTACT.phoneRaw}`} className="inline-flex items-center gap-1.5 hover:opacity-80"><Phone className="h-3 w-3" /> {CONTACT.phone}</a>
            <a href={`mailto:${CONTACT.email}`} className="inline-flex items-center gap-1.5 hover:opacity-80"><Mail className="h-3 w-3" /> {CONTACT.email}</a>
          </div>
        </div>
      </div>

      <nav className="border-b border-border bg-background/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3.5 lg:px-10">
          <Logo />
          <div className="hidden items-center gap-7 lg:flex">
            <div className="relative" onMouseEnter={() => setSvcOpen(true)} onMouseLeave={() => setSvcOpen(false)}>
              <Link to="/services" data-testid="nav-services" className="inline-flex items-center gap-1 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
                Services <ChevronDown className="h-3.5 w-3.5" />
              </Link>
              {svcOpen && (
                <div className="absolute left-1/2 top-full w-72 -translate-x-1/2 pt-3" data-testid="services-dropdown">
                  <div className="overflow-hidden rounded-2xl border border-border bg-card p-2 shadow-2xl">
                    {SERVICE_LINKS.map((s) => (
                      <Link key={s.slug} to={`/services/${s.slug}`} className="block rounded-xl px-4 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
                        {s.label}
                      </Link>
                    ))}
                    <Link to="/services" className="mt-1 block rounded-xl px-4 py-2.5 text-sm font-semibold text-[hsl(var(--primary))] hover:bg-secondary">All services →</Link>
                  </div>
                </div>
              )}
            </div>
            {NAV.map((l) => (
              <Link key={l.label} to={l.to} data-testid={`nav-${l.label.toLowerCase().replace(" ", "-")}`} className="inline-flex items-center gap-1.5 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
                {l.label === "Podcast" && <img src={PODCAST_EMBLEM} alt="" data-testid="nav-podcast-emblem" className="h-5 w-5 rounded-full object-cover ring-1 ring-[hsl(var(--primary))]/40" />}
                {l.label}
              </Link>
            ))}
            <div className="relative" onMouseEnter={() => setMoreOpen(true)} onMouseLeave={() => setMoreOpen(false)}>
              <button type="button" data-testid="nav-more" className="inline-flex items-center gap-1 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
                More <ChevronDown className="h-3.5 w-3.5" />
              </button>
              {moreOpen && (
                <div className="absolute left-1/2 top-full w-56 -translate-x-1/2 pt-3" data-testid="more-dropdown">
                  <div className="overflow-hidden rounded-2xl border border-border bg-card p-2 shadow-2xl">
                    {MORE_LINKS.map((s) => (
                      <Link key={s.to} to={s.to} className="block rounded-xl px-4 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
                        {s.label}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
            <div className="relative" onMouseEnter={() => setProgOpen(true)} onMouseLeave={() => setProgOpen(false)}>
              <Link to="/products" data-testid="nav-programs" className="inline-flex items-center gap-1 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground">
                Work with SK <ChevronDown className="h-3.5 w-3.5" />
              </Link>
              {progOpen && (
                <div className="absolute left-1/2 top-full w-64 -translate-x-1/2 pt-3" data-testid="programs-dropdown">
                  <div className="overflow-hidden rounded-2xl border border-border bg-card p-2 shadow-2xl">
                    {PROGRAM_LINKS.map((s) => (
                      <Link key={s.to} to={s.to} className="block rounded-xl px-4 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground">
                        {s.label}
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
          <div className="hidden items-center gap-3 lg:flex">
            <ThemeToggle />
            {user ? (
              <>
                <Link to={user.role === "admin" ? ADMIN_PATH : "/dashboard"} data-testid="nav-dashboard" className="text-sm font-medium text-muted-foreground hover:text-foreground">{user.role === "admin" ? "Admin" : "Dashboard"}</Link>
                <button onClick={() => { logout(); navigate("/"); }} data-testid="nav-logout" className="text-sm font-medium text-muted-foreground hover:text-foreground">Logout</button>
              </>
            ) : (
              <>
                <Link to="/login" data-testid="nav-login" className="text-sm font-medium text-muted-foreground hover:text-foreground">Client Login</Link>
                <Link to="/login" data-testid="nav-admin-login" className="text-sm font-medium text-muted-foreground hover:text-foreground">Admin Login</Link>
              </>
            )}
            <a href="/#consult" data-testid="nav-consult-cta" className="group inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
              Book Consultation <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
          </div>
          <button onClick={() => setOpen(!open)} data-testid="mobile-menu-toggle" className="grid h-10 w-10 place-items-center rounded-full border border-border lg:hidden">
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {open && (
          <div className="border-t border-border bg-background px-6 py-4 lg:hidden" data-testid="mobile-menu">
            <div className="flex flex-col gap-3">
              <Link to="/services" onClick={() => setOpen(false)} className="text-sm font-semibold">Services</Link>
              {SERVICE_LINKS.map((s) => (
                <Link key={s.slug} to={`/services/${s.slug}`} onClick={() => setOpen(false)} className="pl-3 text-sm text-muted-foreground">{s.label}</Link>
              ))}
              {NAV.map((l) => (<Link key={l.label} to={l.to} onClick={() => setOpen(false)} className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground">{l.label === "Podcast" && <img src={PODCAST_EMBLEM} alt="" className="h-5 w-5 rounded-full object-cover ring-1 ring-[hsl(var(--primary))]/40" />}{l.label}</Link>))}
              <p className="pt-1 text-xs font-semibold uppercase tracking-wide text-[hsl(var(--primary))]">More</p>
              {MORE_LINKS.map((s) => (
                <Link key={s.to} to={s.to} onClick={() => setOpen(false)} className="pl-3 text-sm text-muted-foreground">{s.label}</Link>
              ))}
              <p className="pt-1 text-xs font-semibold uppercase tracking-wide text-[hsl(var(--primary))]">Work with SK</p>
              {PROGRAM_LINKS.map((s) => (
                <Link key={s.to} to={s.to} onClick={() => setOpen(false)} className="pl-3 text-sm text-muted-foreground">{s.label}</Link>
              ))}
              <div className="flex items-center gap-3 pt-2">
                <ThemeToggle />
                {user ? (
                  <button onClick={() => { logout(); navigate("/"); setOpen(false); }} className="text-sm font-medium">Logout</button>
                ) : (
                  <>
                    <Link to="/login" onClick={() => setOpen(false)} className="text-sm font-medium">Client Login</Link>
                    <Link to="/login" onClick={() => setOpen(false)} data-testid="mobile-admin-login" className="text-sm font-medium">Admin Login</Link>
                  </>
                )}
              </div>
              <a href="/#consult" onClick={() => setOpen(false)} className="rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-center text-sm font-semibold text-[hsl(var(--primary-foreground))]">Book Consultation</a>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
}
