"""Provision Stripe claimable sandbox + create consultation catalog. Prints keys as JSON."""
import os, json, urllib.request
import stripe

base = os.environ["INTEGRATION_PROXY_URL"]
job_id = "69d54eb7-07e1-4ffd-ad08-8725f9f9829e"
key = "sk-emergent-6Ba5358C8A9E1Ca673"

req = urllib.request.Request(
    base + "/stripe/sandboxes",
    data=json.dumps({"job_id": job_id}).encode(),
    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req) as r:
    sandbox = json.load(r)

stripe.api_key = sandbox["sandbox_secret_key"]
country = stripe.Account.retrieve()["country"]

CATALOG = [
    {"emergent_product_id": "sk_discovery_call", "name": "Discovery Call — 30 min",
     "tax_code": "txcd_10000000", "prices": [{"lookup_key": "sk_discovery", "amount": 9900, "currency": "usd"}]},
    {"emergent_product_id": "sk_strategy_session", "name": "1:1 Strategy Session — 60 min",
     "tax_code": "txcd_10000000", "prices": [{"lookup_key": "sk_strategy", "amount": 29900, "currency": "usd"}]},
    {"emergent_product_id": "sk_deep_dive", "name": "Deep-Dive Advisory — 90 min",
     "tax_code": "txcd_10000000", "prices": [{"lookup_key": "sk_deepdive", "amount": 59900, "currency": "usd"}]},
]


def get_or_create_product(entry):
    for p in stripe.Product.list(active=True).auto_paging_iter():
        if p.to_dict().get("metadata", {}).get("emergent_product_id") == entry["emergent_product_id"]:
            return p
    return stripe.Product.create(
        name=entry["name"], tax_code=entry.get("tax_code"),
        metadata={"managed_by": "emergent", "emergent_product_id": entry["emergent_product_id"]},
    )


for entry in CATALOG:
    product = get_or_create_product(entry)
    for p in entry["prices"]:
        existing = stripe.Price.list(lookup_keys=[p["lookup_key"]], active=True, limit=1).data
        if existing and (existing[0].unit_amount != p["amount"] or existing[0].currency != p["currency"]):
            stripe.Price.modify(existing[0].id, active=False)
            existing = []
        if not existing:
            stripe.Price.create(
                product=product.id, unit_amount=p["amount"], currency=p["currency"],
                lookup_key=p["lookup_key"], transfer_lookup_key=True,
            )

print("KEYS_JSON=" + json.dumps({
    "secret": sandbox["sandbox_secret_key"],
    "publishable": sandbox["sandbox_publishable_key"],
    "account": sandbox["sandbox_account_id"],
    "webhook": sandbox["preview_webhook_secret"],
    "onboarding_url": sandbox.get("onboarding_url", ""),
    "country": country,
}))
