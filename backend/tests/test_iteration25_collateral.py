"""
Iteration 25 - Collateral & Downloads admin manager tests.
Covers: list/counts, upload, publish/unpublish override, edit metadata, create/delete custom,
public file serving, ansoff-matrix.pdf non-empty regression, AI-generate scheduling.
"""
import io
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://energy-strategy-hub.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "sudarshan@karweers.com"
ADMIN_PASSWORD = "Sudarshan@2026"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD, "captcha_token": "x", "consent": True},
        timeout=30,
    )
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


def _list(auth_headers):
    r = requests.get(f"{BASE_URL}/api/admin/collateral", headers=auth_headers, timeout=30)
    assert r.status_code == 200, r.text[:200]
    return r.json()


# ---------- List / counts ----------
def test_collateral_list_and_counts(auth_headers):
    data = _list(auth_headers)
    assert data["total"] >= 18
    counts = data["counts"]
    for k in ["Strategy Tool", "Digital Product", "Lead Magnet"]:
        assert k in counts, f"missing category {k}"
    assert counts["Strategy Tool"] >= 10
    it = data["items"][0]
    for f in ["id", "key", "kind", "category", "title", "live", "version", "locations"]:
        assert f in it, f"item missing field {f}"


# ---------- Ansoff PDF non-empty regression ----------
def test_ansoff_matrix_pdf_nonempty():
    r = requests.get(f"{BASE_URL}/api/strategy-tools/ansoff-matrix.pdf", timeout=30)
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("application/pdf")
    assert len(r.content) > 1000, f"ansoff PDF too small: {len(r.content)} bytes"
    assert r.content[:4] == b"%PDF"


# ---------- Upload + publish + override + unpublish flow ----------
@pytest.fixture(scope="module")
def five_whys_item(auth_headers):
    data = _list(auth_headers)
    items = data["items"]
    target = next((i for i in items if i.get("key") == "tool:five-whys"), None)
    if not target:
        target = next((i for i in items if i.get("category") == "Strategy Tool" and (i.get("key") or "").startswith("tool:")), None)
    assert target, "no strategy_tool item found"
    return target


def test_upload_publish_override_unpublish(auth_headers, five_whys_item):
    cid = five_whys_item["id"]
    key = five_whys_item.get("key", "")
    slug = key.split(":", 1)[1] if ":" in key else None
    assert slug, "no slug on strategy tool"

    baseline = requests.get(f"{BASE_URL}/api/strategy-tools/{slug}.pdf", timeout=30)
    assert baseline.status_code == 200
    assert len(baseline.content) > 500

    fake_pdf = b"%PDF-1.4\n% test override\n" + b"A" * 200 + b"\n%%EOF"
    files = {"file": ("override.pdf", io.BytesIO(fake_pdf), "application/pdf")}
    up = requests.post(
        f"{BASE_URL}/api/admin/collateral/{cid}/upload",
        headers=auth_headers,
        files=files,
        timeout=60,
    )
    assert up.status_code == 200, up.text[:300]
    up_data = up.json()
    assert up_data.get("has_file") is True
    assert up_data.get("version", 0) >= 1

    pub = requests.post(
        f"{BASE_URL}/api/admin/collateral/{cid}/publish",
        headers=auth_headers,
        json={"notify": False},
        timeout=30,
    )
    assert pub.status_code == 200, pub.text[:300]
    pdata = pub.json()
    assert pdata.get("live") is True
    assert pdata.get("serving_managed_file") is True

    override_get = requests.get(f"{BASE_URL}/api/strategy-tools/{slug}.pdf", timeout=30)
    assert override_get.status_code == 200
    assert override_get.content == fake_pdf, "public strategy-tool endpoint did not serve override"

    pub_file = requests.get(f"{BASE_URL}/api/collateral/{cid}/file", timeout=30)
    assert pub_file.status_code == 200
    assert pub_file.content == fake_pdf

    unpub = requests.post(
        f"{BASE_URL}/api/admin/collateral/{cid}/unpublish",
        headers=auth_headers,
        timeout=30,
    )
    assert unpub.status_code == 200
    assert unpub.json().get("live") is False

    revert = requests.get(f"{BASE_URL}/api/strategy-tools/{slug}.pdf", timeout=30)
    assert revert.status_code == 200
    assert revert.content != fake_pdf, "did not revert to generated PDF"
    assert revert.content[:4] == b"%PDF"


# ---------- Public file endpoint gated by live=false ----------
def test_public_file_offline_gated(auth_headers, five_whys_item):
    cid = five_whys_item["id"]
    r = requests.get(f"{BASE_URL}/api/collateral/{cid}/file", timeout=30)
    assert r.status_code in (403, 404), f"expected gate when offline, got {r.status_code}"


# ---------- Edit metadata ----------
def test_edit_metadata(auth_headers):
    data = _list(auth_headers)
    target = next((i for i in data["items"] if i.get("category") == "Strategy Tool"), None)
    assert target
    cid = target["id"]
    original_title = target["title"]
    new_title = original_title + " (edited)"
    patch = requests.patch(
        f"{BASE_URL}/api/admin/collateral/{cid}",
        headers=auth_headers,
        json={"title": new_title, "description": "test edit desc", "cta_label": "Grab it"},
        timeout=30,
    )
    assert patch.status_code == 200, patch.text[:300]
    assert patch.json().get("title") == new_title
    requests.patch(
        f"{BASE_URL}/api/admin/collateral/{cid}",
        headers=auth_headers,
        json={"title": original_title},
        timeout=30,
    )


def test_edit_product_price_syncs(auth_headers):
    data = _list(auth_headers)
    prod = next((i for i in data["items"] if (i.get("key") or "").startswith("product:")), None)
    if not prod:
        pytest.skip("no digital_product collateral present")
    cid = prod["id"]
    slug = prod["key"].split(":", 1)[1]
    prods = requests.get(f"{BASE_URL}/api/products", timeout=30)
    if prods.status_code != 200:
        pytest.skip("public /api/products not available")
    pj = prods.json()
    pr_list = pj if isinstance(pj, list) else pj.get("items", [])
    match = next((p for p in pr_list if p.get("slug") == slug), None)
    if not match:
        pytest.skip("no matching product for collateral")
    original_price = match.get("price")
    new_price = float(original_price or 0) + 1
    patch = requests.patch(
        f"{BASE_URL}/api/admin/collateral/{cid}",
        headers=auth_headers,
        json={"price": new_price},
        timeout=30,
    )
    assert patch.status_code == 200, patch.text[:300]
    prods2 = requests.get(f"{BASE_URL}/api/products", timeout=30).json()
    pr_list2 = prods2 if isinstance(prods2, list) else prods2.get("items", [])
    match2 = next((p for p in pr_list2 if p.get("slug") == slug), None)
    assert match2 and abs(float(match2.get("price")) - new_price) < 0.001, "product price did not sync"
    requests.patch(
        f"{BASE_URL}/api/admin/collateral/{cid}",
        headers=auth_headers,
        json={"price": original_price},
        timeout=30,
    )


# ---------- Create + Delete custom, plus built-in delete guard ----------
def test_create_and_delete_custom(auth_headers):
    payload = {
        "title": "TEST_custom_asset",
        "kind": "pdf",
        "category": "Lead Magnet",
        "description": "test description",
        "cta_label": "Download",
    }
    r = requests.post(f"{BASE_URL}/api/admin/collateral", headers=auth_headers, json=payload, timeout=30)
    assert r.status_code in (200, 201), r.text[:300]
    created = r.json()
    cid = created["id"]
    assert created.get("origin") == "custom"
    d = requests.delete(f"{BASE_URL}/api/admin/collateral/{cid}", headers=auth_headers, timeout=30)
    assert d.status_code in (200, 204), d.text[:200]


def test_builtin_delete_forbidden(auth_headers):
    data = _list(auth_headers)
    builtin = next((i for i in data["items"] if i.get("origin") != "custom"), None)
    if not builtin:
        pytest.skip("no built-in items")
    d = requests.delete(f"{BASE_URL}/api/admin/collateral/{builtin['id']}", headers=auth_headers, timeout=30)
    assert d.status_code == 400, f"expected 400 for built-in delete, got {d.status_code}"


# ---------- AI generate: schedule + poll (limited) ----------
def test_ai_generate_schedules(auth_headers):
    data = _list(auth_headers)
    target = next((i for i in data["items"] if i.get("kind") == "pdf"), None)
    assert target
    cid = target["id"]
    r2 = requests.post(
        f"{BASE_URL}/api/admin/collateral/{cid}/ai-generate",
        headers=auth_headers,
        json={"instructions": "Short 1-page test outline. Do not exceed 200 words."},
        timeout=30,
    )
    assert r2.status_code == 200, r2.text[:300]
    assert r2.json().get("gen_status") in ("running", "queued", "done")
    reached = None
    for _ in range(10):
        time.sleep(5)
        lst = _list(auth_headers)
        it = next((i for i in lst["items"] if i["id"] == cid), None)
        if it and it.get("gen_status") in ("done", "error"):
            reached = it.get("gen_status")
            break
    assert reached != "error", "AI generation errored"
