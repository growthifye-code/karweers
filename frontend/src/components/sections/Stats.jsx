import { motion } from "framer-motion";

export default function Stats({ stats = [] }) {
  return (
    <section className="border-y border-border bg-card" data-testid="stats">
      <div className="mx-auto grid max-w-7xl grid-cols-2 gap-px bg-border lg:grid-cols-4">
        {stats.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: i * 0.08 }}
            className="bg-card px-6 py-10 text-center lg:py-14"
          >
            <p className="font-display text-4xl font-black text-foreground lg:text-5xl">{s.value}</p>
            <p className="mt-2 text-sm text-muted-foreground">{s.label}</p>
          </motion.div>
        ))}
      </div>
      <div className="mx-auto max-w-7xl border-t border-border px-6 py-4 text-center text-xs font-medium tracking-wide text-muted-foreground" data-testid="stats-credential">
        Former <span className="text-foreground">EY (Big&nbsp;4)</span> management consultant · <span className="text-foreground">$2B+</span> debt syndicated · Advising founders &amp; CXOs across India &amp; globally
      </div>
    </section>
  );
}
