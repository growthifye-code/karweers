import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import StrategyToolkit from "@/components/StrategyToolkit";

export default function StrategyToolkitPage() {
  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Strategy Toolkit — Sudarshan Karweer" description="Free, branded strategy worksheets and operational guidelines — Ansoff, SWOT/TOWS, 7S, Porter's Five Forces, BCG, PESTLE, VRIO, Blue Ocean, 5 Whys, Fishbone, Issue Trees and more." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-40 lg:pt-48">
        <div className="pointer-events-none absolute -right-40 top-20 h-96 w-96 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-4 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Strategy Toolkit</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-black tracking-tight sm:text-5xl">A consultant-grade toolkit, in your hands.</h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">The frameworks Sudarshan uses on live engagements — each a premium, ready-to-use worksheet with operational guidelines. Free to download.</p>
        </div>
      </section>
      <StrategyToolkit />
      <Footer />
    </div>
  );
}
