import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Swords, Shield, Users, UserCheck, Wallet, Truck, ArrowUpRight, Gamepad2 } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";

const ICONS = { swords: Swords, shield: Shield, users: Users, "user-check": UserCheck, wallet: Wallet, truck: Truck };
const COVERS = [
  "from-[#2a1810] to-[#0f0a06]", "from-[#12222b] to-[#08131a]", "from-[#1f1a2e] to-[#0b0a18]",
  "from-[#102a1f] to-[#08170f]", "from-[#2b1a12] to-[#150c08]", "from-[#101f2b] to-[#080f18]",
];

export default function GamesPage() {
  const [games, setGames] = useState([]);
  useEffect(() => { window.scrollTo(0, 0); api.get("/games").then((r) => setGames(r.data || [])).catch(() => {}); }, []);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Strategy Simulations — CX-Level War-Room Games | Sudarshan Karweer"
        description="Rehearse the hard calls: scenario-based leadership games rooted in Art of War, Extreme Ownership, team trust, hiring, cash & runway and the supply-chain bullwhip — each with a score and a Key Lessons debrief in SK's voice." />
      <Navbar />
      <section className="border-b border-border bg-secondary/30 pt-28 pb-14 md:pt-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">
            <Gamepad2 className="h-3.5 w-3.5" /> War Room
          </span>
          <h1 className="mt-6 max-w-4xl font-display text-4xl font-bold leading-[1.05] md:text-6xl">Rehearse the <span className="text-[hsl(var(--primary))]">hard calls.</span></h1>
          <p className="mt-5 max-w-2xl text-base text-muted-foreground md:text-lg">Scenario-based decision games for senior leaders. Every choice scores and explains itself — then you get a debrief in Sudarshan's voice and the key lessons to take back to your own boardroom.</p>
        </div>
      </section>
      <section className="py-14">
        <div className="mx-auto grid max-w-7xl gap-6 px-6 md:grid-cols-2 lg:grid-cols-3 lg:px-10" data-testid="games-grid">
          {games.map((g, i) => {
            const Icon = ICONS[g.icon] || Swords;
            return (
              <Link key={g.slug} to={`/games/${g.slug}`} data-testid={`game-card-${g.slug}`}
                className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card transition-all hover:-translate-y-1 hover:border-[hsl(var(--primary))]/50">
                <div className={`relative flex aspect-[16/9] flex-col justify-between bg-gradient-to-br ${COVERS[i % COVERS.length]} p-6`}>
                  <span className="grid h-12 w-12 place-items-center rounded-xl bg-[hsl(var(--primary))]/15 text-[hsl(var(--primary))] backdrop-blur"><Icon className="h-6 w-6" /></span>
                  <div>
                    <span className="rounded-full bg-black/30 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-white/90">{g.tag}</span>
                    <p className="mt-2 font-display text-2xl font-bold leading-tight text-white">{g.title}</p>
                  </div>
                </div>
                <div className="flex flex-1 flex-col p-5">
                  <p className="text-[11px] font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">{g.framework}</p>
                  <p className="mt-2 flex-1 text-sm leading-relaxed text-muted-foreground">{g.blurb}</p>
                  <div className="mt-4 flex items-center justify-between">
                    <span className="text-xs text-muted-foreground">{g.rounds} decisions</span>
                    <span className="inline-flex items-center gap-1 text-sm font-semibold text-foreground group-hover:text-[hsl(var(--primary))]">Enter the room <ArrowUpRight className="h-4 w-4" /></span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </section>
      <Footer />
    </div>
  );
}
