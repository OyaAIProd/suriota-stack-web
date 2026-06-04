#!/usr/bin/env python3
"""Shared Google auth for the suriota SEO toolkit.

Two auth modes, auto-detected (OAuth preferred when present):

  1. OAuth user creds (recommended) — audit/seo/oauth_token.json, created once via
     `python audit/seo/auth_oauth.py`. Uses YOUR Google account (e.g.
     chanalva@suriota.com, already a GSC Owner). Sidesteps GSC refusing to add
     service-account emails, and gives Indexing API access for free (you're Owner).

  2. Service account — audit/seo/sa.json (or GOOGLE_SA_JSON in .env). Needs the SA
     email added to each property:
       - Search Console:  add SA email as a user in the suriota.com GSC property
       - Indexing API:    same SA (must be an *owner* of the GSC property)
       - GA4:             add SA email as Viewer in GA4 Property Access Management

Either way, mints a short-lived access token via google-auth and returns a ready
`requests` session with the Bearer token. Dependency-light: only google-auth +
requests (no google-api-python-client, no google-auth-oauthlib).
"""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEO = ROOT / "audit" / "seo"

SCOPES = [
    "https://www.googleapis.com/auth/webmasters",          # GSC read+write (sitemaps)
    "https://www.googleapis.com/auth/indexing",            # Indexing API
    "https://www.googleapis.com/auth/analytics.readonly",  # GA4 Data API
]


def _envval(name):
    f = ROOT / ".env"
    if not f.exists():
        return None
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith(name + "="):
            val = line.split("=", 1)[1]
            # strip inline comment (whitespace + '#'), then surrounding ws/quotes
            if " #" in val:
                val = val.split(" #", 1)[0]
            return val.strip().strip('"').strip("'")
    return None


def sa_path():
    p = _envval("GOOGLE_SA_JSON")
    return Path(p) if p else (SEO / "sa.json")


def oauth_token_path():
    p = _envval("GOOGLE_OAUTH_TOKEN")
    return Path(p) if p else (SEO / "oauth_token.json")


def have_sa():
    return sa_path().exists()


def have_oauth():
    return oauth_token_path().exists()


def auth_mode():
    """Which credential is active: 'oauth' (preferred), 'sa', or None."""
    if have_oauth():
        return "oauth"
    if have_sa():
        return "sa"
    return None


def _bearer_session(token):
    import requests
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token}",
                      "Content-Type": "application/json"})
    return s


def session(scopes=None):
    """Return (requests.Session with Bearer token, principal_identifier).

    OAuth user creds take precedence over the service account when both exist.
    """
    from google.auth.transport.requests import Request
    scopes = scopes or SCOPES

    otp = oauth_token_path()
    if otp.exists():
        from google.oauth2.credentials import Credentials
        info = json.loads(otp.read_text(encoding="utf-8"))
        creds = Credentials.from_authorized_user_info(info, scopes=scopes)
        creds.refresh(Request())
        return _bearer_session(creds.token), (_envval("GOOGLE_OAUTH_EMAIL") or "oauth-user")

    p = sa_path()
    if not p.exists():
        sys.exit(
            f"[setup needed] no credentials found.\n"
            f"  OAuth (recommended): run  python audit/seo/auth_oauth.py\n"
            f"  or service account:  save the SA JSON key at {p}\n"
            f"  See audit/seo/SETUP.md."
        )
    from google.oauth2 import service_account
    creds = service_account.Credentials.from_service_account_file(str(p), scopes=scopes)
    creds.refresh(Request())
    return _bearer_session(creds.token), creds.service_account_email


def sa_email():
    p = sa_path()
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8")).get("client_email")


def principal():
    """Human label for the active credential (for diagnostics)."""
    if have_oauth():
        return _envval("GOOGLE_OAUTH_EMAIL") or "OAuth user (your Google account)"
    return sa_email()


def gsc_site():
    """Resolve the GSC property identifier. Override with GSC_SITE in .env.
    Domain property = 'sc-domain:suriota.com'; URL-prefix = 'https://suriota.com/'."""
    return _envval("GSC_SITE") or "sc-domain:suriota.com"
