#!/usr/bin/env python3
"""Google Indexing API — nudge Google to (re)crawl suriota URLs.

Use after we change schema / redirects / content / perf on pages so Google
re-fetches sooner. Officially scoped to JobPosting/BroadcastEvent pages, but
URL_UPDATED notifications are accepted for any URL on a verified property where
the SA is an *owner*. Quota: 200 URLs/day (default).

  python audit/seo/indexing.py push <url> [url2 ...]   notify URL_UPDATED
  python audit/seo/indexing.py push-file <path>        one URL per line
  python audit/seo/indexing.py status <url>            last notification status
  python audit/seo/indexing.py remove <url>            notify URL_DELETED
"""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gauth as g

PUB = "https://indexing.googleapis.com/v3/urlNotifications:publish"
META = "https://indexing.googleapis.com/v3/urlNotifications/metadata"


def _publish(s, url, typ):
    r = s.post(PUB, json={"url": url, "type": typ})
    if r.status_code == 200:
        return "ok"
    return f"HTTP {r.status_code} {r.text[:140]}"


def cmd_push(urls, typ="URL_UPDATED"):
    s, email = g.session(scopes=["https://www.googleapis.com/auth/indexing"])
    print(f"Notifying {len(urls)} URL(s) as {typ} (SA={email})\n")
    ok = 0
    for i, u in enumerate(urls, 1):
        res = _publish(s, u, typ)
        print(f"  [{i}/{len(urls)}] {res:<12} {u}")
        ok += res == "ok"
        time.sleep(0.3)
    print(f"\n{ok}/{len(urls)} accepted. (Acceptance != indexed; check later with gsc.py inspect)")


def cmd_status(url):
    s, _ = g.session(scopes=["https://www.googleapis.com/auth/indexing"])
    r = s.get(META, params={"url": url})
    if r.status_code == 404:
        print(f"No prior notification for {url}"); return
    if r.status_code != 200:
        sys.exit(f"status failed: HTTP {r.status_code} {r.text[:160]}")
    d = r.json()
    print(f"=== {url} ===")
    for k in ("latestUpdate", "latestRemove"):
        if k in d:
            print(f"  {k}: type={d[k].get('type')} at={d[k].get('notifyTime','?')}")


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    if a[0] == "push":
        if len(a) < 2: sys.exit("usage: push <url> [url2 ...]")
        cmd_push(a[1:])
    elif a[0] == "push-file":
        urls = [l.strip() for l in Path(a[1]).read_text(encoding="utf-8").splitlines()
                if l.strip() and not l.startswith("#")]
        cmd_push(urls)
    elif a[0] == "status":
        cmd_status(a[1])
    elif a[0] == "remove":
        cmd_push(a[1:], typ="URL_DELETED")
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
