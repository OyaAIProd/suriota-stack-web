---
name: suriota-google-seo-toolkit
description: "Google SEO API toolkit at audit/seo/ (GSC + Indexing + GA4 + Custom Search) — built 2026-06-03, blocked on user-side service-account setup"
metadata: 
  node_type: memory
  type: project
  originSessionId: 5cd78699-f672-46a0-b556-1eb406beaa8c
---

Built 2026-06-03 a dependency-light Google SEO toolkit at `audit/seo/` to go beyond PSI. Uses `google.auth` (installed) to mint a service-account token + `requests` to hit REST APIs directly — NO google-api-python-client/google-analytics-data needed (both MISSING, not required).

**Key credential fact:** the existing `.env` `PSI_API_KEY` is a *simple API key restricted to PageSpeed Insights only* (probe: Safe Browsing → `API_KEY_SERVICE_BLOCKED`; Custom Search/Knowledge Graph → API-not-enabled in GCP project **566492980711**). The powerful SEO APIs (Search Console, Indexing, GA4) do NOT accept a plain API key — they need **OAuth or a service account**. So one SA covers 3 of the 4 capabilities.

**Files:** `_gauth.py` (shared SA auth, scopes webmasters+indexing+analytics.readonly), `check.py` (one-shot PASS/FAIL validator), `gsc.py` (queries/pages/opportunities/inspect/sitemaps/raw), `indexing.py` (push/status/remove URL_UPDATED), `ga4.py` (overview/channels/sources/landing/events runReport), `rank.py` (Custom Search rank tracker), `keywords.txt` (EN/ID targets), `SETUP.md` (exact click-paths). `.gitignore` updated to block `audit/seo/sa.json` (+ variants); `.env` has commented placeholders (GA4_PROPERTY_ID, GOOGLE_CSE_CX, GSC_SITE, CSE_API_KEY, GOOGLE_SA_JSON).

**BLOCKED on user (you-side, can't be done by Claude):** create SA `suriota-seo-bot` in GCP 566492980711, download JSON → `audit/seo/sa.json`; enable 3 APIs (searchconsole, indexing, analyticsdata); add SA email as **Owner** in GSC suriota.com property (Owner needed for Indexing API, not just Full), **Viewer** in GA4 + copy numeric Property ID (≠ measurement id `G-X69D43F8QD`); for rank.py: enable Custom Search API + Programmable Search Engine set to "search entire web" → CX. Then `python audit/seo/check.py` validates everything. Full steps in `audit/seo/SETUP.md`.

**Why this matters:** suriota's whole trajectory is SEO; GSC API replaces the manual "GSC user-side" steps (see [[suriota_codex_audit_followup_2026-05-31]], [[suriota_gsc_noindex_feeds_pagination_2026-06-01]]) with real query/position/CWV-field/index-status data, and Indexing API pushes re-crawl of pages we fix. Complements PSI lab data (see [[suriota-pagespeed-project-2026-06-02]]).
