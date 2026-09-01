import { useState } from "react";
import { Linkedin, Twitter, MessageCircle, Mail, Link2, Share2, Check } from "lucide-react";
import { toast } from "sonner";

// Reusable social-share row. Works on any page; falls back to the native share sheet on mobile.
export default function ShareBar({ title = "", text = "", url = "", compact = false }) {
  const [copied, setCopied] = useState(false);
  const shareUrl = url || (typeof window !== "undefined" ? window.location.href : "");
  const t = encodeURIComponent(title);
  const u = encodeURIComponent(shareUrl);
  const body = encodeURIComponent(`${title}\n\n${text}\n\n${shareUrl}`);

  const links = [
    { key: "linkedin", label: "LinkedIn", icon: Linkedin, href: `https://www.linkedin.com/sharing/share-offsite/?url=${u}` },
    { key: "twitter", label: "X", icon: Twitter, href: `https://twitter.com/intent/tweet?text=${t}&url=${u}` },
    { key: "whatsapp", label: "WhatsApp", icon: MessageCircle, href: `https://wa.me/?text=${encodeURIComponent(title + " " + shareUrl)}` },
    { key: "email", label: "Email", icon: Mail, href: `mailto:?subject=${t}&body=${body}` },
  ];

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(shareUrl);
      setCopied(true); toast.success("Link copied");
      setTimeout(() => setCopied(false), 1800);
    } catch { toast.error("Couldn't copy the link"); }
  };

  const nativeShare = async () => {
    if (navigator.share) {
      try { await navigator.share({ title, text, url: shareUrl }); } catch { /* dismissed */ }
    } else { copy(); }
  };

  return (
    <div className="flex flex-wrap items-center gap-2" data-testid="share-bar">
      {!compact && <span className="mr-1 inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.15em] text-muted-foreground"><Share2 className="h-4 w-4" /> Share</span>}
      {links.map((l) => (
        <a key={l.key} href={l.href} target="_blank" rel="noopener noreferrer" title={l.label}
          data-testid={`share-${l.key}`}
          className="grid h-9 w-9 place-items-center rounded-full border border-border bg-card text-muted-foreground transition-all hover:-translate-y-0.5 hover:border-[hsl(var(--primary))] hover:text-[hsl(var(--primary))]">
          <l.icon className="h-4 w-4" />
        </a>
      ))}
      <button onClick={copy} title="Copy link" data-testid="share-copy"
        className="grid h-9 w-9 place-items-center rounded-full border border-border bg-card text-muted-foreground transition-all hover:-translate-y-0.5 hover:border-[hsl(var(--primary))] hover:text-[hsl(var(--primary))]">
        {copied ? <Check className="h-4 w-4 text-[hsl(var(--primary))]" /> : <Link2 className="h-4 w-4" />}
      </button>
      <button onClick={nativeShare} title="Share" data-testid="share-native"
        className="grid h-9 w-9 place-items-center rounded-full border border-border bg-card text-muted-foreground transition-all hover:-translate-y-0.5 hover:border-[hsl(var(--primary))] hover:text-[hsl(var(--primary))] sm:hidden">
        <Share2 className="h-4 w-4" />
      </button>
    </div>
  );
}
