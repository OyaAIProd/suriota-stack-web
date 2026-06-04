#!/usr/bin/env python3
"""Comprehensive PSI scanner for suriota.com — full-diagnostic coverage.

Covers every UNIQUE page/template: all EN pages + all blog posts (mobile+desktop)
+ a few ID/ZH spot-checks (ID/ZH mirror EN templates). Resumable (skips existing
JSON), retries on 429 with backoff, paced to stay gentle on origin + PSI quota.

URL list built from audit/_all_pages.json + audit/_all_posts.json (pulled via REST).
Reads PSI_API_KEY from .env. Saves raw JSON to audit/psi/<DATE>/<slug>-<strategy>.json.

Usage:
  python audit/psi_scan_full.py            # fetch missing + report
  python audit/psi_scan_full.py --report   # report only from cached JSON
"""
import json, os, sys, time, subprocess, urllib.parse, re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DATE = "2026-06-03-fixed-full"
OUT = ROOT / "audit" / "psi" / DATE
OUT.mkdir(parents=True, exist_ok=True)
PSI = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
CATS = ["performance", "accessibility", "best-practices", "seo"]
STRATEGIES = ["mobile", "desktop"]
PACE = 3  # seconds between calls (gentle)


def load_key():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("PSI_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("PSI_API_KEY not found in .env")


def lang_of(u):
    p = urlparse(u).path
    if p.startswith("/id/") or p == "/id": return "id"
    if p.startswith("/zh/") or p == "/zh": return "zh"
    return "en"


def slug_of(u):
    p = urlparse(u).path.strip("/")
    s = re.sub(r"[^a-z0-9]+", "-", p.lower()).strip("-") or "home"
    return s[:60]


def build_urls():
    pages = json.load(open(ROOT / "audit/_all_pages.json", encoding="utf-8"))
    posts = json.load(open(ROOT / "audit/_all_posts.json", encoding="utf-8"))
    urls = []
    seen = set()
    # all EN pages
    for p in pages:
        if lang_of(p["link"]) == "en":
            urls.append(p["link"])
    # all posts (EN)
    for p in posts:
        urls.append(p["link"])
    # 6 ID/ZH spot-checks of key pages
    spot = ["/id/beranda/", "/zh/shouye/",
            "/id/suriota-modbus-gateway-id/", "/zh/modbus-gateway/",
            "/id/iot-industri-integrasi-sistem/", "/zh/gongye-wulianwang-jicheng/"]
    # only add spot-checks that actually exist among page links
    pagelinks = {urlparse(p["link"]).path: p["link"] for p in pages}
    for sp in spot:
        if sp in pagelinks:
            urls.append(pagelinks[sp])
    # dedup preserve order
    out = []
    for u in urls:
        if u not in seen:
            seen.add(u); out.append(u)
    return out


def jobname(url, strat):
    return f"{slug_of(url)}-{lang_of(url)}-{strat}"


def fetch(url, strategy, key, dest):
    qs = {"url": url, "strategy": strategy, "key": key}
    full = PSI + "?" + urllib.parse.urlencode(qs) + "".join(f"&category={c}" for c in CATS)
    for attempt in range(4):
        r = subprocess.run(["curl", "-s", "--max-time", "120", full],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        out = r.stdout or ""
        try:
            data = json.loads(out)
        except Exception:
            data = {}
        if "lighthouseResult" in data:
            dest.write_text(json.dumps(data), encoding="utf-8")
            return "ok"
        err = data.get("error", {}).get("code") if isinstance(data, dict) else None
        if err == 429 or "rateLimitExceeded" in out or "RESOURCE_EXHAUSTED" in out:
            wait = 30 * (attempt + 1)
            print(f"     429 — backoff {wait}s (attempt {attempt+1})", flush=True)
            time.sleep(wait)
            continue
        return f"err:{(out[:120] or 'empty')}"
    return "err:429-exhausted"


def score(audits_cats, cat):
    s = audits_cats.get(cat, {}).get("score")
    return round(s * 100) if isinstance(s, (int, float)) else None


def report():
    rows = []
    for f in sorted(OUT.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            lr = d["lighthouseResult"]
            cats = lr["categories"]
            a = lr["audits"]
            rows.append({
                "name": f.stem,
                "P": score(cats, "performance"), "A": score(cats, "accessibility"),
                "B": score(cats, "best-practices"), "S": score(cats, "seo"),
                "LCP": a.get("largest-contentful-paint", {}).get("displayValue", ""),
                "CLS": a.get("cumulative-layout-shift", {}).get("displayValue", ""),
                "TBT": a.get("total-blocking-time", {}).get("displayValue", ""),
            })
        except Exception as e:
            rows.append({"name": f.stem, "err": str(e)[:40]})
    print("\n================ FULL SCORECARD ================")
    print(f"{'page-lang-strat':<48}{'P':>4}{'A':>4}{'B':>4}{'S':>4}  {'LCP':>7} {'CLS':>6} {'TBT':>8}")
    for r in rows:
        if "err" in r:
            print(f"{r['name']:<48} ERR {r['err']}"); continue
        print(f"{r['name']:<48}{str(r['P']):>4}{str(r['A']):>4}{str(r['B']):>4}{str(r['S']):>4}  "
              f"{r['LCP']:>7} {r['CLS']:>6} {r['TBT']:>8}")
    # summary
    ok = [r for r in rows if "err" not in r and r["P"] is not None]
    for cat in ["P", "A", "B", "S"]:
        vals = [r[cat] for r in ok if r[cat] is not None]
        if vals:
            ge90 = sum(1 for v in vals if v >= 90)
            print(f"  {cat}: min={min(vals)} avg={sum(vals)//len(vals)} >=90: {ge90}/{len(vals)}")
    print(f"  total measured: {len(ok)}")


def main():
    if "--report" in sys.argv:
        report(); return
    key = load_key()
    urls = build_urls()
    jobs = [(u, s) for u in urls for s in STRATEGIES]
    todo = [(u, s) for (u, s) in jobs if not (OUT / f"{jobname(u,s)}.json").exists()]
    print(f"URLs={len(urls)} jobs={len(jobs)} todo={len(todo)} (cached={len(jobs)-len(todo)})", flush=True)
    for i, (u, s) in enumerate(todo, 1):
        dest = OUT / f"{jobname(u,s)}.json"
        res = fetch(u, s, key, dest)
        print(f"  [{i}/{len(todo)}] {jobname(u,s):<46} {res}", flush=True)
        time.sleep(PACE)
    report()


if __name__ == "__main__":
    main()
