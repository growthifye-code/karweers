import { useEffect, useState } from "react";
import { Clock } from "lucide-react";

function parts(ms) {
  const s = Math.max(0, Math.floor(ms / 1000));
  return { d: Math.floor(s / 86400), h: Math.floor((s % 86400) / 3600), m: Math.floor((s % 3600) / 60), s: s % 60 };
}

// Shows a live "Offer ends in ..." countdown. Renders nothing if target is missing/past.
export default function Countdown({ target, label = "Offer ends in", testid }) {
  const end = target ? new Date(target).getTime() : 0;
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    if (!end) return;
    const t = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(t);
  }, [end]);
  if (!end || end - now <= 0) return null;
  const p = parts(end - now);
  return (
    <div data-testid={testid} className="inline-flex items-center gap-2 rounded-full bg-[hsl(var(--accent))]/15 px-3 py-1 text-xs font-semibold text-[hsl(var(--accent))]">
      <Clock className="h-3.5 w-3.5" />
      <span>{label} {p.d > 0 && `${p.d}d `}{String(p.h).padStart(2, "0")}:{String(p.m).padStart(2, "0")}:{String(p.s).padStart(2, "0")}</span>
    </div>
  );
}
