import { useEffect } from "react";

const SITE = "https://www.sudarshankarweer.com";
const DEFAULT_IMG = `${SITE}/og-cover.png`;

function upsert(selector, create) {
  let el = document.head.querySelector(selector);
  if (!el) { el = create(); document.head.appendChild(el); }
  return el;
}
function setMeta(name, content, attr = "name") {
  if (content == null) return;
  const el = upsert(`meta[${attr}="${name}"]`, () => {
    const m = document.createElement("meta"); m.setAttribute(attr, name); return m;
  });
  el.setAttribute("content", content);
}

export default function Seo({ title, description, jsonLd, image, path, type = "website", keywords }) {
  useEffect(() => {
    const url = SITE + (path || (typeof window !== "undefined" ? window.location.pathname : "/"));
    const img = image || DEFAULT_IMG;
    if (title) document.title = title;
    setMeta("description", description);
    if (keywords) setMeta("keywords", keywords);
    setMeta("robots", "index, follow, max-image-preview:large");
    // Open Graph
    setMeta("og:title", title, "property");
    setMeta("og:description", description, "property");
    setMeta("og:type", type, "property");
    setMeta("og:url", url, "property");
    setMeta("og:image", img, "property");
    setMeta("og:site_name", "Sudarshan Karweer", "property");
    // Twitter
    setMeta("twitter:card", "summary_large_image");
    setMeta("twitter:title", title);
    setMeta("twitter:description", description);
    setMeta("twitter:image", img);
    // Canonical
    const canonical = upsert('link[rel="canonical"]', () => {
      const l = document.createElement("link"); l.setAttribute("rel", "canonical"); return l;
    });
    canonical.setAttribute("href", url);

    let script;
    if (jsonLd) {
      script = document.createElement("script");
      script.type = "application/ld+json";
      script.text = JSON.stringify(jsonLd);
      document.head.appendChild(script);
    }
    return () => { if (script && script.parentNode) document.head.removeChild(script); };
  }, [title, description, jsonLd, image, path, type, keywords]);
  return null;
}
