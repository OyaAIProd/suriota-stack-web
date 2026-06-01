"""GSC 'crawled-not-indexed' remediation (2026-06-01):
Add a SERVER-RENDERED "Related Projects" block to 4 orphan project posts + 4
sibling posts that link back (inbound). Strengthens internal linking, adds
topical context, and bumps `modified` -> sitemap lastmod -> triggers recrawl.

Reversible: each post's raw content is backed up before editing.
Idempotent: skips a post if the block marker already present.
"""
import os, json, re, pathlib
import requests
from requests.auth import HTTPBasicAuth

ENV = {}
for line in pathlib.Path(__file__).resolve().parents[2].joinpath(".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1)
        ENV[k.strip()] = v.strip()

BASE = "https://suriota.com/wp-json/wp/v2/posts"
AUTH = HTTPBasicAuth("admin", ENV["WP_APP_PASS"])
BK = pathlib.Path(__file__).resolve().parents[2] / "backups" / "2026-06-01" / "related-links"
BK.mkdir(parents=True, exist_ok=True)
MARKER = "sx-related-projects"

# orphan_id : list of 3 post IDs to link in its Related Projects block
BLOCKS = {
    1443: [2246, 1470, 1474],   # setup-ethernet-printer (electrical)
    1470: [1443, 2246, 1474],   # electrical-wiring-commissioning -> inbound to 1443
    2266: [2036, 1995, 1482],   # jasa-maintenance-webmail (IT/software)
    2036: [2266, 1995, 1482],   # pembuatan-website-sekolah -> inbound to 2266
    2022: [2122, 2115, 2015],   # surface-grinding (machining TEFA)
    2122: [2022, 2115, 2015],   # cnc-bubut-poros -> inbound to 2022
    1464: [2253, 1458, 1478],   # load-suppression (electrical eng)
    1458: [1464, 2253, 1478],   # schematic-programming-panel -> inbound to 1464
}

def get_post(pid, edit=False):
    params = {"_fields": "id,slug,title,content,link"}
    if edit:
        params["context"] = "edit"
    r = requests.get(f"{BASE}/{pid}", auth=AUTH, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

# resolve titles/links for every referenced id
ids = set(BLOCKS) | {i for v in BLOCKS.values() for i in v}
meta = {}
for pid in ids:
    p = get_post(pid)
    title = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", p["title"]["rendered"])).strip()
    meta[pid] = {"title": title, "url": p["link"]}
print(f"resolved {len(meta)} post titles")

def build_block(target_ids):
    items = "".join(
        f'<li style="margin:0;"><a href="{meta[t]["url"]}" '
        f'style="color:#0E2530;font:600 15px/1.45 \'Geist\',system-ui,sans-serif;text-decoration:none;">'
        f'{meta[t]["title"]} →</a></li>'
        for t in target_ids
    )
    return (
        '<!-- wp:html -->\n'
        f'<aside class="{MARKER}" style="margin:48px auto 8px;max-width:900px;padding:24px 0 0;'
        'border-top:1px solid #EAEFF1;">'
        '<p style="font:600 11px/1 \'Geist Mono\',ui-monospace,monospace;letter-spacing:.16em;'
        'text-transform:uppercase;color:#95A4AB;margin:0 0 14px;">Related Projects</p>'
        '<ul style="list-style:none;margin:0;padding:0;display:grid;gap:10px;">'
        f'{items}</ul></aside>\n'
        '<!-- /wp:html -->'
    )

for pid, targets in BLOCKS.items():
    p = get_post(pid, edit=True)
    raw = p["content"]["raw"]
    (BK / f"{pid}-before.html").write_text(raw, encoding="utf-8")
    if MARKER in raw:
        print(f"[{pid}] {p['slug']}: already has block, skip")
        continue
    new = raw.rstrip() + "\n\n" + build_block(targets)
    r = requests.post(f"{BASE}/{pid}", auth=AUTH, json={"content": new}, timeout=30)
    ok = r.status_code in (200, 201)
    j = r.json() if ok else {}
    print(f"[{pid}] {p['slug']}: status={r.status_code} modified={j.get('modified','?')} -> links {targets}")
    if not ok:
        print("   ERR:", r.text[:200])
