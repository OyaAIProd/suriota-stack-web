#!/usr/bin/env python3
"""GA4 Data API reporting for suriota (service-account auth, REST runReport).

Needs the numeric GA4 Property ID in .env as GA4_PROPERTY_ID (NOT the
measurement id G-X69D43F8QD). Find it: GA4 Admin → Property Settings.

  python audit/seo/ga4.py overview [DAYS]     sessions/users/engagement (default 28d)
  python audit/seo/ga4.py channels [DAYS]      traffic by default channel group
  python audit/seo/ga4.py sources  [DAYS]      sessions by source/medium
  python audit/seo/ga4.py landing  [DAYS]      top landing pages by sessions
  python audit/seo/ga4.py events   [DAYS]      event counts (find your conversions)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gauth as g

SCOPE = ["https://www.googleapis.com/auth/analytics.readonly"]


def _pid():
    pid = g._envval("GA4_PROPERTY_ID")
    if not pid:
        sys.exit("Set GA4_PROPERTY_ID in .env (numeric, from GA4 Admin → Property Settings).")
    return pid


def _run(dims, mets, days, limit=50, order_metric=None):
    s, _ = g.session(scopes=SCOPE)
    body = {
        "dateRanges": [{"startDate": f"{days}daysAgo", "endDate": "today"}],
        "dimensions": [{"name": d} for d in dims],
        "metrics": [{"name": m} for m in mets],
        "limit": limit,
    }
    if order_metric:
        body["orderBys"] = [{"metric": {"metricName": order_metric}, "desc": True}]
    r = s.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{_pid()}:runReport",
               json=body)
    if r.status_code != 200:
        sys.exit(f"GA4 failed: HTTP {r.status_code} {r.text[:200]}")
    return r.json()


def _print(j, dims, mets):
    head = dims + mets
    print("  ".join(f"{h:<24}" if i < len(dims) else f"{h:>12}"
                     for i, h in enumerate(head)))
    print("-" * (26 * len(dims) + 14 * len(mets)))
    for row in j.get("rows", []):
        dv = [d["value"] for d in row.get("dimensionValues", [])]
        mv = [m["value"] for m in row.get("metricValues", [])]
        line = "  ".join(f"{v[:22]:<24}" for v in dv) + "  " + "  ".join(f"{v:>12}" for v in mv)
        print(line)


def cmd_overview(days=28):
    print(f"\n=== GA4 overview (last {days}d) ===")
    j = _run([], ["sessions", "totalUsers", "newUsers", "screenPageViews",
                  "averageSessionDuration", "engagementRate"], days)
    if j.get("rows"):
        mv = j["rows"][0]["metricValues"]
        labels = ["sessions", "users", "newUsers", "pageviews", "avgSessDur(s)", "engRate"]
        for lab, m in zip(labels, mv):
            v = m["value"]
            if lab == "avgSessDur(s)": v = f"{float(v):.0f}"
            if lab == "engRate": v = f"{float(v)*100:.1f}%"
            print(f"  {lab:<16}: {v}")


def cmd_channels(days=28):
    print(f"\n=== Channels (last {days}d) ===")
    j = _run(["sessionDefaultChannelGroup"], ["sessions", "totalUsers", "conversions"],
             days, order_metric="sessions")
    _print(j, ["channel"], ["sessions", "users", "conversions"])


def cmd_sources(days=28):
    print(f"\n=== Source / Medium (last {days}d) ===")
    j = _run(["sessionSource", "sessionMedium"], ["sessions", "totalUsers"],
             days, order_metric="sessions")
    _print(j, ["source", "medium"], ["sessions", "users"])


def cmd_landing(days=28):
    print(f"\n=== Top landing pages (last {days}d) ===")
    j = _run(["landingPage"], ["sessions", "totalUsers", "conversions"],
             days, order_metric="sessions")
    _print(j, ["landingPage"], ["sessions", "users", "conv"])


def cmd_events(days=28):
    print(f"\n=== Events (last {days}d) — pick your conversion events ===")
    j = _run(["eventName"], ["eventCount"], days, order_metric="eventCount")
    _print(j, ["eventName"], ["count"])


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__); return
    days = int(a[1]) if len(a) > 1 else 28
    {"overview": cmd_overview, "channels": cmd_channels, "sources": cmd_sources,
     "landing": cmd_landing, "events": cmd_events}.get(a[0], lambda *_: print(__doc__))(days)


if __name__ == "__main__":
    main()
