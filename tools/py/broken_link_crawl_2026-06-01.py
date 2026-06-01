"""Site-wide broken-link crawl for suriota.com.
1. Read all URLs from sitemaps (post + page).
2. Fetch each page, extract <a href> links.
3. Dedupe links (internal + external), track which source pages contain each.
4. HTTP-check every unique link (HEAD->GET fallback, follow redirects).
5. Report: broken internal (4xx/5xx), broken external, internal links that redirect.
Read-only. No writes.
"""
import re, sys, json, time, pathlib
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import requests

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"}
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "backups" / "2026-06-01" / "broken-link-crawl.json"
OUT.parent.mkdir(parents=True, exist_ok=True)
SITE = "suriota.com"

def get(url, method="GET", timeout=25):
    return requests.request(method, url, headers=UA, timeout=timeout, allow_redirects=True, stream=True)

# 1. sitemap pages
idx = requests.get("https://suriota.com/sitemap.xml", headers=UA, timeout=30).text
subs = re.findall(r'<loc><!\[CDATA\[([^\]]+)\]\]>', idx)
pages = []
for s in subs:
    sm = requests.get(s, headers=UA, timeout=30).text
    pages += re.findall(r'<loc><!\[CDATA\[([^\]]+)\]\]>', sm)
pages = sorted(set(pages))
print(f"pages from sitemap: {len(pages)}")

# 2-3. crawl pages, extract links, track sources
link_sources = defaultdict(set)
def crawl(pg):
    try:
        html = get(pg).text
    except Exception as e:
        return pg, []
    hrefs = re.findall(r'<a\b[^>]*?href=["\']([^"\']+)["\']', html, re.I)
    out = []
    for h in hrefs:
        h = h.strip()
        if h.startswith(("mailto:", "tel:", "javascript:", "#", "data:", "whatsapp:")):
            continue
        if h.startswith("//"): h = "https:" + h
        if h.startswith("/"): h = "https://suriota.com" + h
        if not h.startswith("http"): continue
        h = h.split("#")[0].rstrip("/") or h
        out.append(h)
    return pg, out

with ThreadPoolExecutor(max_workers=8) as ex:
    for pg, links in ex.map(crawl, pages):
        for l in links:
            link_sources[l].add(pg)
print(f"unique links extracted: {len(link_sources)}")

# 4. check each unique link
def check(url):
    try:
        r = get(url, method="HEAD", timeout=20)
        if r.status_code in (405, 501, 403) or r.status_code >= 400:
            r = get(url, method="GET", timeout=25)
        final = r.url.rstrip("/")
        return url, r.status_code, final
    except Exception as e:
        return url, -1, type(e).__name__

results = {}
links = list(link_sources)
with ThreadPoolExecutor(max_workers=10) as ex:
    for url, code, final in ex.map(check, links):
        results[url] = (code, final)

# 5. classify
broken_int, broken_ext, redir_int, errors = [], [], [], []
for url, (code, final) in results.items():
    internal = SITE in url
    src = sorted(link_sources[url])
    rec = {"url": url, "code": code, "final": final, "n_src": len(src), "src": src[:3]}
    if code == -1:
        (errors).append(rec)
    elif code >= 400:
        (broken_int if internal else broken_ext).append(rec)
    elif internal and isinstance(final, str) and final.rstrip("/") != url.rstrip("/"):
        redir_int.append(rec)

OUT.write_text(json.dumps({"broken_int": broken_int, "broken_ext": broken_ext,
    "redir_int": redir_int, "errors": errors}, indent=2), encoding="utf-8")

def show(title, items):
    print(f"\n=== {title}: {len(items)} ===")
    for r in sorted(items, key=lambda x: -x["n_src"])[:60]:
        print(f"  [{r['code']}] {r['url']}  (on {r['n_src']} pages)" + (f" -> {r['final']}" if r['code'] not in (-1,) and str(r['final'])!=r['url'] else ""))
        for s in r["src"][:2]: print(f"        src: {s}")

print(f"\nchecked {len(results)} unique links")
show("BROKEN internal (4xx/5xx)", broken_int)
show("BROKEN external (4xx/5xx)", broken_ext)
show("UNREACHABLE (timeout/DNS/SSL)", errors)
show("Internal links that REDIRECT (301/302)", redir_int)
print(f"\nfull report: {OUT}")
