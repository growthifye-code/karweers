import { useState, useRef, useEffect } from "react";
import { Sparkles, X, Send } from "lucide-react";
import { API } from "@/lib/api";

const SUGGESTIONS = [
  "Is battery storage bankable in India yet?",
  "How do I structure a green financing round?",
  "What's the path to green hydrogen cost parity?",
];

export default function AIChatWidget() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState([
    { role: "ai", text: "Hi, I'm Karweer AI — Sudarshan's advisory engine. Ask me about the energy transition, financing, strategy or scaling." },
  ]);
  const sessionId = useRef("web-" + Math.random().toString(36).slice(2));
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, open]);

  const send = async (text) => {
    const q = (text ?? input).trim();
    if (!q || busy) return;
    setInput("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", text: q }, { role: "ai", text: "" }]);
    try {
      const res = await fetch(`${API}/ai/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId.current, message: q }),
      });
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop();
        for (const p of parts) {
          const line = p.replace(/^data:\s*/, "").trim();
          if (!line) continue;
          try {
            const evt = JSON.parse(line);
            if (evt.delta) {
              setMessages((m) => {
                const copy = [...m];
                copy[copy.length - 1] = { role: "ai", text: copy[copy.length - 1].text + evt.delta };
                return copy;
              });
            } else if (evt.error) {
              setMessages((m) => {
                const copy = [...m];
                copy[copy.length - 1] = { role: "ai", text: "Sorry, I hit an issue. Please try again." };
                return copy;
              });
            }
          } catch { /* ignore partial */ }
        }
      }
    } catch {
      setMessages((m) => {
        const copy = [...m];
        copy[copy.length - 1] = { role: "ai", text: "Connection issue. Please try again." };
        return copy;
      });
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <button
        onClick={() => setOpen(!open)}
        data-testid="ai-widget-toggle"
        className="fixed bottom-6 right-6 z-[60] flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-5 py-3.5 font-semibold text-[hsl(var(--primary-foreground))] shadow-2xl transition-transform hover:-translate-y-1"
      >
        {open ? <X className="h-5 w-5" /> : <Sparkles className="h-5 w-5" />}
        <span className="hidden sm:inline">{open ? "Close" : "Ask Karweer AI"}</span>
      </button>

      {open && (
        <div
          data-testid="ai-widget-panel"
          className="fixed bottom-24 right-6 z-[60] flex h-[32rem] w-[min(92vw,26rem)] flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-2xl"
        >
          <div className="flex items-center gap-3 border-b border-border bg-[hsl(var(--primary))] px-5 py-4 text-[hsl(var(--primary-foreground))]">
            <Sparkles className="h-5 w-5" />
            <div>
              <p className="font-display text-lg font-bold leading-none">Karweer AI</p>
              <p className="text-xs opacity-80">Advisory intelligence engine</p>
            </div>
          </div>

          <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
            {messages.map((m, i) => (
              <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                <div
                  data-testid={`ai-msg-${m.role}`}
                  className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                    m.role === "user"
                      ? "bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]"
                      : "bg-secondary text-secondary-foreground"
                  }`}
                >
                  {m.text || <span className="opacity-50">…</span>}
                </div>
              </div>
            ))}
            {messages.length <= 1 && (
              <div className="space-y-2 pt-2">
                {SUGGESTIONS.map((s) => (
                  <button
                    key={s}
                    onClick={() => send(s)}
                    className="block w-full rounded-xl border border-border px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:border-[hsl(var(--primary))] hover:text-foreground"
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 border-t border-border p-3">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && send()}
              data-testid="ai-input"
              placeholder="Ask anything…"
              className="flex-1 rounded-full border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]"
            />
            <button
              onClick={() => send()}
              disabled={busy}
              data-testid="ai-send"
              className="grid h-10 w-10 place-items-center rounded-full bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}
