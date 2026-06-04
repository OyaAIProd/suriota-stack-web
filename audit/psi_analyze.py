#!/usr/bin/env python3
"""Analyze full PSI scan JSON: scorecard + root-cause clustering across all pages.

Reads audit/psi/2026-06-03-full/*.json. Prints:
  - per-page scores (P/A/B/S) + LCP/CLS/TBT, sorted worst-first by Performance
  - counts >=90 per category
  - pages below 90 per category
  - opportunity/diagnostic clusters: which audits fail across the most pages + total wasted ms
"""
import json, sys
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "audit" / "psi" / "2026-06-03-full"

# audits worth clustering (opportunities + diagnostics)
OPP = ["largest-contentful-paint", "cumulative-layout-shift", "total-blocking-time",
       "render-blocking-resources", "unused-javascript", "unused-css-rules",
       "unminified-javascript", "unminified-css", "uses-responsive-images",
       "uses-optimized-images", "modern-image-formats", "offscreen-images",
       "uses-text-compression", "server-response-time", "redirects",
       "uses-long-cache-ttl", "dom-size", "third-party-summary",
       "duplicated-javascript", "legacy-javascript", "prioritize-lcp-image",
       "layout-shift-elements", "non-composited-animations"]


def sc(cats, k):
    s = cats.get(k, {}).get("score")
    return round(s * 100) if isinstance(s, (int, float)) else None


def main():
    rows = []
    # cluster: audit_id -> list of (page, savings_ms or value)
    fail_pages = defaultdict(list)
    save_ms = defaultdict(float)
    for f in sorted(DIR.glob("*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            lr = d["lighthouseResult"]; cats = lr["categories"]; a = lr["audits"]
        except Exception as e:
            rows.append((f.stem, None, None, None, None, "", "", "", "ERR")); continue
        P, A, B, S = sc(cats, "performance"), sc(cats, "accessibility"), sc(cats, "best-practices"), sc(cats, "seo")
        lcp = a.get("largest-contentful-paint", {}).get("displayValue", "")
        cls = a.get("cumulative-layout-shift", {}).get("displayValue", "")
        tbt = a.get("total-blocking-time", {}).get("displayValue", "")
        rows.append((f.stem, P, A, B, S, lcp, cls, tbt, ""))
        # clustering only on mobile (authoritative) + opportunities with score<0.9
        for aid in OPP:
            au = a.get(aid)
            if not au:
                continue
            ascore = au.get("score")
            # opportunity savings (ms)
            details = au.get("details", {}) or {}
            ov = details.get("overallSavingsMs") or au.get("numericValue") if aid in ("unused-javascript","unused-css-rules","render-blocking-resources","modern-image-formats","uses-responsive-images","server-response-time") else None
            if ascore is not None and ascore < 0.9:
                fail_pages[aid].append(f.stem)
                if isinstance(ov, (int, float)):
                    save_ms[aid] += ov

    rows.sort(key=lambda r: (999 if r[1] is None else r[1]))
    print("================ FULL SCORECARD (worst Perf first) ================")
    print(f"{'page-lang-strat':<46}{'P':>4}{'A':>4}{'B':>4}{'S':>4}  {'LCP':>7}{'CLS':>7}{'TBT':>8}")
    for r in rows:
        nm, P, A, B, S, lcp, cls, tbt, err = r
        if err:
            print(f"{nm:<46} {err}"); continue
        print(f"{nm:<46}{str(P):>4}{str(A):>4}{str(B):>4}{str(S):>4}  {lcp:>7}{cls:>7}{tbt:>8}")

    ok = [r for r in rows if r[8] != "ERR" and r[1] is not None]
    print("\n================ COVERAGE / PASS-RATE ================")
    labels = {1: "Performance", 2: "Accessibility", 3: "Best-Practices", 4: "SEO"}
    for idx, lab in labels.items():
        vals = [r[idx] for r in ok if r[idx] is not None]
        if vals:
            ge = sum(1 for v in vals if v >= 90)
            print(f"  {lab:<14} min={min(vals):>3} avg={sum(vals)//len(vals):>3}  >=90: {ge}/{len(vals)}  (fails: {len(vals)-ge})")
    print(f"  measured page×strategy: {len(ok)}  (mobile {sum(1 for r in ok if r[0].endswith('mobile'))}, desktop {sum(1 for r in ok if r[0].endswith('desktop'))})")

    print("\n================ BELOW-90 by category ================")
    for idx, lab in labels.items():
        bad = sorted([(r[idx], r[0]) for r in ok if r[idx] is not None and r[idx] < 90])
        if bad:
            print(f"\n  -- {lab} <90 ({len(bad)}) --")
            for v, nm in bad:
                print(f"     {v:>3}  {nm}")

    print("\n================ ROOT-CAUSE CLUSTERS (audit fails across N page×strat) ================")
    clust = sorted(fail_pages.items(), key=lambda kv: -len(kv[1]))
    for aid, pages in clust:
        ms = f"~{int(save_ms[aid])}ms tot" if save_ms[aid] else ""
        print(f"  {aid:<28} fails on {len(pages):>3} page×strat  {ms}")


if __name__ == "__main__":
    main()
