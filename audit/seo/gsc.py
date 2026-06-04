#!/usr/bin/env python3
"""Google Search Console reporting for suriota.com (service-account auth).

Subcommands:
  python audit/seo/gsc.py queries [DAYS]      top search queries (default 28d)
  python audit/seo/gsc.py pages   [DAYS]      top landing pages
  python audit/seo/gsc.py opportunities [DAYS] high-impression / low-CTR queries (quick SEO wins)
  python audit/seo/gsc.py inspect <URL>       URL Inspection: index + rich-result status
  python audit/seo/gsc.py sitemaps            list submitted sitemaps + errors
  python audit/seo/gsc.py raw DIM1,DIM2 [DAYS]  custom Search Analytics (dims: query,page,country,device,date)

Dates use GSC's own lag (~2-3 days). All read-only except sitemap submit (not exposed here).
"""
import sys, json
from datetime import date, timedelta
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gauth as g

WM = "https://www.googleapis.com/webmasters/v3"
SC = "https://searchconsole.googleapis.com/v1"


def _range(days):
    end = date.today() - timedelta(days=2)
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def _query(s, site, body):
    import urllib.parse
    url = f"{WM}/sites/{urllib.parse.quote(site, safe='')}/searchAnalytics/query"
    r = s.post(url, json=body)
    if r.status_code != 200:
        sys.exit(f"GSC query failed: HTTP {r.status_code} {r.text[:200]}")
    return r.json().get("rows", [])


def _print_rows(rows, dim_label):
    print(f"{dim_label:<52}{'clicks':>8}{'impr':>9}{'CTR':>7}{'pos':>7}")
    print("-" * 83)
    for r in rows:
        k = " | ".join(r.get("keys", []))[:50]
        print(f"{k:<52}{int(r['clicks']):>8}{int(r['impressions']):>9}"
              f"{r['ctr']*100:>6.1f}%{r['position']:>7.1f}")


def cmd_queries(days=28):
    s, _ = g.session()
    rows = _query(s, g.gsc_site(),
                  {"startDate": _range(days)[0], "endDate": _range(days)[1],
                   "dimensions": ["query"], "rowLimit": 50})
    print(f"\n=== Top queries (last {days}d, GSC {g.gsc_site()}) ===")
    _print_rows(rows, "query")


def cmd_pages(days=28):
    s, _ = g.session()
    rows = _query(s, g.gsc_site(),
                  {"startDate": _range(days)[0], "endDate": _range(days)[1],
                   "dimensions": ["page"], "rowLimit": 50})
    print(f"\n=== Top pages (last {days}d) ===")
    _print_rows(rows, "page")


def cmd_opportunities(days=28):
    """High impressions but poor position (4-20) = pages a small push could rank."""
    s, _ = g.session()
    rows = _query(s, g.gsc_site(),
                  {"startDate": _range(days)[0], "endDate": _range(days)[1],
                   "dimensions": ["query"], "rowLimit": 250})
    opp = [r for r in rows if r["impressions"] >= 20 and 4 <= r["position"] <= 20]
    opp.sort(key=lambda r: r["impressions"], reverse=True)
    print(f"\n=== Quick-win queries (impr>=20, pos 4-20) — last {days}d ===")
    print("These rank on page 1-2 but not top 3; targeted content/links can lift them.\n")
    _print_rows(opp[:40], "query")
    print(f"\n{len(opp)} opportunity queries total.")


def cmd_inspect(url):
    s, _ = g.session()
    r = s.post(f"{SC}/urlInspection/index:inspect",
               json={"inspectionUrl": url, "siteUrl": g.gsc_site()})
    if r.status_code != 200:
        sys.exit(f"inspect failed: HTTP {r.status_code} {r.text[:200]}")
    res = r.json().get("inspectionResult", {})
    idx = res.get("indexStatusResult", {})
    print(f"\n=== URL Inspection: {url} ===")
    print(f"  Coverage     : {idx.get('coverageState','?')}")
    print(f"  Verdict      : {idx.get('verdict','?')}")
    print(f"  Indexing     : {idx.get('indexingState','?')}")
    print(f"  Last crawl   : {idx.get('lastCrawlTime','?')}")
    print(f"  Robots       : {idx.get('robotsTxtState','?')}")
    print(f"  Canonical(G) : {idx.get('googleCanonical','?')}")
    print(f"  Canonical(U) : {idx.get('userCanonical','?')}")
    rich = res.get("richResultsResult", {})
    if rich:
        det = rich.get("detectedItems", [])
        print(f"  Rich results : {rich.get('verdict','?')} "
              f"({', '.join(d.get('richResultType','?') for d in det) or 'none'})")
    mob = res.get("mobileUsabilityResult", {})
    if mob:
        print(f"  Mobile usable: {mob.get('verdict','?')}")


def cmd_sitemaps():
    import urllib.parse
    s, _ = g.session()
    site = g.gsc_site()
    r = s.get(f"{WM}/sites/{urllib.parse.quote(site, safe='')}/sitemaps")
    if r.status_code != 200:
        sys.exit(f"sitemaps failed: HTTP {r.status_code} {r.text[:200]}")
    print(f"\n=== Sitemaps ({site}) ===")
    for sm in r.json().get("sitemap", []):
        n = sm.get("contents", [{}])
        submitted = sm.get("lastSubmitted", "?")[:10]
        errs = sm.get("errors", 0); warns = sm.get("warnings", 0)
        print(f"  {sm['path']}\n    submitted {submitted}  errors={errs} warnings={warns}  "
              f"pending={sm.get('isPending', False)}")


def cmd_raw(dims, days=28):
    s, _ = g.session()
    rows = _query(s, g.gsc_site(),
                  {"startDate": _range(int(days))[0], "endDate": _range(int(days))[1],
                   "dimensions": dims.split(","), "rowLimit": 100})
    _print_rows(rows, dims)


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    cmd = a[0]
    if cmd == "queries":   cmd_queries(int(a[1]) if len(a) > 1 else 28)
    elif cmd == "pages":   cmd_pages(int(a[1]) if len(a) > 1 else 28)
    elif cmd == "opportunities": cmd_opportunities(int(a[1]) if len(a) > 1 else 28)
    elif cmd == "inspect": cmd_inspect(a[1])
    elif cmd == "sitemaps": cmd_sitemaps()
    elif cmd == "raw":     cmd_raw(a[1], a[2] if len(a) > 2 else 28)
    else: print(__doc__)


if __name__ == "__main__":
    main()
