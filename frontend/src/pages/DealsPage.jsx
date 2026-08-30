import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import DealsTicker from "@/components/DealsTicker";

export default function DealsPage() {
  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Deals & Developments — Sudarshan Karweer" description="Live renewables M&A, fundraises and developments — an auto-curated feed refreshed daily." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-40 lg:pt-44">
        <div className="pointer-events-none absolute -right-40 top-20 h-96 w-96 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Deals & Developments</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-extrabold tracking-tight sm:text-5xl">Live renewables M&amp;A and fundraises.</h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">An auto-curated feed of the latest deals, fundraises and developments across renewables, storage and green hydrogen.</p>
        </div>
      </section>
      <DealsTicker />
      <Footer />
    </div>
  );
}
