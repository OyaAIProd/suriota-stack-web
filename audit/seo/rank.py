#!/usr/bin/env python3
"""Keyword rank tracker via Google Custom Search JSON API.

Looks up where suriota.com appears (top 30 results) for each target keyword.
Uses CSE_API_KEY (or PSI_API_KEY) + GOOGLE_CSE_CX from .env. The Programmable
Search Engine MUST be set to "Search the entire web" for ranks to be meaningful.

CAVEAT: Custom Search ≠ exact organic SERP (no personalization/geo, different
index slice). Treat as a consistent *trend* signal, not ground truth. For true
positions, GSC `gsc.py queries` is authoritative. Quota: 100 queries/day free.

  python audit/seo/rank.py "industrial iot batam" "modbus gateway"
  python audit/seo/rank.py --file audit/seo/keywords.txt
  python audit/seo/rank.py --file audit/seo/keywords.txt --domain suriota.com --depth 30
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gauth as g

API = "https://www.googleapis.com/customsearch/v1"


def rank_for(key, cx, kw, domain, depth=30):
    import requests
    found = []
    for start in range(1, depth + 1, 10):  # 10 results per call
        r = requests.get(API, params={"key": key, "cx": cx, "q": kw,
                                       "num": 10, "start": start}, timeout=25)
        if r.status_code != 200:
            return None, f"HTTP {r.status_code} {r.text[:100]}"
        items = r.json().get("items", [])
        for j, it in enumerate(items):
            pos = start + j
            link = it.get("link", "")
            if domain in link:
                found.append((pos, link))
        if len(items) < 10:
            break
        time.sleep(0.2)
    return found, None


def main():
    a = sys.argv[1:]
    domain = "suriota.com"; depth = 30; kws = []
    i = 0
    while i < len(a):
        if a[i] == "--file":
            kws += [l.strip() for l in Path(a[i+1]).read_text(encoding="utf-8").splitlines()
                    if l.strip() and not l.startswith("#")]; i += 2
        elif a[i] == "--domain":
            domain = a[i+1]; i += 2
        elif a[i] == "--depth":
            depth = int(a[i+1]); i += 2
        else:
            kws.append(a[i]); i += 1
    if not kws:
        print(__doc__); return

    key = g._envval("CSE_API_KEY") or g._envval("PSI_API_KEY")
    cx = g._envval("GOOGLE_CSE_CX")
    if not cx:
        sys.exit("GOOGLE_CSE_CX not set in .env — create a Programmable Search Engine first "
                 "(see audit/seo/SETUP.md), set it to 'Search the entire web'.")

    print(f"\n=== Rank check: {domain} (top {depth}) — {len(kws)} keyword(s) ===")
    print(f"{'keyword':<42}{'rank':>6}  best URL")
    print("-" * 90)
    for kw in kws:
        found, err = rank_for(key, cx, kw, domain, depth)
        if err:
            print(f"{kw[:40]:<42}{'ERR':>6}  {err}"); continue
        if found:
            pos, url = sorted(found)[0]
            print(f"{kw[:40]:<42}{pos:>6}  {url[:42]}")
        else:
            print(f"{kw[:40]:<42}{'>'+str(depth):>6}  (not in top {depth})")


if __name__ == "__main__":
    main()
