import { useState, useRef, useEffect } from "react";
import { X, Send } from "lucide-react";
import api, { API } from "@/lib/api";

const WHATSAPP_NUMBER = "917208998944";
const REVERT_LINE = "\n\n— A member of Sudarshan's team will revert back to you shortly.";

const SUGGESTIONS = [
  "Renewable energy & storage advisory",
  "Green / climate financing & fundraising",
  "Business strategy, scaling & transformation",
];

function WhatsAppIcon({ className }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <path d="M17.47 14.38c-.3-.15-1.75-.86-2.02-.96-.27-.1-.47-.15-.67.15-.2.3-.77.96-.94 1.16-.17.2-.35.22-.64.07-.3-.15-1.25-.46-2.38-1.47-.88-.78-1.47-1.75-1.64-2.05-.17-.3-.02-.46.13-.6.13-.13.3-.35.44-.52.15-.17.2-.3.3-.5.1-.2.05-.37-.02-.52-.08-.15-.67-1.6-.92-2.2-.24-.58-.49-.5-.67-.5h-.57c-.2 0-.52.07-.8.37-.27.3-1.04 1.02-1.04 2.48s1.07 2.88 1.22 3.08c.15.2 2.1 3.2 5.08 4.49.71.3 1.26.49 1.69.63.71.22 1.36.19 1.87.12.57-.09 1.75-.72 2-1.4.24-.7.24-1.28.17-1.4-.07-.13-.27-.2-.57-.35z" />
      <path d="M12 2a10 10 0 0 0-8.5 15.3L2 22l4.8-1.5A10 10 0 1 0 12 2zm0 18.2a8.2 8.2 0 0 1-4.18-1.14l-.3-.18-2.85.9.9-2.78-.2-.32A8.2 8.2 0 1 1 12 20.2z" />
    </svg>
  );
}

export default function AIChatWidget() {
  const [open, setOpen] = useState(false);
  const [stage, setStage] = useState("capture"); // capture -> chat
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [savingLead, setSavingLead] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState([]);
  const sessionId = useRef("web-" + Math.random().toString(36).slice(2));
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, open, stage]);

  const startChat = async () => {
    if (!name.trim() || phone.trim().length < 7) return;
    setSavingLead(true);
    try {
      await api.post("/chat/lead", { name: name.trim(), phone: phone.trim() });
    } catch { /* still let them chat */ }
    setSavingLead(false);
    setStage("chat");
    setMessages([
      { role: "ai", text: `Lovely to meet you, ${name.trim().split(" ")[0]}! 👋 What are you exploring today? I can point you to the right service across renewable energy, green financing, fundraising, business strategy, scaling and transformation.` },
    ]);
  };

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
        body: JSON.stringify({ session_id: sessionId.current, message: `${q}\n\n(Context: prospect ${name} / ${phone}. Recommend the most relevant Sudarshan Karweer service and next step.)` }),
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
      // Close with the human-handoff assurance.
      setMessages((m) => {
        const copy = [...m];
        const last = copy[copy.length - 1];
        if (last?.role === "ai" && last.text && !last.text.includes("revert back")) {
          copy[copy.length - 1] = { ...last, text: last.text + REVERT_LINE };
        }
        return copy;
      });
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
      {/* WhatsApp quick chat */}
      <a
        href={`https://wa.me/${WHATSAPP_NUMBER}?text=${encodeURIComponent("Hi Sudarshan, I'd like to know more about your advisory services.")}`}
        target="_blank"
        rel="noopener noreferrer"
        data-testid="whatsapp-button"
        aria-label="Chat on WhatsApp"
        className="fixed bottom-6 left-6 z-[60] flex h-14 w-14 items-center justify-center rounded-full bg-[#25D366] text-white shadow-2xl transition-transform hover:-translate-y-1"
      >
        <WhatsAppIcon className="h-7 w-7" />
      </a>

      <button
        onClick={() => setOpen(!open)}
        data-testid="ai-widget-toggle"
        className="fixed bottom-6 right-6 z-[60] flex items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-4 py-3 font-semibold text-[hsl(var(--primary-foreground))] shadow-2xl transition-transform hover:-translate-y-1"
      >
        {open ? <X className="h-5 w-5" /> : <span className="font-display text-lg font-black leading-none">S<span className="text-[hsl(var(--accent))]">K.</span></span>}
        <span className="hidden sm:inline">{open ? "Close" : "Ask SK"}</span>
      </button>

      {open && (
        <div
          data-testid="ai-widget-panel"
          className="fixed bottom-24 right-6 z-[60] flex h-[34rem] w-[min(92vw,26rem)] flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-2xl"
        >
          <div className="flex items-center gap-3 border-b border-border bg-[hsl(var(--primary))] px-5 py-4 text-[hsl(var(--primary-foreground))]">
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-[hsl(var(--primary-foreground))] font-display text-base font-black text-[hsl(var(--primary))]">SK</span>
            <div>
              <p className="font-display text-lg font-bold leading-none">Ask SK</p>
              <p className="text-xs opacity-80">Sudarshan's advisory assistant</p>
            </div>
          </div>

          {stage === "capture" ? (
            <div className="flex flex-1 flex-col justify-center gap-4 p-6" data-testid="lead-capture">
              <div>
                <p className="font-display text-lg font-bold">Hi there 👋</p>
                <p className="mt-1 text-sm text-muted-foreground">I'm SK, Sudarshan's assistant. Tell me a little about you and I'll help you find the right advisory — someone from the team will also follow up.</p>
              </div>
              <input value={name} onChange={(e) => setName(e.target.value)} data-testid="lead-name" placeholder="Your name"
                className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <input value={phone} onChange={(e) => setPhone(e.target.value)} data-testid="lead-phone" placeholder="Contact number (with country code)" inputMode="tel"
                className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
              <button onClick={startChat} disabled={savingLead || !name.trim() || phone.trim().length < 7} data-testid="lead-start"
                className="w-full rounded-full bg-[hsl(var(--primary))] px-6 py-3 font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-50">
                {savingLead ? "Just a sec…" : "Start chatting"}
              </button>
              <p className="text-center text-[11px] text-muted-foreground">By continuing you agree to be contacted about your enquiry.</p>
            </div>
          ) : (
            <>
              <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto p-4">
                {messages.map((m, i) => (
                  <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
                    <div data-testid={`ai-msg-${m.role}`}
                      className={`max-w-[85%] whitespace-pre-line rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${m.role === "user" ? "bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]" : "bg-secondary text-secondary-foreground"}`}>
                      {m.text || <span className="opacity-50">…</span>}
                    </div>
                  </div>
                ))}
                {messages.length <= 1 && (
                  <div className="space-y-2 pt-2">
                    {SUGGESTIONS.map((s) => (
                      <button key={s} onClick={() => send(s)}
                        className="block w-full rounded-xl border border-border px-3 py-2 text-left text-xs text-muted-foreground transition-colors hover:border-[hsl(var(--primary))] hover:text-foreground">
                        {s}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="flex items-center gap-2 border-t border-border p-3">
                <input value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={(e) => e.key === "Enter" && send()}
                  data-testid="ai-input" placeholder="Tell me what you're exploring…"
                  className="flex-1 rounded-full border border-border bg-background px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-[hsl(var(--ring))]" />
                <button onClick={() => send()} disabled={busy} data-testid="ai-send"
                  className="grid h-10 w-10 place-items-center rounded-full bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5 disabled:opacity-50">
                  <Send className="h-4 w-4" />
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </>
  );
}
