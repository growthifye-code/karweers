import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { BookOpen, Headphones, Play, ShoppingCart, ChevronLeft, Sparkles, Info, Repeat, MessageSquare } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import VideoCard from "@/components/VideoCard";
import Flipbook from "@/components/Flipbook";
import api, { API, track } from "@/lib/api";

export default function BookPage() {
  const { slug } = useParams();
  const [book, setBook] = useState(null);
  const [tab, setTab] = useState("overview");
  const [text, setText] = useState("");
  const [textLoading, setTextLoading] = useState(false);

  useEffect(() => { window.scrollTo(0, 0); }, [slug]);
  useEffect(() => {
    api.get(`/books/${slug}`).then((r) => { setBook(r.data); track("book", slug); }).catch(() => setBook(false));
  }, [slug]);

  const openRead = () => {
    setTab("read");
    if (!text && book?.has_read) {
      setTextLoading(true);
      api.get(`/books/${slug}/text`, { responseType: "text" })
        .then((r) => setText(typeof r.data === "string" ? r.data : ""))
        .catch(() => setText("Sorry — the text couldn't be loaded right now."))
        .finally(() => setTextLoading(false));
    }
  };

  if (book === false) return (
    <div className="min-h-screen bg-background text-foreground"><Navbar />
      <div className="grid place-items-center py-40 text-center"><h1 className="font-display text-3xl font-bold">Book not found</h1>
        <Link to="/library" className="mt-6 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))]">Back to library</Link></div><Footer /></div>
  );

  const tabs = [["overview", "Overview", Sparkles]];
  if (book?.has_read) tabs.push(["read", "Read", BookOpen]);
  if (book?.has_audio) tabs.push(["listen", "Listen", Headphones]);
  if (book?.videos && book.videos.length) tabs.push(["watch", "Watch", Play]);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title={book ? `${book.title} — ${book.author} | Leadership Library` : "Loading…"} description={book?.blurb} />
      <Navbar />
      <section className="border-b border-border bg-secondary/30 pt-28 pb-12 md:pt-32">
        <div className="mx-auto max-w-5xl px-6 lg:px-10">
          <Link to="/library" data-testid="book-back" className="inline-flex items-center gap-1 text-sm font-medium text-muted-foreground hover:text-foreground"><ChevronLeft className="h-4 w-4" /> Leadership Library</Link>
          {book && (
            <div className="mt-6 flex flex-col gap-6 md:flex-row md:items-end md:justify-between">
              <div>
                <span className="inline-flex items-center rounded-full border border-[hsl(var(--primary))]/40 bg-[hsl(var(--primary))]/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(var(--primary))]">{book.theme}</span>
                <h1 className="mt-4 font-display text-4xl font-bold md:text-5xl" data-testid="book-title">{book.title}</h1>
                <p className="mt-2 text-base text-muted-foreground">{book.author} · {book.year}</p>
              </div>
              <div className="flex flex-shrink-0 flex-wrap gap-3">
                <Link to={`/?area=Business%20Coaching&msg=${encodeURIComponent(`I'd like to discuss "${book.title}" by ${book.author} and how to apply its ideas in my business.`)}#consult`}
                  data-testid="book-discuss-sk"
                  className="inline-flex items-center gap-2 rounded-full border border-[hsl(var(--primary))] px-5 py-3 text-sm font-semibold text-[hsl(var(--primary))] transition-colors hover:bg-[hsl(var(--primary))]/10">
                  <MessageSquare className="h-4 w-4" /> Discuss this with SK
                </Link>
                <a href={book.amazon} target="_blank" rel="noopener noreferrer" data-testid="book-amazon"
                  className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                  <ShoppingCart className="h-4 w-4" /> Get it on Amazon
                </a>
              </div>
            </div>
          )}
        </div>
      </section>

      {book && (
        <section className="py-10">
          <div className="mx-auto max-w-5xl px-6 lg:px-10">
            <div className="flex flex-wrap gap-2 border-b border-border">
              {tabs.map(([id, label, Icon]) => (
                <button key={id} onClick={() => id === "read" ? openRead() : setTab(id)} data-testid={`book-tab-${id}`}
                  className={`flex items-center gap-1.5 border-b-2 px-3 pb-2.5 text-sm font-semibold transition-colors ${tab === id ? "border-[hsl(var(--primary))] text-[hsl(var(--primary))]" : "border-transparent text-muted-foreground hover:text-foreground"}`}>
                  <Icon className="h-4 w-4" /> {label}
                </button>
              ))}
            </div>

            <div className="mt-6">
              {tab === "overview" && (
                <div className="space-y-6">
                  <div className="grid gap-6 md:grid-cols-2">
                    <div className="rounded-2xl border border-border bg-card p-6">
                      <h3 className="font-display text-lg font-bold">About</h3>
                      <p className="mt-3 text-sm leading-relaxed text-muted-foreground">{book.blurb}</p>
                      <div className="mt-4 rounded-xl border border-[hsl(var(--primary))]/30 bg-[hsl(var(--primary))]/5 p-4">
                        <p className="flex items-center gap-1.5 text-xs font-bold text-[hsl(var(--primary))]"><Sparkles className="h-3.5 w-3.5" /> SK's perspective</p>
                        <p className="mt-2 text-sm text-foreground">{book.why_sk}</p>
                      </div>
                    </div>
                    <div className="rounded-2xl border border-border bg-card p-6">
                      <h3 className="font-display text-lg font-bold">Key learnings</h3>
                      <ul className="mt-3 space-y-2.5">
                        {book.lessons.map((l, i) => (
                          <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                            <span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[hsl(var(--primary))]" />{l}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  {(book.ritual || book.ritual_pro?.length || book.ritual_personal?.length) && (
                    <div className="rounded-2xl border border-[hsl(var(--primary))]/30 bg-gradient-to-br from-[hsl(var(--primary))]/8 to-transparent p-6" data-testid="book-ritual">
                      <h3 className="flex items-center gap-2 font-display text-lg font-bold"><Repeat className="h-5 w-5 text-[hsl(var(--primary))]" /> Make it a ritual</h3>
                      {book.ritual && <p className="mt-2 max-w-3xl text-sm leading-relaxed text-muted-foreground">{book.ritual}</p>}
                      <div className="mt-5 grid gap-5 md:grid-cols-2">
                        <div className="rounded-xl border border-border bg-card/70 p-5">
                          <p className="text-[11px] font-bold uppercase tracking-widest text-[hsl(var(--primary))]">Professional life</p>
                          <ul className="mt-3 space-y-2.5">
                            {(book.ritual_pro || []).map((l, i) => (
                              <li key={i} className="flex items-start gap-2 text-sm text-foreground/90"><span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[hsl(var(--primary))]" />{l}</li>
                            ))}
                          </ul>
                        </div>
                        <div className="rounded-xl border border-border bg-card/70 p-5">
                          <p className="text-[11px] font-bold uppercase tracking-widest text-[hsl(var(--primary))]">Personal life</p>
                          <ul className="mt-3 space-y-2.5">
                            {(book.ritual_personal || []).map((l, i) => (
                              <li key={i} className="flex items-start gap-2 text-sm text-foreground/90"><span className="mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-[hsl(var(--primary))]" />{l}</li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {tab === "read" && (
                <div data-testid="book-reader">
                  {textLoading ? (
                    <div className="grid place-items-center py-16"><div className="h-8 w-8 animate-spin rounded-full border-2 border-[hsl(var(--primary))] border-t-transparent" /></div>
                  ) : text && !text.startsWith("Sorry") ? (
                    <Flipbook text={text} title={book.title} />
                  ) : (
                    <div className="rounded-2xl border border-border bg-card p-6 text-sm text-muted-foreground">{text || "Loading the book…"}</div>
                  )}
                </div>
              )}

              {tab === "listen" && book.audio_embed && (
                <div className="rounded-2xl border border-border bg-card p-4" data-testid="book-audio">
                  <iframe src={book.audio_embed} title={`${book.title} audiobook`} className="h-[360px] w-full rounded-lg" frameBorder="0" allowFullScreen />
                  <p className="mt-3 text-xs text-muted-foreground">Free audiobook streamed from LibriVox via the Internet Archive.</p>
                </div>
              )}

              {tab === "watch" && (
                <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3" data-testid="book-videos">
                  {(book.videos || []).length ? book.videos.map((v) => (
                    <VideoCard key={v.video_id} video={v} onPlay={() => track("video", `book:${slug}`)} />
                  )) : <p className="text-sm text-muted-foreground">Curated talks loading…</p>}
                </div>
              )}
            </div>

            <p className="mt-8 inline-flex items-start gap-1.5 text-xs text-muted-foreground" data-testid="book-credit">
              <Info className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" /> {book.source} — {book.credit}
            </p>
          </div>
        </section>
      )}
      <Footer />
    </div>
  );
}
