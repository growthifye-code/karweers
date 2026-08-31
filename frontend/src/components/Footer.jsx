import { Link } from "react-router-dom";
import { Logo, SERVICE_LINKS } from "@/components/Navbar";
import { Linkedin, Mail, Phone, MessageCircle } from "lucide-react";
import { CONTACT } from "@/lib/assets";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-background" data-testid="footer">
      <div className="mx-auto max-w-7xl px-6 py-16 lg:px-10">
        <div className="grid gap-12 md:grid-cols-6">
          <div className="md:col-span-2">
            <Logo />
            <p className="mt-5 max-w-md text-sm leading-relaxed text-muted-foreground">
              Strategic advisory and business coaching for founders and CXOs across renewable energy, storage,
              green hydrogen, climate finance and government asset monetisation. 23+ years, 60+ projects.
            </p>
            <div className="mt-5 flex gap-3">
              <a href={`mailto:${CONTACT.email}`} aria-label="Email" className="grid h-10 w-10 place-items-center rounded-full border border-border hover:bg-secondary"><Mail className="h-4 w-4" /></a>
              <a href={`tel:${CONTACT.phoneRaw}`} aria-label="Phone" className="grid h-10 w-10 place-items-center rounded-full border border-border hover:bg-secondary"><Phone className="h-4 w-4" /></a>
              <a href={`https://wa.me/${CONTACT.whatsapp}`} target="_blank" rel="noreferrer" aria-label="WhatsApp" className="grid h-10 w-10 place-items-center rounded-full border border-border hover:bg-secondary"><MessageCircle className="h-4 w-4" /></a>
              <a href="https://www.linkedin.com/in/karweers" target="_blank" rel="noreferrer" aria-label="LinkedIn" data-testid="footer-linkedin" className="grid h-10 w-10 place-items-center rounded-full border border-border hover:bg-secondary"><Linkedin className="h-4 w-4" /></a>
            </div>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground">Explore</h4>
            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              <li><Link to="/about" className="hover:text-foreground">About</Link></li>
              <li><Link to="/services" className="hover:text-foreground">Services</Link></li>
              <li><Link to="/insights" className="hover:text-foreground">Insights</Link></li>
              <li><Link to="/case-studies" className="hover:text-foreground">Case Studies</Link></li>
              <li><Link to="/market" className="hover:text-foreground">Market</Link></li>
              <li><Link to="/deals" className="hover:text-foreground">Deals</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground">Services</h4>
            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              {SERVICE_LINKS.map((s) => (<li key={s.slug}><Link to={`/services/${s.slug}`} className="hover:text-foreground">{s.label}</Link></li>))}
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground">Legal</h4>
            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              <li><Link to="/privacy" className="hover:text-foreground">Privacy & GDPR</Link></li>
              <li><Link to="/terms" className="hover:text-foreground">Terms & Conditions</Link></li>
              <li><Link to="/refund" className="hover:text-foreground">Booking & Cancellation</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground">Account</h4>
            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              <li><Link to="/login" data-testid="footer-client-login" className="hover:text-foreground">Client Login</Link></li>
              <li><Link to="/login" data-testid="footer-admin-login" className="hover:text-foreground">Admin Login</Link></li>
              <li><Link to="/register" className="hover:text-foreground">Create Account</Link></li>
            </ul>
          </div>
        </div>
        <div className="mt-12 flex flex-col items-start justify-between gap-3 border-t border-border pt-6 text-xs text-muted-foreground sm:flex-row sm:items-center">
          <p>© {new Date().getFullYear()} Sudarshan Karweer. All rights reserved.</p>
          <p>Thought leadership · Strategy · Energy transition · Coaching</p>
        </div>
      </div>
    </footer>
  );
}
