"""Default registry of every downloadable/collateral asset on the site.

Each entry is seeded (idempotently) into the `collateral` collection so the admin can
edit, upload, AI-generate and publish it. `key` is a stable identifier used to wire the
managed override back into the public download endpoints.
"""
from strategy_tools import STRATEGY_TOOLS

SITE = "https://www.sudarshankarweer.com"


def _tool_entries():
    out = []
    for t in STRATEGY_TOOLS:
        out.append({
            "key": f"tool:{t['slug']}",
            "kind": "pdf",
            "category": "Strategy Tool",
            "title": t["name"],
            "description": t.get("tagline", ""),
            "cta_label": "Download worksheet",
            "default_route": f"/api/strategy-tools/{t['slug']}.pdf",
            "locations": [
                {"page": "/strategy-tools", "label": "Strategy Tools page", "cta": "Download worksheet"},
            ],
            "source": "generated",
        })
    return out


def default_collateral(products=None):
    products = products or []
    items = [{
        "key": "tool-bundle",
        "kind": "pdf",
        "category": "Strategy Tool",
        "title": "Complete Strategy Toolkit (Bundle)",
        "description": "Every framework in one branded PDF.",
        "cta_label": "Download the full toolkit",
        "default_route": "/api/strategy-tools-bundle.pdf",
        "locations": [{"page": "/strategy-tools", "label": "Strategy Tools page", "cta": "Download full toolkit"}],
        "source": "generated",
    }]
    items += _tool_entries()

    items.append({
        "key": "leadmagnet:starter",
        "kind": "pdf",
        "category": "Lead Magnet",
        "title": "SK Leadership Blueprint (Starter)",
        "description": "The free starter blueprint delivered through the lead-magnet funnel.",
        "cta_label": "Get the free blueprint",
        "default_route": "/api/blueprint/starter.pdf",
        "locations": [
            {"page": "/", "label": "Homepage lead magnet", "cta": "Download free blueprint"},
            {"page": "/assessment", "label": "Assessment CTA", "cta": "Get your blueprint"},
        ],
        "source": "generated",
    })

    for p in products:
        items.append({
            "key": f"product:{p.get('slug')}",
            "kind": "ebook",
            "category": "Digital Product",
            "title": p.get("title", ""),
            "description": p.get("subtitle") or p.get("description", ""),
            "cta_label": "Buy & download",
            "price": p.get("price"),
            "default_route": p.get("download_url") or "",
            "locations": [{"page": "/products", "label": "Products / Store page", "cta": "Buy & download"}],
            "source": "manual" if not (p.get("download_url")) else "managed",
        })

    items.append({
        "key": "learning-hub",
        "kind": "video",
        "category": "Video",
        "title": "Learning Hub (curated videos)",
        "description": "Auto-curated YouTube learning feed. Add a specific featured video below if you want to spotlight one.",
        "cta_label": "Watch",
        "default_route": "",
        "external_url": f"{SITE}/learning",
        "locations": [{"page": "/learning", "label": "Learning Hub", "cta": "Watch"}],
        "source": "external",
    })
    items.append({
        "key": "library",
        "kind": "audio",
        "category": "Audio",
        "title": "Library (audiobooks & long-reads)",
        "description": "Auto-curated library shelf. Upload your own audio/long-read below to feature it.",
        "cta_label": "Open library",
        "default_route": "",
        "external_url": f"{SITE}/library",
        "locations": [{"page": "/library", "label": "Library", "cta": "Open"}],
        "source": "external",
    })
    return items
