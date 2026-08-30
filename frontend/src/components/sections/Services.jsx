import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import { ArrowUpRight } from "lucide-react";

export default function Services({ services = [] }) {
  return (
    <section id="services" className="scroll-mt-24 border-t border-border bg-card py-24 lg:py-32" data-testid="services">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <div className="max-w-2xl">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">What I do</p>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">
            Advisory built for decisions that move capital.
          </h2>
        </div>
        <div className="mt-14 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
          {services.map((s, i) => {
            const featured = i === 0;
            return (
              <motion.div
                key={s.no}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.06 }}
                className={`group relative overflow-hidden rounded-2xl border border-border p-8 transition-transform hover:-translate-y-1 ${
                  featured ? "md:col-span-2 lg:col-span-1 lg:row-span-2 bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "bg-background"
                }`}
                data-testid={`service-${s.no}`}
              >
                {featured && (
                  <img src={s.image} alt="" className="absolute inset-0 h-full w-full object-cover opacity-20" />
                )}
                <Link to={`/services/${s.slug}`} data-testid={`service-link-${s.slug}`} aria-label={s.title} className="absolute inset-0 z-10" />
                <div className="relative pointer-events-none">
                  <p className={`font-display text-sm font-bold ${featured ? "text-[hsl(var(--accent))]" : "text-muted-foreground"}`}>{s.no}</p>
                  <h3 className="mt-4 font-display text-xl font-bold leading-snug">{s.title}</h3>
                  <p className={`mt-3 text-sm leading-relaxed ${featured ? "text-[hsl(var(--primary-foreground))]/80" : "text-muted-foreground"}`}>{s.desc}</p>
                  <div className="mt-5 flex flex-wrap gap-2">
                    {s.tags.map((t) => (
                      <span key={t} className={`rounded-full px-3 py-1 text-xs ${featured ? "bg-white/15 text-white" : "border border-border text-muted-foreground"}`}>{t}</span>
                    ))}
                  </div>
                  <span className={`mt-5 inline-flex items-center gap-1 text-sm font-semibold ${featured ? "text-white" : "text-[hsl(var(--primary))]"}`}>
                    Explore <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
                  </span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
