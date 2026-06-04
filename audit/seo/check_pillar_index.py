#!/usr/bin/env python3
"""Check Google index status of the 3 commissioning pillar URLs.

Uses the GSC URL Inspection API (via the SEO toolkit's OAuth creds) to report
coverage/verdict per URL. Prints a one-line SUMMARY the caller (cron/loop) can
grep: "ALL INDEXED" when every URL is indexed, else "PENDING n/3".

  python audit/seo/check_pillar_index.py
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gauth as g

SEO = Path(__file__).resolve().parent
STATE = SEO / "_index_watch_state.json"
LOG = SEO / "index_watch.log"
TASK_NAME = "SuriotaPillarIndexCheck"  # Windows Task Scheduler name (for self-disable)

URLS = [
    "https://suriota.com/id/commissioning-adalah/",
    "https://suriota.com/what-is-commissioning/",
    "https://suriota.com/zh/shenme-shi-diaoshi/",
]
SITE = "https://suriota.com/"  # URL-prefix property (has the data)


def inspect_all():
    s, _ = g.session()  # default granted scopes (webmasters + indexing + analytics)
    results = {}
    for u in URLS:
        r = s.post("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
                   json={"inspectionUrl": u, "siteUrl": SITE})
        if r.status_code != 200:
            results[u] = {"indexed": False, "coverage": f"ERR HTTP {r.status_code}",
                          "verdict": "?", "last": "?"}
            continue
        res = r.json().get("inspectionResult", {}).get("indexStatusResult", {})
        cov = res.get("coverageState", "?")
        is_idx = ("indexed" in cov.lower()) and ("not" not in cov.lower())
        results[u] = {"indexed": is_idx, "coverage": cov,
                      "verdict": res.get("verdict", "?"), "last": res.get("lastCrawlTime", "never")}
    return results


def render(results):
    indexed = sum(1 for v in results.values() if v["indexed"])
    lines = ["=== Commissioning pillars — index status ==="]
    for u, v in results.items():
        lines.append(f"  [{'INDEXED' if v['indexed'] else 'pending'}] {u}")
        lines.append(f"           coverage={v['coverage']!r} verdict={v['verdict']} lastCrawl={v['last']}")
    total = len(results)
    lines.append(f"SUMMARY: {'ALL INDEXED' if indexed==total else 'PENDING'} {indexed}/{total} indexed")
    return "\n".join(lines), indexed, total


def _notify(title, msg):
    """Best-effort Windows desktop notification (msg.exe), never fatal."""
    try:
        subprocess.run(["msg", "*", "/TIME:120", f"{title}\n{msg}"],
                       timeout=15, capture_output=True)
    except Exception:
        pass


def _self_disable():
    try:
        subprocess.run(["schtasks", "/Change", "/TN", TASK_NAME, "/DISABLE"],
                       timeout=15, capture_output=True)
    except Exception:
        pass


def main():
    watch = "--watch" in sys.argv
    results = inspect_all()
    text, indexed, total = render(results)
    print(text)

    if not watch:
        return 0 if indexed == total else 1

    # --watch: compare to prior state, log, notify only on meaningful change
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    prev = {}
    if STATE.exists():
        try:
            prev = json.loads(STATE.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    prev_idx = {u: bool(v) for u, v in (prev.get("urls") or {}).items()}
    cur_idx = {u: results[u]["indexed"] for u in results}

    newly = [u for u in cur_idx if cur_idx[u] and not prev_idx.get(u, False)]
    with LOG.open("a", encoding="utf-8") as f:
        f.write(f"[{ts}] {indexed}/{total} indexed"
                + (f" | NEW: {', '.join(newly)}" if newly else "") + "\n")

    if indexed == total and prev.get("indexed") != total:
        _notify("SURIOTA: pillars indexed", f"All {total} commissioning pillars are now indexed by Google.")
        _self_disable()  # job done, stop the recurring task
    elif newly:
        _notify("SURIOTA: pillar indexed", f"{indexed}/{total} indexed. New: " + "; ".join(newly))
    # else: stay quiet (no noise on unchanged PENDING)

    STATE.write_text(json.dumps({"indexed": indexed, "total": total, "urls": cur_idx,
                                 "checked": ts}, indent=1), encoding="utf-8")
    return 0  # watcher: "pending" is not a failure (scheduler should see success)


if __name__ == "__main__":
    sys.exit(main())
