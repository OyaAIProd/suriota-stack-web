"""Related-Projects internal-link mesh for all 64 project posts.
See docs/superpowers/specs/2026-06-01-related-projects-mesh-design.md

Modes (SAFE BY DEFAULT):
  (no flag)    -> DRY RUN: compute + print plan, ZERO writes
  --execute    -> backup + append block + POST update (skips posts with marker)
  --revert     -> restore content.raw from backups/2026-06-01/related-links/

Guardrails: only 'post' type project posts; idempotent (marker); append-only;
per-post backup; per-post try/except; ~0.4s spacing.
"""
import os, re, sys, time, json, pathlib
from collections import defaultdict
import requests
from requests.auth import HTTPBasicAuth

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENV = {}
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1); ENV[k.strip()] = v.strip()

BASE = "https://suriota.com/wp-json/wp/v2/posts"
AUTH = HTTPBasicAuth("admin", ENV["WP_APP_PASS"])
BK = ROOT / "backups" / "2026-06-01" / "related-links"
BK.mkdir(parents=True, exist_ok=True)
MARKER = "sx-related-projects"
N_LINKS = 4
# Topical overrides for taxonomy-isolated posts (no shared category/tag).
# 1925 hybrid-PJU (solar+wind street lighting IoT) -> energy/IoT cluster.
OVERRIDE = {1925: [1869, 1468, 1460, 1476]}
MODE = "execute" if "--execute" in sys.argv else ("revert" if "--revert" in sys.argv else "dryrun")

def fetch_all():
    posts, page = [], 1
    while True:
        r = requests.get(BASE, auth=AUTH, params={
            "per_page": 100, "page": page, "context": "edit",
            "_fields": "id,slug,link,title,categories,tags,date,content"}, timeout=40)
        r.raise_for_status()
        chunk = r.json()
        if not chunk: break
        posts += chunk
        if len(chunk) < 100: break
        page += 1
    return posts

def norm(u): return u.rstrip("/")
def title_of(p): return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", p["title"]["rendered"])).strip()

def block_hrefs(raw):
    m = re.search(r'<aside class="%s".*?</aside>' % MARKER, raw, re.S)
    return re.findall(r'href="([^"]+)"', m.group(0)) if m else []

def build_block(targets, meta):
    items = "".join(
        f'<li style="margin:0;"><a href="{meta[t]["link"]}" '
        f"style=\"color:#0E2530;font:600 15px/1.45 'Geist',system-ui,sans-serif;text-decoration:none;\">"
        f'{meta[t]["title"]} →</a></li>' for t in targets)
    return ('<!-- wp:html -->\n'
        f'<aside class="{MARKER}" style="margin:48px auto 8px;max-width:900px;padding:24px 0 0;border-top:1px solid #EAEFF1;">'
        "<p style=\"font:600 11px/1 'Geist Mono',ui-monospace,monospace;letter-spacing:.16em;"
        'text-transform:uppercase;color:#95A4AB;margin:0 0 14px;">Related Projects</p>'
        '<ul style="list-style:none;margin:0;padding:0;display:grid;gap:10px;">'
        f'{items}</ul></aside>\n<!-- /wp:html -->')

def main():
    posts = fetch_all()
    by_id = {p["id"]: p for p in posts}
    link_to_id = {norm(p["link"]): p["id"] for p in posts}
    meta = {p["id"]: {"link": p["link"], "title": title_of(p), "slug": p["slug"]} for p in posts}
    cats = {p["id"]: set(p["categories"]) for p in posts}
    tags = {p["id"]: set(p["tags"]) for p in posts}
    date = {p["id"]: p["date"] for p in posts}
    has_block = {p["id"]: (MARKER in p["content"]["raw"]) for p in posts}
    ids = list(by_id)
    done = [i for i in ids if has_block[i]]
    todo = [i for i in ids if not has_block[i]]
    print(f"posts={len(ids)}  already-block={len(done)}  to-edit={len(todo)}")

    if MODE == "revert":
        n = 0
        for f in BK.glob("*-before.html"):
            pid = int(f.stem.split("-")[0])
            raw = f.read_text(encoding="utf-8")
            r = requests.post(f"{BASE}/{pid}", auth=AUTH, json={"content": raw}, timeout=40)
            print(f"  revert {pid}: {r.status_code}"); n += 1; time.sleep(0.4)
        print(f"reverted {n}"); return

    def related_for(pid):
        if pid in OVERRIDE:
            return [t for t in OVERRIDE[pid] if t in by_id][:N_LINKS]
        others = [q for q in ids if q != pid]
        same = [q for q in others if cats[q] & cats[pid]]
        same.sort(key=lambda q: (len(cats[q] & cats[pid]), len(tags[q] & tags[pid]), date[q]), reverse=True)
        chosen = same[:N_LINKS]
        if len(chosen) < N_LINKS:
            cset = {q for q in chosen}
            tm = [q for q in others if q not in cset and (tags[q] & tags[pid])]
            tm.sort(key=lambda q: (len(tags[q] & tags[pid]), date[q]), reverse=True)
            chosen += tm[:N_LINKS - len(chosen)]
        if len(chosen) < N_LINKS:  # defensive fallback: never emit <N_LINKS
            cset = set(chosen)
            rest = [q for q in others if q not in cset]
            rest.sort(key=lambda q: date[q], reverse=True)
            chosen += rest[:N_LINKS - len(chosen)]
        return chosen[:N_LINKS]

    outbound = {pid: related_for(pid) for pid in todo}

    # reciprocal inbound for OVERRIDE isolates: force up to 2 todo targets to link back
    for src, forced in OVERRIDE.items():
        if src not in todo:
            continue
        recip = [t for t in forced if t in outbound][:2]
        for t in recip:
            if src not in outbound[t]:
                outbound[t][-1] = src

    # inbound tally: existing blocks (done) + new outbound
    inbound = defaultdict(set)
    for pid in done:
        for h in block_hrefs(by_id[pid]["content"]["raw"]):
            t = link_to_id.get(norm(h))
            if t: inbound[t].add(pid)
    for src, tgts in outbound.items():
        for t in tgts: inbound[t].add(src)

    # balancing: ensure every post >=2 inbound by injecting into a todo donor
    def donor_for(pid):
        cands = [d for d in todo if d != pid and pid not in outbound[d]
                 and (cats[d] & cats[pid] or tags[d] & tags[pid])]
        # prefer donor whose current 4th link target still has >2 inbound after removal
        cands.sort(key=lambda d: (len(cats[d] & cats[pid]), len(tags[d] & tags[pid])), reverse=True)
        for d in cands:
            victim = outbound[d][-1]
            if len(inbound[victim]) > 2:
                return d, victim
        return (cands[0], outbound[cands[0]][-1]) if cands else (None, None)

    balanced = []
    for pid in ids:
        guard = 0
        while len(inbound[pid]) < 2 and guard < 6:
            guard += 1
            d, victim = donor_for(pid)
            if not d: break
            inbound[victim].discard(d)
            outbound[d][-1] = pid
            inbound[pid].add(d)
            balanced.append((d, victim, pid))

    # report
    print("\n=== PLAN (to-edit posts -> 4 related) ===")
    for pid in todo:
        names = " | ".join(meta[t]["slug"] for t in outbound[pid])
        print(f"[{pid}] {meta[pid]['slug'][:48]:48} -> {names}")
    if balanced:
        print("\n=== balancing swaps (donor: dropped -> injected) ===")
        for d, v, t in balanced:
            print(f"  [{d}] {meta[d]['slug'][:36]}: -{meta[v]['slug'][:28]} +{meta[t]['slug'][:28]}")
    under = [pid for pid in ids if len(inbound[pid]) < 2]
    dist = defaultdict(int)
    for pid in ids: dist[len(inbound[pid])] += 1
    print("\n=== inbound distribution (count -> #posts) ===")
    for k in sorted(dist): print(f"  {k} inbound: {dist[k]} posts")
    print(f"posts still <2 inbound: {len(under)}  {[meta[p]['slug'] for p in under]}")

    if MODE == "dryrun":
        print("\nDRY RUN — no writes. Re-run with --execute to apply.")
        return

    # EXECUTE
    print("\n=== EXECUTING ===")
    ok = fail = 0
    for pid in todo:
        try:
            raw = by_id[pid]["content"]["raw"]
            if MARKER in raw:
                print(f"[{pid}] skip (marker)"); continue
            (BK / f"{pid}-before.html").write_text(raw, encoding="utf-8")
            new = raw.rstrip() + "\n\n" + build_block(outbound[pid], meta)
            r = requests.post(f"{BASE}/{pid}", auth=AUTH, json={"content": new}, timeout=40)
            if r.status_code in (200, 201):
                ok += 1; print(f"[{pid}] OK {meta[pid]['slug'][:40]} mod={r.json().get('modified','?')}")
            else:
                fail += 1; print(f"[{pid}] FAIL {r.status_code} {r.text[:120]}")
            time.sleep(0.4)
        except Exception as e:
            fail += 1; print(f"[{pid}] EXC {e}")
    print(f"\ndone: ok={ok} fail={fail}")

if __name__ == "__main__":
    main()
