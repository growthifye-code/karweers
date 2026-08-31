import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";
import EYBadge from "@/components/EYBadge";

const pillars = [
  "Strategy", "Supply Chain & Cost Optimisation", "Business Transformation", "Digital Transformation",
  "Financial Management", "Business Scaling", "M&A", "Debt Syndication", "Start-up Funding",
  "Renewable Energy", "Energy Storage", "Green Hydrogen",
];

export default function About() {
  return (
    <section id="about" className="scroll-mt-28 border-t border-border py-24 lg:py-32" data-testid="about">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="grid gap-14 lg:grid-cols-[1fr_1fr]">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">About Me</p>
              <EYBadge />
            </div>
            <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">
              An engineer's rigour. A financier's discipline. A coach's clarity.
            </h2>
            <div className="mt-6 space-y-4 text-base leading-relaxed text-muted-foreground">
              <p>Across 23+ years and 60+ engagements with leading corporates in India and globally, Sudarshan Karweer has driven strategy, supply chain &amp; cost optimisation, business &amp; digital transformation, financial management and business scaling — turning complex, capital-intensive ambitions into bankable, operating realities.</p>
              <p>A former Management Consultant with <span className="font-semibold text-foreground">EY (Ernst &amp; Young, Big 4)</span> Advisory, he has led credible debt syndication programmes exceeding <span className="font-semibold text-foreground">$2B</span> across key development authorities in Maharashtra, alongside renewable energy, storage and green-hydrogen advisory, green &amp; climate financing, and the landmark monetisation of MSRTC's bus depot assets.</p>
            </div>
            <Link to="/about" data-testid="about-more" className="mt-8 inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
              Read the full story <ArrowUpRight className="h-4 w-4" />
            </Link>
          </div>
          <div className="grid grid-cols-2 gap-4 self-start">
            {[["$2B+", "Debt Syndicated"], ["60+", "Projects Delivered"], ["EY", "Ex Big-4 Advisory"], ["CXO", "Boardroom Advisory"]].map(([v, l], i) => (
              <motion.div key={l} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.4, delay: i * 0.06 }}
                className="rounded-2xl border border-border bg-card p-6">
                <p className="font-display text-4xl font-black text-[hsl(var(--primary))]">{v}</p>
                <p className="mt-2 text-sm text-muted-foreground">{l}</p>
              </motion.div>
            ))}
          </div>
        </div>
        <div className="mt-12 flex flex-wrap gap-2">
          {pillars.map((p, i) => (
            <motion.span key={p} initial={{ opacity: 0, y: 8 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.35, delay: i * 0.03 }}
              className="rounded-full border border-border bg-secondary px-4 py-1.5 text-xs font-medium text-secondary-foreground">{p}</motion.span>
          ))}
        </div>
      </div>
    </section>
  );
}
