import { useEffect, useState } from "react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Hero from "@/components/sections/Hero";
import Stats from "@/components/sections/Stats";
import Sectors from "@/components/sections/Sectors";
import About from "@/components/sections/About";
import Services from "@/components/sections/Services";
import MarketPulse from "@/components/sections/MarketPulse";
import InsightsPreview from "@/components/sections/InsightsPreview";
import AIInsights from "@/components/sections/AIInsights";
import FeaturedInsight from "@/components/sections/FeaturedInsight";
import CaseStudies from "@/components/sections/CaseStudies";
import Consultation from "@/components/sections/Consultation";
import LearningStrip from "@/components/sections/LearningStrip";
import NewsletterSignup from "@/components/NewsletterSignup";
import DealsTicker from "@/components/DealsTicker";
import Seo from "@/components/Seo";
import api from "@/lib/api";

export default function Home() {
  const [meta, setMeta] = useState({ services: [], stats: [], market_pulse: [], testimonials: [] });
  const [articles, setArticles] = useState([]);
  const [cases, setCases] = useState([]);
  const [homeContent, setHomeContent] = useState(null);

  useEffect(() => {
    api.get("/meta").then((r) => setMeta(r.data)).catch(() => {});
    api.get("/articles").then((r) => setArticles(r.data)).catch(() => {});
    api.get("/articles", { params: { category: "casestudy" } }).then((r) => setCases(r.data)).catch(() => {});
    api.get("/home/content").then((r) => setHomeContent(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (window.location.hash) {
      const el = document.querySelector(window.location.hash);
      if (el) setTimeout(() => el.scrollIntoView({ behavior: "smooth" }), 300);
    }
  }, []);

  return (
    <div className="min-h-screen bg-background text-foreground text-left">
      <Seo title="Sudarshan Karweer — Business Coach & Energy Transition Advisor"
        description="Premium 1:1 strategic consultation for renewable energy, storage & green hydrogen founders. Fundraising, strategy, scaling, climate finance & government asset monetisation. 23Y+, 60+ projects."
        jsonLd={{ "@context": "https://schema.org", "@type": "ProfessionalService", name: "Sudarshan Karweer Advisory", description: "Business coaching & strategic advisory across the energy transition.", email: "sudarshan@karweers.com", areaServed: "Global" }} />
      <Navbar />
      <Hero content={homeContent} />
      <Stats stats={meta.stats} />
      <Sectors />
      <About />
      <Services services={meta.services} />
      <MarketPulse pulse={meta.market_pulse} />
      <DealsTicker />
      <AIInsights content={homeContent} />
      <FeaturedInsight />
      <InsightsPreview articles={articles} />
      <CaseStudies cases={cases} />
      <LearningStrip />
      <Consultation testimonials={meta.testimonials} />
      <NewsletterSignup />
      <Footer />
    </div>
  );
}
