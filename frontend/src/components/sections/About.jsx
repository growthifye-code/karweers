import { motion } from "framer-motion";
import { SK_PHOTOS } from "@/lib/assets";

const pillars = [
  "Renewable Energy", "Energy Storage / BESS", "Green Hydrogen", "Climate & Green Financing",
  "Fundraising", "Strategy", "New Business Development", "Scaling", "Asset Monetisation",
];

export default function About() {
  return (
    <section id="about" className="scroll-mt-24 py-24 lg:py-32" data-testid="about">
      <div className="mx-auto grid max-w-7xl gap-14 px-6 lg:grid-cols-[0.9fr_1.1fr] lg:px-10">
        <div className="relative">
          <img
            src={SK_PHOTOS.aboutWide}
            alt="Sudarshan Karweer"
            className="rounded-2xl border border-border object-cover"
            data-testid="about-image"
          />
        </div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--accent))]">Thought Leadership</p>
          <h2 className="mt-4 font-display text-3xl font-bold tracking-tight sm:text-4xl">
            An engineer's rigour. A financier's discipline. A coach's clarity.
          </h2>
          <div className="mt-6 space-y-4 text-base leading-relaxed text-muted-foreground">
            <p>
              Over 23+ years and 60+ engagements with corporates and CXOs, Sudarshan Karweer has built a reputation
              for turning complex, capital-intensive ambitions into built, bankable, operating realities — especially
              across the energy transition.
            </p>
            <p>
              His work spans renewable energy, battery storage and green hydrogen advisory; green and climate
              financing; and the monetisation of government assets — including the landmark blueprint for monetising
              MSRTC's bus depot assets. As a business coach, he helps founders convert founder-led hustle into
              system-led, scalable growth.
            </p>
          </div>
          <div className="mt-8 flex flex-wrap gap-2">
            {pillars.map((p, i) => (
              <motion.span
                key={p}
                initial={{ opacity: 0, y: 8 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.04 }}
                className="rounded-full border border-border bg-secondary px-4 py-1.5 text-xs font-medium text-secondary-foreground"
              >
                {p}
              </motion.span>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
