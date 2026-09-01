import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowUpRight, Star } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";
import { SK_PORTRAITS } from "@/lib/assets";

export default function ServicesIndex() {
  const [services, setServices] = useState([]);
  useEffect(() => { api.get("/services").then((r) => setServices(r.data)).catch(() => {}); }, []);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Services — Sudarshan Karweer" description="Premium 1:1 consultation, RE/Storage/Green Hydrogen advisory, green & climate financing, government asset monetisation and business coaching for founders & CXOs." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-40 lg:pt-48">
        <div className="pointer-events-none absolute -right-40 top-20 h-96 w-96 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Services</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-black tracking-tight sm:text-5xl">Advisory built for decisions that move capital.</h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">Every engagement follows a clear workflow with a defined approach and measurable outcomes. Explore each.</p>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 pb-24 lg:px-10">
        <div className="grid gap-6 md:grid-cols-2">
          {services.map((s, i) => (
            <Link key={s.slug} to={`/services/${s.slug}`} data-testid={`service-card-${s.slug}`} className="group grid gap-0 overflow-hidden rounded-2xl border border-border bg-card transition-transform hover:-translate-y-1 sm:grid-cols-[1fr_140px]">
              <div className="p-8">
                <p className="font-display text-sm font-bold text-muted-foreground">0{i + 1}</p>
                {s.signature && (
                  <span data-testid={`signature-badge-${s.slug}`} className="mt-2 inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))]/15 px-2.5 py-0.5 text-[11px] font-bold uppercase tracking-wide text-[hsl(var(--primary))]">
                    <Star className="h-3 w-3" /> Signature strength
                  </span>
                )}
                <h3 className="mt-3 font-display text-xl font-bold leading-snug group-hover:text-[hsl(var(--primary))]">{s.title}</h3>
                <p className="mt-3 text-sm leading-relaxed text-muted-foreground line-clamp-3">{s.overview}</p>
                <span className="mt-5 inline-flex items-center gap-1 text-sm font-semibold text-[hsl(var(--primary))]">Explore <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" /></span>
              </div>
              <div className="hidden overflow-hidden bg-[hsl(var(--primary))]/10 sm:block">
                <img src={s.slug === "premium-consultation" ? (SK_PORTRAITS[s.portrait] || SK_PORTRAITS.advisory) : s.hero_image} alt="" className={`h-full w-full object-cover opacity-90 ${s.slug === "premium-consultation" ? "object-top" : "object-center"}`} />
              </div>
            </Link>
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}
