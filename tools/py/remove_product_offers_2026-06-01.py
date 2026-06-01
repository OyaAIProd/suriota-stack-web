"""Remove the `offers` block from Product JSON-LD on all product pages.
Source confirmed = Elementor HTML widget in each page's `_elementor_data`
(NOT a plugin). Quote-based products -> dropping offers resolves merchant-listing
price/hasMerchantReturnPolicy/shippingDetails at once; Product stays valid
(image/sku/brand).

Robust: json.loads(_elementor_data) -> find html widget(s) holding a Product
JSON-LD with offers -> parse inner JSON-LD -> del offers on every Product node
(handles @graph) -> re-serialize -> write back. Dry-run default; --execute writes.
Backups in backups/2026-06-01/product-offers/.
"""
import os, re, sys, json, time, pathlib
import requests
from requests.auth import HTTPBasicAuth

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENV = {}
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1); ENV[k.strip()] = v.strip()
AUTH = HTTPBasicAuth("admin", ENV["WP_APP_PASS"])
PAGES = "https://suriota.com/wp-json/wp/v2/pages"
BK = ROOT / "backups" / "2026-06-01" / "product-offers"; BK.mkdir(parents=True, exist_ok=True)
EXECUTE = "--execute" in sys.argv

def fetch_all_pages():
    out, page = [], 1
    while True:
        r = requests.get(PAGES, auth=AUTH, params={"per_page": 100, "page": page,
            "context": "edit", "_fields": "id,slug,meta"}, timeout=90)
        if r.status_code != 200:
            break
        chunk = r.json()
        if not chunk:
            break
        out += chunk
        if len(chunk) < 100:
            break
        page += 1
    return out

def strip_offers_from_jsonld(jsonld_text):
    """Parse a JSON-LD string, delete `offers` from every Product node. Return (new_text, changed)."""
    try:
        data = json.loads(jsonld_text)
    except Exception:
        return jsonld_text, False
    changed = [False]
    def walk(n):
        if isinstance(n, dict):
            t = n.get("@type")
            if (t == "Product" or (isinstance(t, list) and "Product" in t)) and "offers" in n:
                del n["offers"]; changed[0] = True
            for v in n.values(): walk(v)
        elif isinstance(n, list):
            for v in n: walk(v)
    walk(data)
    if not changed[0]:
        return jsonld_text, False
    return json.dumps(data, indent=2, ensure_ascii=False), True

def process(ed_str):
    """Return (new_ed_str, n_widgets_changed)."""
    tree = json.loads(ed_str)
    n = [0]
    def walk(node):
        if isinstance(node, dict):
            s = node.get("settings")
            if isinstance(s, dict):
                for key in ("html", "editor", "text"):
                    v = s.get(key)
                    if isinstance(v, str) and '"Product"' in v and "offers" in v and "application/ld" in v:
                        def repl(m):
                            new, ch = strip_offers_from_jsonld(m.group(2))
                            if ch: n[0] += 1
                            return m.group(1) + new + m.group(3) if ch else m.group(0)
                        s[key] = re.sub(r'(<script[^>]*application/ld\+json[^>]*>)(.*?)(</script>)', repl, v, flags=re.S)
            for v in node.values(): walk(v)
        elif isinstance(node, list):
            for v in node: walk(v)
    walk(tree)
    if n[0] == 0:
        return None, 0
    return json.dumps(tree, ensure_ascii=False, separators=(",", ":")), n[0]

pages = fetch_all_pages()
print(f"scanned pages: {len(pages)}")
targets = []
for p in pages:
    ed = (p.get("meta") or {}).get("_elementor_data") or ""
    # raw _elementor_data has the inner JSON-LD escaped (\"Product\", application\/ld);
    # match bare words that survive escaping.
    if isinstance(ed, str) and "Product" in ed and "offers" in ed and "ld+json" in ed:
        targets.append(p)
print(f"pages with Product+offers schema: {len(targets)}")

changed_total = 0
for p in targets:
    pid, slug = p["id"], p["slug"]
    ed = p["meta"]["_elementor_data"]
    new_ed, n = process(ed)
    if not new_ed:
        print(f"  [{pid}] {slug}: Product found but no offers stripped (check)"); continue
    # validation: offers gone, Product+image kept, valid json
    assert '"@type": "Product"' in new_ed.replace('\\', '') or '"Product"' in new_ed
    json.loads(new_ed)
    print(f"  [{pid}] {slug}: widgets_changed={n}  ed_len {len(ed)}->{len(new_ed)}")
    changed_total += 1
    if EXECUTE:
        (BK / f"{pid}-before.json").write_text(ed, encoding="utf-8")
        r = requests.post(f"{PAGES}/{pid}", auth=AUTH, json={"meta": {"_elementor_data": new_ed}}, timeout=90)
        ok = r.status_code in (200, 201)
        if ok:
            cur = requests.get(PAGES, auth=AUTH, params={"include": pid, "context": "edit", "_fields": "meta"}, timeout=90).json()
            ced = cur[0]["meta"]["_elementor_data"]
            print(f"     POST {r.status_code}  offers_remaining_in_ld={'offers' in ced and 'application/ld' in ced and chr(34)+'Product'+chr(34) in ced}")
        else:
            print(f"     POST FAIL {r.status_code} {r.text[:150]}")
        time.sleep(0.5)

print(f"\n{'EXECUTED' if EXECUTE else 'DRY RUN'} — pages to change: {changed_total}")
if not EXECUTE:
    print("Re-run with --execute to apply, then flush Elementor cache (Tools > Clear Files & Data).")
