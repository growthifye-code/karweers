import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import MarketPulse from "@/components/sections/MarketPulse";
import api from "@/lib/api";

export default function MarketPage() {
  const [pulse, setPulse] = useState([]);
  useEffect(() => { api.get("/meta").then((r) => setPulse(r.data.market_pulse || [])).catch(() => {}); }, []);
  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Market Pulse — Sudarshan Karweer" description="Live market data across lithium, solar, storage and energy-transition benchmarks that move the sector." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-40 lg:pt-44">
        <div className="pointer-events-none absolute -right-40 top-20 h-96 w-96 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Market Intelligence</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-extrabold tracking-tight sm:text-5xl">Live signals from the energy transition.</h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">Real-time benchmarks across lithium, solar, storage and clean-energy equities — the numbers that shape capital and strategy decisions.</p>
        </div>
      </section>
      <MarketPulse pulse={pulse} />
      <Footer />
    </div>
  );
}
