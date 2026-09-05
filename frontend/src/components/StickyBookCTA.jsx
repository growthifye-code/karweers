import { useState, useEffect } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { CalendarCheck, ArrowUpRight } from "lucide-react";
import { getAdminPath } from "@/config";

export default function StickyBookCTA() {
  const [show, setShow] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const onScroll = () => setShow(window.scrollY > 500);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  const hiddenPaths = ["/login", "/register", "/dashboard", getAdminPath(), "/booking/manage"];
  if (hiddenPaths.some((p) => location.pathname.startsWith(p))) return null;
  if (!show) return null;

  const goConsult = () => {
    if (location.pathname === "/") {
      document.getElementById("consult")?.scrollIntoView({ behavior: "smooth" });
    } else {
      navigate("/#consult");
    }
  };

  return (
    <button
      onClick={goConsult}
      data-testid="sticky-book-cta"
      className="group fixed bottom-6 left-1/2 z-[55] inline-flex -translate-x-1/2 items-center gap-2 rounded-full bg-[hsl(var(--primary))] px-6 py-3 text-sm font-semibold text-[hsl(var(--primary-foreground))] shadow-2xl ring-1 ring-black/5 transition-transform hover:-translate-y-0.5 hover:-translate-x-1/2"
    >
      <CalendarCheck className="h-4 w-4" />
      Book Consultation
      <ArrowUpRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
    </button>
  );
}
