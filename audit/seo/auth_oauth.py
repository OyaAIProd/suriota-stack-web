#!/usr/bin/env python3
"""One-time OAuth user-credential flow for the suriota SEO toolkit.

Uses YOUR Google account (e.g. chanalva@suriota.com, already a GSC Owner) instead
of a service account — sidesteps Search Console refusing to add service-account
emails, and grants Indexing API access for free (you're an Owner).

Dependency-light: stdlib http.server + requests only (no google-auth-oauthlib).

Prereqs (you-side, GCP project named-sequencer-458710-n1):
  1. OAuth consent screen configured:
       Internal  (if suriota.com is Google Workspace — no verification, tokens
                  don't expire), else External + add your email as a Test user.
  2. Credentials -> Create credentials -> OAuth client ID
       -> Application type: **Desktop app** -> download JSON
       -> save as  audit/seo/client_secret.json
  3. Enable 3 APIs (project named-sequencer-458710-n1):
       Search Console API, Web Search Indexing API, Google Analytics Data API.

Run:  python audit/seo/auth_oauth.py
A browser opens; sign in + consent once. Refresh token is saved to
audit/seo/oauth_token.json (git-ignored). Re-run only if you revoke access.
"""
import json, sys, webbrowser, urllib.parse, http.server, socket
from pathlib import Path

import requests

SEO = Path(__file__).resolve().parent
CLIENT_SECRET = SEO / "client_secret.json"
TOKEN_OUT = SEO / "oauth_token.json"

SCOPES = [
    "https://www.googleapis.com/auth/webmasters",          # GSC read+write (sitemaps)
    "https://www.googleapis.com/auth/indexing",            # Indexing API
    "https://www.googleapis.com/auth/analytics.readonly",  # GA4 Data API
]
AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URI = "https://oauth2.googleapis.com/token"


def _load_client():
    if not CLIENT_SECRET.exists():
        sys.exit(
            f"[setup needed] {CLIENT_SECRET} not found.\n"
            "  GCP -> APIs & Services -> Credentials -> Create credentials\n"
            "  -> OAuth client ID -> Application type: Desktop app -> download JSON\n"
            "  -> save it as audit/seo/client_secret.json, then re-run."
        )
    data = json.loads(CLIENT_SECRET.read_text(encoding="utf-8"))
    node = data.get("installed") or data.get("web")
    if not node:
        sys.exit("client_secret.json: expected a 'Desktop app' (installed) OAuth client.")
    return node["client_id"], node["client_secret"]


def _free_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


class _Catch(http.server.BaseHTTPRequestHandler):
    code = None

    def do_GET(self):
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
        _Catch.code = params.get("code")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        ok = bool(_Catch.code)
        msg = ("Authorization complete - close this tab and return to the terminal."
               if ok else "No authorization code received.")
        self.wfile.write(
            f"<html><body style='font-family:sans-serif;padding:2rem'>"
            f"<h3>{msg}</h3></body></html>".encode("utf-8"))

    def log_message(self, *a):
        pass


def main():
    client_id, client_secret = _load_client()
    port = _free_port()
    redirect_uri = f"http://localhost:{port}/"

    url = AUTH_URI + "?" + urllib.parse.urlencode({
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(SCOPES),
        "access_type": "offline",
        "prompt": "consent",       # force a refresh_token even on a re-grant
        "include_granted_scopes": "true",
    })

    print("Opening browser for Google sign-in...")
    print("If it does not open, paste this URL into your browser:\n  " + url + "\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

    srv = http.server.HTTPServer(("127.0.0.1", port), _Catch)
    srv.handle_request()   # serve exactly one request (the OAuth redirect)
    srv.server_close()

    code = _Catch.code
    if not code:
        sys.exit("No authorization code captured. Re-run the script.")

    tok = requests.post(TOKEN_URI, data={
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }, timeout=30).json()

    if "refresh_token" not in tok:
        sys.exit(
            f"No refresh_token in token response: {tok}\n"
            "  Revoke the prior grant at https://myaccount.google.com/permissions\n"
            "  then re-run (a reused client sometimes skips the refresh_token)."
        )

    TOKEN_OUT.write_text(json.dumps({
        "type": "authorized_user",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": tok["refresh_token"],
        "token_uri": TOKEN_URI,
        "scopes": SCOPES,
    }, indent=2), encoding="utf-8")

    print(f"\nSaved {TOKEN_OUT}")
    print("Next:  python audit/seo/check.py")


if __name__ == "__main__":
    main()
