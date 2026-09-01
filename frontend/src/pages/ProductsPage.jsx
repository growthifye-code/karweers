import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Download, ArrowUpRight, Check, Sparkles, Star } from "lucide-react";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import Seo from "@/components/Seo";
import api from "@/lib/api";
import BlueprintLeadMagnet from "@/components/BlueprintLeadMagnet";
import CommerceCheckoutModal from "@/components/CommerceCheckoutModal";

const inr = (v) => "\u20b9" + Number(v || 0).toLocaleString("en-IN");

export default function ProductsPage() {
  const [items, setItems] = useState([]);
  const [checkout, setCheckout] = useState(null);
  const [loading, setLoading] = useState(true);
  const [best, setBest] = useState({});
  const [params] = useSearchParams();
  const promoCode = params.get("code") || "";
  const autoProduct = params.get("product") || "";

  useEffect(() => {
    api.get("/products").then((r) => setItems(r.data)).catch(() => {}).finally(() => setLoading(false));
    api.get("/commerce/best-sellers").then((r) => setBest(r.data)).catch(() => {});
  }, []);

  useEffect(() => {
    if (autoProduct && items.length) {
      const p = items.find((x) => x.slug === autoProduct && x.type !== "blueprint");
      if (p) setCheckout({ kind: "product", ref_id: p.slug, title: p.title, price: p.price });
    }
  }, [autoProduct, items]);

  return (
    <div className="min-h-screen bg-background text-left text-foreground">
      <Seo title="Digital Downloads — Sudarshan Karweer" description="Premium playbooks, toolkits and the personalised Leadership Blueprint from Sudarshan Karweer." />
      <Navbar />
      <section className="grain relative overflow-hidden pt-40 lg:pt-48">
        <div className="pointer-events-none absolute -right-40 top-20 h-96 w-96 rounded-full bg-[hsl(var(--primary))] opacity-20 blur-[140px]" />
        <div className="relative mx-auto max-w-7xl px-6 pb-12 lg:px-10">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-[hsl(var(--primary))]">Playbooks & Toolkits</p>
          <h1 className="mt-4 max-w-3xl font-display text-4xl font-extrabold tracking-tight sm:text-5xl">The frameworks Sudarshan uses, in your hands.</h1>
          <p className="mt-5 max-w-2xl text-muted-foreground">Battle-tested playbooks and templates for strategy, capital and scaling — plus a personalised Leadership Blueprint built on your own profile.</p>
        </div>
      </section>

      <div className="mx-auto max-w-7xl px-6 pb-24 lg:px-10">
        <div className="mb-14"><BlueprintLeadMagnet /></div>

        {loading ? (
          <p className="py-16 text-center text-muted-foreground">Loading…</p>
        ) : (
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3" data-testid="products-grid">
            {items.map((p) => {
              const isBlueprint = p.type === "blueprint";
              return (
                <div key={p.slug} data-testid={`product-${p.slug}`} className="group relative flex flex-col rounded-3xl border border-border bg-card p-7 transition-all hover:-translate-y-1 hover:border-[hsl(var(--primary))]">
                  {best.product === p.slug && (
                    <span data-testid={`best-seller-${p.slug}`} className="absolute -top-3 right-6 inline-flex items-center gap-1 rounded-full bg-[hsl(var(--primary))] px-3 py-1 text-xs font-bold text-[hsl(var(--primary-foreground))] shadow-lg"><Star className="h-3.5 w-3.5" /> Most popular</span>
                  )}
                  {isBlueprint && (
                    <span className="mb-3 inline-flex w-fit items-center gap-1.5 rounded-full bg-[hsl(var(--primary))]/15 px-3 py-1 text-xs font-semibold text-[hsl(var(--primary))]"><Sparkles className="h-3.5 w-3.5" /> Personalised</span>
                  )}
                  <h3 className="font-display text-xl font-bold leading-tight">{p.title}</h3>
                  {p.subtitle && <p className="mt-1.5 text-sm font-medium text-[hsl(var(--primary))]">{p.subtitle}</p>}
                  <p className="mt-3 flex-1 text-sm leading-relaxed text-muted-foreground">{p.description}</p>
                  <div className="mt-6 flex items-center justify-between">
                    <span className="font-display text-2xl font-extrabold">{inr(p.price)}</span>
                    {isBlueprint ? (
                      <Link to="/assessment" data-testid={`product-cta-${p.slug}`} className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                        Take assessment <ArrowUpRight className="h-4 w-4" />
                      </Link>
                    ) : (
                      <button onClick={() => setCheckout({ kind: "product", ref_id: p.slug, title: p.title, price: p.price })} data-testid={`product-cta-${p.slug}`}
                        className="inline-flex items-center gap-1.5 rounded-full bg-[hsl(var(--primary))] px-5 py-2.5 text-sm font-semibold text-[hsl(var(--primary-foreground))] transition-transform hover:-translate-y-0.5">
                        Buy & download <Download className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  {isBlueprint && <p className="mt-3 flex items-center gap-1.5 text-xs text-muted-foreground"><Check className="h-3.5 w-3.5 text-[hsl(var(--primary))]" /> Built from your free Big-Five assessment</p>}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <CommerceCheckoutModal open={!!checkout} item={checkout} initialCode={promoCode} onClose={() => setCheckout(null)}
        onDone={(r) => { if (r.download_url) window.open(r.download_url, "_blank"); }} />
      <Footer />
    </div>
  );
}
