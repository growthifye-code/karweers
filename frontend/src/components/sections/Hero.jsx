import { motion } from "framer-motion";
import { ArrowUpRight, Sparkles } from "lucide-react";
import { SK_PHOTOS } from "@/lib/assets";

const portrait = SK_PHOTOS.heroPortrait;

export default function Hero() {
  return (
    <section className="grain relative overflow-hidden pt-32 lg:pt-40" data-testid="hero">
      <div className="pointer-events-none absolute -right-32 top-20 h-96 w-96 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[120px]" />
      <div className="pointer-events-none absolute -left-32 bottom-0 h-96 w-96 rounded-full bg-[hsl(var(--accent))] opacity-10 blur-[120px]" />
      <div className="relative mx-auto grid max-w-7xl items-center gap-12 px-6 pb-24 lg:grid-cols-[1.15fr_0.85fr] lg:px-10">
        <div>
          <motion.div
            initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }}
            className="inline-flex items-center gap-2 rounded-full border border-border px-4 py-1.5 text-xs font-medium text-muted-foreground"
          >
            <Sparkles className="h-3.5 w-3.5 text-[hsl(var(--accent))]" />
            Business Coach · Strategic Advisor · Energy Transition Leader
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.1 }}
            className="mt-6 font-display text-4xl font-black leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl"
          >
            Turning ambition into <span className="text-[hsl(var(--primary))]">bankable</span>,
            enduring <span className="text-[hsl(var(--accent))]">businesses</span>.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.2 }}
            className="mt-6 max-w-xl text-base leading-relaxed text-muted-foreground sm:text-lg"
          >
            I'm Sudarshan Karweer — a renowned business coach and strategic advisor with 23+ years and 60+ projects
            across corporates and CXOs. I help founders in renewable energy, storage and green hydrogen with strategy,
            fundraising, scaling and new business development.
          </motion.p>
          <motion.div
            initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.3 }}
            className="mt-9 flex flex-wrap items-center gap-4"
          >
            <a
              href="#consult"
              data-testid="hero-consult-cta"
              className="group inline-flex items-center gap-2 rounded-full bg-[hsl(var(--accent))] px-7 py-3.5 font-semibold text-[hsl(var(--accent-foreground))] transition-transform hover:-translate-y-1"
            >
              Book a Premium 1:1 Consultation
              <ArrowUpRight className="h-5 w-5 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
            <a
              href="#services"
              data-testid="hero-services-cta"
              className="inline-flex items-center gap-2 rounded-full border border-border px-7 py-3.5 font-semibold text-foreground transition-colors hover:bg-secondary"
            >
              Explore Services
            </a>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8, delay: 0.2 }}
          className="relative"
        >
          <div className="relative overflow-hidden rounded-2xl border border-border">
            <img src={portrait} alt="Sudarshan Karweer" className="h-[30rem] w-full object-cover" data-testid="hero-portrait" />
            <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/10 to-transparent" />
            <div className="absolute bottom-5 left-5 right-5">
              <p className="font-display text-2xl font-bold text-white">Sudarshan Karweer</p>
              <p className="text-sm text-white/80">Founder · Advisor · Coach</p>
            </div>
          </div>
          <div className="absolute -left-6 -top-6 hidden rounded-2xl border border-border bg-card p-5 shadow-xl sm:block">
            <p className="font-display text-3xl font-black text-[hsl(var(--primary))]">23+</p>
            <p className="text-xs text-muted-foreground">Years Experience</p>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
