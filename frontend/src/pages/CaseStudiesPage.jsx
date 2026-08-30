import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import ArticleCard from "@/components/ArticleCard";
import api from "@/lib/api";

export default function CaseStudiesPage() {
  const [items, setItems] = useState([]);
  useEffect(() => {
    api.get("/articles", { params: { category: "casestudy" } }).then((r) => setItems(r.data)).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Case Studies — Sudarshan Karweer" description="Proof-point case studies across aviation, metals & mining, telecom, agriculture, energy storage and government asset monetisation." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-40 lg:pt-48">
        <div className="pointer-events-none absolute -right-40 top-20 h-96 w-96 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Proof of Delivery</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-extrabold tracking-tight sm:text-5xl">Case studies across a dozen-plus sectors.</h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">From aviation turnarounds and metals CAPEX discipline to telecom monetisation, agri scaling, storage financial close and government asset monetisation.</p>
        </div>
      </section>
      <div className="mx-auto max-w-7xl px-6 pb-24 lg:px-10">
        {items.length === 0 ? (
          <p className="py-20 text-center text-muted-foreground">Loading case studies…</p>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {items.map((a) => <ArticleCard key={a.slug} article={a} testid={`case-${a.slug}`} />)}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
