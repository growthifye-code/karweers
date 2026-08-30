import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Hero from "@/components/sections/Hero";
import Stats from "@/components/sections/Stats";
import About from "@/components/sections/About";
import Services from "@/components/sections/Services";
import MarketPulse from "@/components/sections/MarketPulse";
import InsightsPreview from "@/components/sections/InsightsPreview";
import CaseStudies from "@/components/sections/CaseStudies";
import Consultation from "@/components/sections/Consultation";
import api from "@/lib/api";

export default function Home() {
  const [meta, setMeta] = useState({ services: [], stats: [], market_pulse: [], testimonials: [] });
  const [articles, setArticles] = useState([]);
  const [cases, setCases] = useState([]);

  useEffect(() => {
    api.get("/meta").then((r) => setMeta(r.data)).catch(() => {});
    api.get("/articles").then((r) => setArticles(r.data)).catch(() => {});
    api.get("/articles", { params: { category: "casestudy" } }).then((r) => setCases(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (window.location.hash) {
      const el = document.querySelector(window.location.hash);
      if (el) setTimeout(() => el.scrollIntoView({ behavior: "smooth" }), 300);
    }
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground text-left">
      <Navbar />
      <Hero />
      <Stats stats={meta.stats} />
      <About />
      <Services services={meta.services} />
      <MarketPulse pulse={meta.market_pulse} />
      <InsightsPreview articles={articles} />
      <CaseStudies cases={cases} />
      <Consultation testimonials={meta.testimonials} />
      <Footer />
    </div>
  );
}
