#!/usr/bin/env python3
"""PageSpeed Insights batch auditor for suriota.com priority pages.

Reads PSI_API_KEY from .env, runs mobile+desktop for each URL via PSI API v5,
saves raw JSON to audit/psi/<date>/<slug>-<strategy>.json (resumable: skips existing),
then prints a per-page scorecard + a cross-page opportunity matrix.

Usage:
  python audit/psi_audit.py                # fetch (if missing) + report
  python audit/psi_audit.py --report-only  # report from cached JSON, no API calls
  python audit/psi_audit.py --date 2026-06-02   # use a specific dated folder
"""
import json, os, sys, time, subprocess, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PSI = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
CATS = ["performance", "accessibility", "best-practices", "seo"]
STRATEGIES = ["mobile", "desktop"]

PAGES = [
    ("home", "https://suriota.com/"),
    ("modbus-gateway", "https://suriota.com/suriota-modbus-gateway/"),
    ("thm-30md", "https://suriota.com/thm-30md/"),
    ("pm1611-wd", "https://suriota.com/pm1611-wd/"),
    ("iso-m485-series", "https://suriota.com/iso-m485-series/"),
    ("spd-t485-105", "https://suriota.com/rs-485-surge-protector-spd-t485-105/"),
    ("waste-water-logger", "https://suriota.com/waste-water-logger/"),
    ("iiot-sys-integration", "https://suriota.com/industrial-iot-system-integration/"),
    ("system-integration", "https://suriota.com/system-integration/"),
    ("surge-saas", "https://suriota.com/surge-saas-platform/"),
]


def load_key():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("PSI_API_KEY="):
            return line.split("=", 1)[1].strip()
    sys.exit("PSI_API_KEY not found in .env")


def fetch(url, strategy, key, out):
    qs = {"url": url, "strategy": strategy, "key": key}
    full = PSI + "?" + urllib.parse.urlencode(qs) + "".join(f"&category={c}" for c in CATS)
    # curl (Cloudflare-safe UA not needed for googleapis; curl is fine)
    r = subprocess.run(["curl", "-s", full], capture_output=True, text=True)
    data = json.loads(r.stdout)
    if "error" in data:
        return False, data["error"].get("message", "unknown")[:120]
    out.write_text(json.dumps(data), encoding="utf-8")
    return True, "ok"


def cat_scores(lr):
    return {k: (round(v["score"] * 100) if v.get("score") is not None else None)
            for k, v in lr["categories"].items()}


def main():
    report_only = "--report-only" in sys.argv
    date = "2026-06-02"
    if "--date" in sys.argv:
        date = sys.argv[sys.argv.index("--date") + 1]
    outdir = ROOT / "audit" / "psi" / date
    outdir.mkdir(parents=True, exist_ok=True)
    key = None if report_only else load_key()

    # ---- fetch ----
    if not report_only:
        for slug, url in PAGES:
            for strat in STRATEGIES:
                f = outdir / f"{slug}-{strat}.json"
                if f.exists():
                    print(f"  skip (cached) {slug}-{strat}")
                    continue
                ok, msg = fetch(url, strat, key, f)
                print(f"  {'OK ' if ok else 'ERR'} {slug}-{strat}: {msg}")
                time.sleep(1.2)

    # ---- report ----
    print("\n================ SCORECARD (P=perf A=a11y B=best-practices S=seo) ================")
    print(f"{'page':24} {'strat':7} {'P':>4}{'A':>4}{'B':>4}{'S':>4}   LCP    TBT    CLS")
    opp_agg = {}  # title -> [count, total_ms]
    for slug, url in PAGES:
        for strat in STRATEGIES:
            f = outdir / f"{slug}-{strat}.json"
            if not f.exists():
                print(f"{slug:24} {strat:7}  (no data)")
                continue
            lr = json.loads(f.read_text(encoding="utf-8"))["lighthouseResult"]
            s = cat_scores(lr)
            au = lr["audits"]
            lcp = au.get("largest-contentful-paint", {}).get("displayValue", "-")
            tbt = au.get("total-blocking-time", {}).get("displayValue", "-")
            cls = au.get("cumulative-layout-shift", {}).get("displayValue", "-")
            def g(k):
                v = s.get(k)
                return f"{v:>4}" if v is not None else "   -"
            print(f"{slug:24} {strat:7} {g('performance')}{g('accessibility')}{g('best-practices')}{g('seo')}  "
                  f"{lcp:>5} {tbt:>6} {cls:>5}")
            for k, a in au.items():
                det = a.get("details", {})
                sc = a.get("score")
                if isinstance(det, dict) and det.get("type") == "opportunity" and sc is not None and sc < 1:
                    ms = det.get("overallSavingsMs", 0) or 0
                    e = opp_agg.setdefault(a.get("title", k), [0, 0.0])
                    e[0] += 1; e[1] += ms

    print("\n================ OPPORTUNITY MATRIX (across all page×strategy) ================")
    print(f"{'#hits':>5} {'tot_ms':>8}  opportunity")
    for title, (cnt, ms) in sorted(opp_agg.items(), key=lambda x: -x[1][1]):
        print(f"{cnt:>5} {int(ms):>8}  {title}")


if __name__ == "__main__":
    main()
