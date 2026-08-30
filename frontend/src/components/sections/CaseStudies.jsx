import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

export default function CaseStudies({ cases = [] }) {
  return (
    <section id="casestudies" className="scroll-mt-24 py-24 lg:py-32" data-testid="casestudies">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Proof of Delivery</p>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Case studies — from asset monetisation to financial close.
          </h2>
        </div>
        <div className="mt-12 grid gap-6 lg:grid-cols-3">
          {cases.map((c, i) => (
            <motion.div
              key={c.slug}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.08 }}
            >
              <Link
                to={`/insights/${c.slug}`}
                data-testid={`case-${c.slug}`}
                className="group relative flex h-80 flex-col justify-end overflow-hidden rounded-2xl border border-border"
              >
                <img src={c.image} alt={c.title} className="absolute inset-0 h-full w-full object-cover transition-transform duration-500 group-hover:scale-105" />
                <div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/40 to-transparent" />
                <div className="relative p-6">
                  <span className="rounded-full bg-[hsl(var(--accent))] px-3 py-1 text-xs font-semibold text-[hsl(var(--accent-foreground))]">{c.sector}</span>
                  <h3 className="mt-3 font-display text-lg font-bold leading-snug text-white">{c.title}</h3>
                  <span className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-white">
                    View case <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                  </span>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
