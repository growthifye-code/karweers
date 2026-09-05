import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Quote } from "lucide-react";

// Social-proof carousel placed high on the page (global best-practice: proof above the fold).
export default function TestimonialsStrip({ testimonials = [] }) {
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    if (testimonials.length <= 1) return;
    const id = setInterval(() => setIdx((i) => (i + 1) % testimonials.length), 5500);
    return () => clearInterval(id);
  }, [testimonials.length]);

  if (!testimonials.length) return null;
  const t = testimonials[Math.min(idx, testimonials.length - 1)];

  return (
    <section className="grain border-b border-border bg-background py-16 lg:py-20" data-testid="testimonials-strip">
      <div className="mx-auto max-w-4xl px-6 text-center">
        <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[hsl(var(--primary))]">What leaders say</p>
        <div className="relative mt-6 min-h-[160px] sm:min-h-[150px]">
          <AnimatePresence mode="wait">
            <motion.blockquote key={idx} data-testid="testimonial-item"
              initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -18 }}
              transition={{ duration: 0.5 }}>
              <Quote className="mx-auto h-8 w-8 text-[hsl(var(--primary))]/40" />
              <p className="mx-auto mt-4 max-w-3xl font-display text-xl font-medium leading-snug text-foreground sm:text-2xl">
                &ldquo;{t.quote}&rdquo;
              </p>
              <p className="mt-5 text-sm text-muted-foreground">
                <span className="font-semibold text-foreground">{t.name}</span> · {t.role}
              </p>
            </motion.blockquote>
          </AnimatePresence>
        </div>
        {testimonials.length > 1 && (
          <div className="mt-7 flex justify-center gap-2">
            {testimonials.map((_, i) => (
              <button key={i} onClick={() => setIdx(i)} data-testid={`testimonial-dot-${i}`} aria-label={`Show testimonial ${i + 1}`}
                className={`h-2 rounded-full transition-all ${i === idx ? "w-7 bg-[hsl(var(--primary))]" : "w-2 bg-border hover:bg-muted-foreground"}`} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}
