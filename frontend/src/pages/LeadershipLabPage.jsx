import { Link } from "react-router-dom";
import { BookOpen, Compass, Swords, ArrowUpRight } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";

const CARDS = [
  { to: "/assessment", icon: Compass, tag: "Assessment", title: "Leadership Blueprint", testid: "lab-assessment",
    desc: "A validated Big Five profile maps you to a leadership quadrant, then Sudarshan draws out your strengths, blind spots and a milestone roadmap.", cta: "Discover your quadrant" },
  { to: "/library", icon: BookOpen, tag: "Library", title: "Leadership Library", testid: "lab-library",
    desc: "Read the classics in-site, listen to free audiobooks, and watch curated talks — Art of War, The Prince, Meditations, Extreme Ownership, Shoe Dog and more.", cta: "Enter the library" },
  { to: "/games", icon: Swords, tag: "War Room", title: "Strategy Simulations", testid: "lab-games",
    desc: "CX-level decision games rooted in Art of War, Extreme Ownership, team trust, hiring, cash & runway and the supply-chain bullwhip — each scored, with a Key Lessons debrief in SK's voice.", cta: "Enter the War Room" },
];

export default function LeadershipLabPage() {
  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Leadership Lab — Blueprint, Library & Strategy Simulations | Sudarshan Karweer"
        description="Sharpen how you lead: a Big Five leadership blueprint, an in-site library of leadership classics (read, listen, watch), and CX-level strategy simulations." />
      <Navbar />
      <section className="border-b border-border bg-secondary/30 pt-28 pb-14 md:pt-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">
            <Compass className="h-3.5 w-3.5" /> Leadership Lab
          </span>
          <h1 className="mt-6 max-w-4xl font-display text-4xl font-bold leading-[1.05] md:text-6xl">
            Sharpen how you <span className="text-[hsl(var(--primary))]">lead.</span>
          </h1>
          <p className="mt-5 max-w-2xl text-base text-muted-foreground md:text-lg">
            Know yourself, learn from the masters, and rehearse the hard calls — a blueprint of your leadership style, a living library of classics, and strategy simulations for senior leaders.
          </p>
        </div>
      </section>
      <section className="py-14">
        <div className="mx-auto grid max-w-7xl gap-6 px-6 md:grid-cols-3 lg:px-10">
          {CARDS.map((c) => (
            <Link key={c.title} to={c.to} data-testid={c.testid}
              className={`group flex flex-col rounded-2xl border border-border bg-card p-7 transition-all hover:-translate-y-1 hover:border-[hsl(var(--primary))]/50 ${c.soon ? "opacity-80" : ""}`}>
              <span className="grid h-12 w-12 place-items-center rounded-xl bg-[hsl(var(--primary))]/12 text-[hsl(var(--primary))]"><c.icon className="h-6 w-6" /></span>
              <span className="mt-5 text-[11px] font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">{c.tag}</span>
              <h2 className="mt-2 font-display text-2xl font-bold">{c.title}</h2>
              <p className="mt-3 flex-1 text-sm leading-relaxed text-muted-foreground">{c.desc}</p>
              <span className="mt-5 inline-flex items-center gap-1 text-sm font-semibold text-foreground group-hover:text-[hsl(var(--primary))]">{c.cta} <ArrowUpRight className="h-4 w-4" /></span>
            </Link>
          ))}
        </div>
      </section>
      <Footer />
    </div>
  );
}
