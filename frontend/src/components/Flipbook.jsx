import { forwardRef, useMemo, useRef, useState, useEffect } from "react";
import HTMLFlipBook from "react-pageflip";
import { ChevronLeft, ChevronRight } from "lucide-react";

const Page = forwardRef(({ children, num }, ref) => (
  <div ref={ref} className="flipbook-page bg-[#f6f1e7] text-[#2b2620]" data-density="soft">
    <div className="flex h-full flex-col px-7 py-8">
      <div className="flex-1 overflow-hidden whitespace-pre-wrap font-serif text-[13.5px] leading-[1.75]">{children}</div>
      {num != null && <div className="pt-3 text-center text-[11px] text-[#8a7f6c]">{num}</div>}
    </div>
  </div>
));
Page.displayName = "Page";

function paginate(text, perPage = 1300) {
  const clean = (text || "").replace(/\r\n/g, "\n").trim();
  const paras = clean.split(/\n{2,}/).filter(Boolean);
  const pages = [];
  let buf = "";
  for (const p of paras) {
    if ((buf + "\n\n" + p).length > perPage && buf) { pages.push(buf.trim()); buf = p; }
    else { buf = buf ? buf + "\n\n" + p : p; }
    while (buf.length > perPage * 1.6) { pages.push(buf.slice(0, perPage).trim()); buf = buf.slice(perPage); }
  }
  if (buf.trim()) pages.push(buf.trim());
  return pages.length ? pages : ["The text will appear here."];
}

export default function Flipbook({ text, title }) {
  const bookRef = useRef(null);
  const [page, setPage] = useState(0);
  const [dims, setDims] = useState({ w: 460, h: 620 });
  const pages = useMemo(() => paginate(text), [text]);

  useEffect(() => {
    const resize = () => {
      const vw = Math.min(window.innerWidth - 48, 980);
      const single = window.innerWidth < 768;
      const w = single ? Math.min(vw, 460) : Math.min(Math.floor(vw / 2), 480);
      setDims({ w, h: Math.min(Math.floor(w * 1.35), 640) });
    };
    resize();
    window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, []);

  const flip = (dir) => {
    const api = bookRef.current?.pageFlip?.();
    if (!api) return;
    dir === "next" ? api.flipNext() : api.flipPrev();
  };

  return (
    <div className="flex flex-col items-center" data-testid="flipbook">
      <div className="w-full overflow-hidden rounded-xl bg-[#2a2620] p-3 shadow-2xl sm:p-6">
        <HTMLFlipBook
          ref={bookRef}
          width={dims.w}
          height={dims.h}
          size="stretch"
          minWidth={280}
          maxWidth={480}
          minHeight={380}
          maxHeight={640}
          maxShadowOpacity={0.4}
          showCover={false}
          mobileScrollSupport={true}
          drawShadow={true}
          usePortrait={true}
          flippingTime={700}
          className="mx-auto"
          onFlip={(e) => setPage(e.data)}
        >
          {pages.map((p, i) => (
            <Page key={i} num={`${i + 1} / ${pages.length}`}>{p}</Page>
          ))}
        </HTMLFlipBook>
      </div>
      <div className="mt-4 flex items-center gap-4">
        <button onClick={() => flip("prev")} disabled={page <= 0} data-testid="flip-prev"
          className="inline-flex items-center gap-1 rounded-full border border-border px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:border-[hsl(var(--primary))] disabled:opacity-40">
          <ChevronLeft className="h-4 w-4" /> Prev
        </button>
        <span className="text-xs text-muted-foreground">Page {page + 1} of {pages.length}</span>
        <button onClick={() => flip("next")} disabled={page >= pages.length - 1} data-testid="flip-next"
          className="inline-flex items-center gap-1 rounded-full border border-border px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:border-[hsl(var(--primary))] disabled:opacity-40">
          Next <ChevronRight className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
