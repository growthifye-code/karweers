import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { BookOpen, Headphones, ShoppingCart, ArrowUpRight, Sparkles, RefreshCw, Repeat, Mail } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import Captcha from "@/components/Captcha";
import api from "@/lib/api";

const COVERS = [
  "from-[#1f2937] to-[#0b3b2e]", "from-[#3b1f2b] to-[#1a1030]", "from-[#12303b] to-[#0a1f2e]",
  "from-[#2b2410] to-[#0f1a0a]", "from-[#241a3b] to-[#0a1030]", "from-[#0e2f2f] to-[#08201a]",
  "from-[#331f10] to-[#1a0f08]", "from-[#20122b] to-[#0c0a20]", "from-[#102a1f] to-[#08170f]",
];

export default function LibraryPage() {
  const [books, setBooks] = useState([]);
  const [scope, setScope] = useState("shelf");
  const [email, setEmail] = useState("");
  const [captcha, setCaptcha] = useState("");
  const [subBusy, setSubBusy] = useState(false);
  useEffect(() => {
    window.scrollTo(0, 0);
    api.get(`/books${scope === "all" ? "?scope=all" : ""}`).then((r) => setBooks(r.data || [])).catch(() => {});
  }, [scope]);

  const subscribe = async (e) => {
    e.preventDefault();
    if (!email) { toast.error("Please enter your email."); return; }
    if (!captcha) { toast.error("Please complete the captcha."); return; }
    setSubBusy(true);
    try {
      const { data } = await api.post("/newsletter", { email, captcha_token: captcha });
      toast.success(data.message || "You're on the list — the fresh shelf lands every Monday.");
      setEmail("");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Could not subscribe right now.");
    } finally { setSubBusy(false); }
  };

  const today = new Date().toLocaleDateString(undefined, { weekday: "long", month: "short", day: "numeric" });

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Leadership Library — Read, Listen & Watch the Classics | Sudarshan Karweer"
        description="A rotating shelf of leadership classics — read in a page-flip reader, stream free audiobooks and watch talks specific to each book. Every title carries SK's perspective, key learnings and a daily ritual." />
      <Navbar />
      <section className="border-b border-border bg-secondary/30 pt-28 pb-14 md:pt-32">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">
            <BookOpen className="h-3.5 w-3.5" /> Leadership Library
          </span>
          <h1 className="mt-6 max-w-4xl font-display text-4xl font-bold leading-[1.05] md:text-6xl">Read. Listen. Watch. <span className="text-[hsl(var(--primary))]">All here.</span></h1>
          <p className="mt-5 max-w-2xl text-base text-muted-foreground md:text-lg">Timeless leadership books — read the classics in a page-flip reader, hear free audiobooks, and watch talks specific to each book. Every title carries SK's perspective, the key learnings, and how to turn it into a daily ritual.</p>
          <div className="mt-7 flex flex-wrap items-center gap-3">
            <button onClick={() => setScope("shelf")} data-testid="library-tab-shelf"
              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition-colors ${scope === "shelf" ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border border-border text-foreground hover:border-[hsl(var(--primary))]"}`}>
              <Sparkles className="h-4 w-4" /> Today's shelf
            </button>
            <button onClick={() => setScope("all")} data-testid="library-tab-all"
              className={`inline-flex items-center gap-1.5 rounded-full px-4 py-2 text-sm font-semibold transition-colors ${scope === "all" ? "bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))]" : "border border-border text-foreground hover:border-[hsl(var(--primary))]"}`}>
              <BookOpen className="h-4 w-4" /> Browse the full library
            </button>
            {scope === "shelf" && <span className="inline-flex items-center gap-1.5 text-xs text-muted-foreground" data-testid="library-refresh-note"><RefreshCw className="h-3.5 w-3.5" /> Fresh picks every day · {today}</span>}
          </div>
        </div>
      </section>
      <section className="py-14">
        <div className="mx-auto grid max-w-7xl gap-6 px-6 sm:grid-cols-2 lg:grid-cols-3 lg:px-10" data-testid="library-grid">
          {books.map((b, i) => (
            <Link key={b.slug} to={`/library/${b.slug}`} data-testid={`book-card-${b.slug}`}
              className="group flex flex-col overflow-hidden rounded-2xl border border-border bg-card transition-all hover:-translate-y-1 hover:border-[hsl(var(--primary))]/50">
              <div className={`relative flex aspect-[16/10] flex-col justify-end bg-gradient-to-br ${COVERS[i % COVERS.length]} p-5`}>
                <span className="absolute right-4 top-4 rounded-full bg-black/30 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-white/90">{b.theme}</span>
                <p className="font-display text-2xl font-bold leading-tight text-white">{b.title}</p>
                <p className="mt-1 text-sm text-white/70">{b.author} · {b.year}</p>
              </div>
              <div className="flex flex-1 flex-col p-5">
                <p className="flex-1 text-sm leading-relaxed text-muted-foreground line-clamp-3">{b.blurb}</p>
                <div className="mt-4 flex flex-wrap items-center gap-2">
                  {b.has_read && <span className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))]/10 px-2.5 py-1 text-[11px] font-semibold text-[hsl(var(--primary))]"><BookOpen className="h-3 w-3" /> Read free</span>}
                  {b.has_audio && <span className="inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))]/10 px-2.5 py-1 text-[11px] font-semibold text-[hsl(var(--primary))]"><Headphones className="h-3 w-3" /> Audiobook</span>}
                  <span className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[11px] font-semibold text-muted-foreground"><Repeat className="h-3 w-3" /> Ritual</span>
                  {!b.public_domain && <span className="inline-flex items-center gap-1 rounded-full border border-border px-2.5 py-1 text-[11px] font-semibold text-muted-foreground"><ShoppingCart className="h-3 w-3" /> Get it</span>}
                </div>
                <span className="mt-4 inline-flex items-center gap-1 text-sm font-semibold text-foreground group-hover:text-[hsl(var(--primary))]">Open <ArrowUpRight className="h-4 w-4" /></span>
              </div>
            </Link>
          ))}
        </div>
      </section>
      <section className="border-t border-border bg-secondary/30 py-14">
        <div className="mx-auto max-w-3xl px-6 text-center lg:px-10">
          <span className="grid h-12 w-12 mx-auto place-items-center rounded-xl bg-[hsl(var(--primary))]/12 text-[hsl(var(--primary))]"><Mail className="h-6 w-6" /></span>
          <h2 className="mt-5 font-display text-2xl font-bold md:text-3xl">Get the fresh shelf every Monday</h2>
          <p className="mx-auto mt-3 max-w-xl text-sm text-muted-foreground md:text-base">Join the Library digest and we'll email you the week's rotating picks — read, listen and turn each into a ritual. Unsubscribe anytime.</p>
          <form onSubmit={subscribe} data-testid="library-subscribe" className="mx-auto mt-6 flex max-w-md flex-col gap-3 sm:flex-row">
            <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" placeholder="you@company.com" data-testid="library-subscribe-email"
              className="flex-1 rounded-full border border-border bg-background px-5 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
            <button type="submit" disabled={subBusy} data-testid="library-subscribe-btn"
              className="inline-flex items-center justify-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-60">
              {subBusy ? "Joining…" : "Get the digest"}
            </button>
          </form>
          <div className="mt-4 flex justify-center"><Captcha onVerify={setCaptcha} onExpire={() => setCaptcha("")} /></div>
        </div>
      </section>
      <Footer />
    </div>
  );
}
