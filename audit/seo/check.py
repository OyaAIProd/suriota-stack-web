#!/usr/bin/env python3
"""One-shot validator: is the Google SEO setup wired correctly?

Run this after creating the service account + granting it access. It checks each
capability and prints PASS/FAIL with the exact remediation if something's missing.

  python audit/seo/check.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import _gauth as g


def main():
    print("=== suriota Google SEO setup check ===\n")

    mode = g.auth_mode()
    if mode is None:
        print("FAIL  no credentials found.")
        print("      OAuth (recommended): python audit/seo/auth_oauth.py")
        print(f"      or service account:  save SA JSON at {g.sa_path()}")
        print("      → see audit/seo/SETUP.md\n")
        _check_cse()  # CSE can still be checked (uses API key)
        return

    if mode == "oauth":
        print(f"PASS  OAuth user credentials found: {g.oauth_token_path()}")
        print(f"      principal = {g.principal()}\n")
    else:
        print(f"PASS  service-account key found: {g.sa_path()}")
        print(f"      SA email = {g.sa_email()}\n")

    try:
        s, email = g.session()
    except SystemExit:
        raise
    except Exception as e:
        print(f"FAIL  token mint: {e}")
        if mode == "oauth":
            print("      → token may be revoked/expired; re-run python audit/seo/auth_oauth.py")
        return

    # --- GSC: list sites the SA can see ---
    r = s.get("https://www.googleapis.com/webmasters/v3/sites")
    if r.status_code == 200:
        sites = [e["siteUrl"] for e in r.json().get("siteEntry", [])]
        if sites:
            print(f"PASS  Search Console: SA can access {len(sites)} property(ies):")
            for x in sites:
                print(f"        {x}")
            print(f"      (toolkit uses GSC_SITE={g.gsc_site()})")
        else:
            print("FAIL  Search Console: authenticated but sees 0 properties")
            if mode == "oauth":
                print("      → the signed-in account isn't a user/owner of any GSC property")
            else:
                print(f"      → add {g.sa_email()} as a user in the suriota.com GSC property")
    else:
        print(f"FAIL  Search Console API: HTTP {r.status_code} {r.text[:120]}")
        print("      → enable 'Search Console API' in GCP" +
              ("" if mode == "oauth" else " + add SA in GSC"))
    print()

    # --- Indexing API: dry metadata read on home ---
    r = s.get("https://indexing.googleapis.com/v3/urlNotifications/metadata",
              params={"url": "https://suriota.com/"})
    if r.status_code in (200, 404):  # 404 = never notified yet, but API works
        print("PASS  Indexing API: reachable (token accepted)")
    elif r.status_code == 403:
        print("FAIL  Indexing API: 403 — enable 'Web Search Indexing API' in GCP")
        if mode == "oauth":
            print("      (you're a GSC Owner, so once the API is enabled this passes)")
        else:
            print(f"      AND add {g.sa_email()} as an *Owner* of the GSC property")
    else:
        print(f"WARN  Indexing API: HTTP {r.status_code} {r.text[:120]}")
    print()

    # --- GA4: needs numeric property id ---
    pid = g._envval("GA4_PROPERTY_ID")
    if not pid:
        print("WARN  GA4: GA4_PROPERTY_ID not set in .env")
        print("      → GA4 Admin → Property Settings → copy numeric Property ID (not G-XXXX)")
    else:
        r = s.post(f"https://analyticsdata.googleapis.com/v1beta/properties/{pid}:runReport",
                   json={"dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}],
                         "metrics": [{"name": "sessions"}]})
        if r.status_code == 200:
            v = r.json().get("rows", [{}])
            tot = v[0]["metricValues"][0]["value"] if v else "0"
            print(f"PASS  GA4 Data API: property {pid} reachable (last 7d sessions={tot})")
        elif r.status_code == 403:
            who = g.principal() if mode == "oauth" else g.sa_email()
            print(f"FAIL  GA4: 403 — add {who} as Viewer in GA4 Property Access Mgmt")
            print("      AND enable 'Google Analytics Data API' in GCP")
        else:
            print(f"WARN  GA4: HTTP {r.status_code} {r.text[:120]}")
    print()

    _check_cse()


def _check_cse():
    import requests
    key = g._envval("CSE_API_KEY") or g._envval("PSI_API_KEY")
    cx = g._envval("GOOGLE_CSE_CX")
    if not cx:
        print("WARN  Custom Search: GOOGLE_CSE_CX not set")
        print("      → create a Programmable Search Engine (programmablesearch.google.com),")
        print("        enable 'Custom Search API' in GCP, put CX in .env as GOOGLE_CSE_CX")
        return
    r = requests.get("https://www.googleapis.com/customsearch/v1",
                     params={"key": key, "cx": cx, "q": "suriota", "num": 1}, timeout=20)
    if r.status_code == 200:
        print(f"PASS  Custom Search: CX={cx} working (totalResults="
              f"{r.json().get('searchInformation', {}).get('totalResults', '?')})")
    else:
        print(f"FAIL  Custom Search: HTTP {r.status_code} {r.text[:120]}")
        print("      → enable Custom Search API + ensure the key allows it (API restrictions)")


if __name__ == "__main__":
    main()
