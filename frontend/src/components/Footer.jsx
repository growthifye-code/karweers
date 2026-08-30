import { Logo } from "@/components/Navbar";
import { Linkedin, Mail, Phone } from "lucide-react";

export default function Footer() {
  return (
    <footer className="border-t border-border bg-background" data-testid="footer">
      <div className="mx-auto max-w-7xl px-6 py-16 lg:px-10">
        <div className="grid gap-12 md:grid-cols-4">
          <div className="md:col-span-2">
            <Logo />
            <p className="mt-5 max-w-md text-sm leading-relaxed text-muted-foreground">
              Strategic advisory and business coaching for founders and CXOs across renewable energy, storage,
              green hydrogen, climate finance and government asset monetisation. 23+ years, 60+ projects.
            </p>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground">Explore</h4>
            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              <li><a href="/#about" className="transition-colors hover:text-foreground">About</a></li>
              <li><a href="/#services" className="transition-colors hover:text-foreground">Services</a></li>
              <li><a href="/insights" className="transition-colors hover:text-foreground">Insights</a></li>
              <li><a href="/#casestudies" className="transition-colors hover:text-foreground">Case Studies</a></li>
            </ul>
          </div>
          <div>
            <h4 className="text-sm font-semibold text-foreground">Connect</h4>
            <ul className="mt-4 space-y-3 text-sm text-muted-foreground">
              <li><a href="mailto:sudarshan@karweers.com" className="inline-flex items-center gap-2 transition-colors hover:text-foreground"><Mail className="h-4 w-4" /> sudarshan@karweers.com</a></li>
              <li><a href="tel:+919999999999" className="inline-flex items-center gap-2 transition-colors hover:text-foreground"><Phone className="h-4 w-4" /> +91 99999 99999</a></li>
              <li><a href="https://linkedin.com" target="_blank" rel="noreferrer" className="inline-flex items-center gap-2 transition-colors hover:text-foreground"><Linkedin className="h-4 w-4" /> LinkedIn</a></li>
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
