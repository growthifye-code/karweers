import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Sparkles, ArrowUpRight } from "lucide-react";
import api from "@/lib/api";

export default function FeaturedInsight() {
  const [f, setF] = useState(null);
  useEffect(() => {
    api.get("/service-insights-featured").then((r) => setF(r.data && r.data.slug ? r.data : null)).catch(() => {});
  }, []);
  if (!f) return null;
  return (
    <section className="border-t border-border py-24" data-testid="home-featured-insight">
      <div className="mx-auto max-w-7xl px-6 lg:px-10">
        <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">SK Insights · Featured this week</p>
        <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }}>
          <Link to={`/insight/${f.slug}`} className="group mt-6 grid overflow-hidden rounded-3xl border border-[hsl(var(--primary))]/30 bg-card lg:grid-cols-2">
            <div className="aspect-[16/10] overflow-hidden lg:aspect-auto"><img src={f.hero_image} alt="" className="h-full w-full object-cover transition-transform duration-700 group-hover:scale-105" /></div>
            <div className="flex flex-col justify-center p-8 lg:p-12">
              <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-[hsl(var(--primary))]/15 px-3 py-1 text-xs font-bold uppercase tracking-[0.15em] text-[hsl(var(--primary))]"><Sparkles className="h-3.5 w-3.5" /> {f.category}</span>
              <h2 className="mt-4 font-display text-3xl font-black leading-tight tracking-tight group-hover:text-[hsl(var(--primary))] lg:text-4xl">{f.title}</h2>
              <p className="mt-4 line-clamp-3 text-muted-foreground">{f.dek}</p>
              {f.sk_take && <p className="mt-5 border-l-2 border-[hsl(var(--primary))] pl-4 text-sm italic text-muted-foreground line-clamp-3">“{f.sk_take}”</p>}
              <span className="mt-6 inline-flex items-center gap-1.5 text-sm font-semibold text-[hsl(var(--primary))]">Read the insight <ArrowUpRight className="h-4 w-4" /></span>
            </div>
          </Link>
        </motion.div>
      </div>
    </section>
  );
}
