---
name: suriota-tese-outreach-workflow-2026-06-01
description: Reusable 6-step workflow that turned TESE supplier Excel (247 vendors no-email) into 122 deliverable sends — DNS guess + urllib scrape + Playwright + Hunter API + custom correlations
metadata: 
  node_type: memory
  type: project
  originSessionId: afa07d25-2e44-4289-9c0b-7a85d5e3eb04
---

The TESE outreach campaign (`compro_tese`, `compro_tese2`, `compro_tese3`, plus `compro_sgmy` and `compro_ums`) demonstrates a complete lead-enrichment pipeline that turned a low-signal SAP supplier list into 122 deliverable cold-email sends. Materials at `Desktop\Suriota AI Analys\04. Sales & Marketing\campaigns\tese_prep_2026-05-31\`.

**Why:** Original TESE supplier Excel (`Supplier Feedback on TESE.xlsx`) had 312 vendor rows but only 65 had real emails (rest were VLOOKUP refs to an external file that wasn't accessible). For SURIOTA cold outreach to reach the other 247, needed multi-tier enrichment without burning paid APIs (Apollo + Hunter free tiers exhausted, Snov 403, VoilaNorbert 404).

**How to apply:** Re-use this workflow whenever Gifari hands over an Excel/CSV of company names with no/partial emails. The script collection is parameterized — only the source filename and tier classifications need editing for new lists.

## 6-step pipeline (executed 2026-06-01, total ~90 minutes)

### Step 1 — Classify + segment original emails (`build_prep.py`)
- Reads source XLSX Sheet2, classifies each row into Tier A (Batam/Indo PT/CV), B (intl OEM), C (component distributor), D (free-mail/role-only/drop), X (no email).
- Outputs: audit XLSX (5 sheets) + EMAIL_CAMPAIGN_COMPRO_TESE_ALL.csv (CSV-format ready for broadcaster) + TESE_ENRICHMENT_TARGETS.csv (247 no-email rows for enrichment).
- TESE result: 20 A / 25 B / 7 C / 13 D / 247 X.

### Step 2 — Generate domain candidates + DNS verify (`enrich_missing.py --verify-only`)
- For each "no email" row, generate up to 12 domain candidates (`{stems}.{tlds}`) using legal-suffix-stripped tokens + TLD heuristics by hint (PT prefix → .co.id, /SDN BHD/ → .com.my, etc.).
- DNS-resolve each candidate (`socket.gethostbyname` with 3s timeout). First alive = domain attached to row.
- TESE result: **176/238 alive domains (73%)** including Batam PT/CV 67%, intl OEM 76%.
- Output: TESE_ENRICHED_DNS_ONLY_2026-06-01.csv (one row per company w/ alive_domain or empty).

### Step 3a — urllib scrape contact pages (`scrape_emails.py`)
- For each alive domain, fetch homepage + 9 contact-like paths (`/contact`, `/contact-us`, `/about`, `/team`, `/kontak`, etc.) via urllib.
- Extract emails via regex on HTML + mailto: hrefs. Score each: +10 for same-domain match, +0-5 by local-part priority (sales/info/contact > admin > webmaster).
- TESE result: **24 companies with email (13%)**, 37 emails total.
- Key gotcha: Modern corporate SPAs hide emails behind contact forms; urllib misses JS-rendered content.

### Step 3b — Playwright fallback for the 144 no-email alives (`scrape_emails_playwright.py`)
- Each thread gets its own `sync_playwright()` instance + Chromium browser (CRITICAL: sync_playwright is NOT thread-safe; can't share browser across threads).
- Per domain: load homepage, dismiss cookie banners, auto-discover contact links from nav, visit up to 4 contact paths, extract emails from rendered DOM + mailto hrefs.
- 4 parallel workers, ~8 min for 144 domains. **+32 companies with email** (additional 23%), bringing combined coverage to 57/176 = 32%.
- New JS-only finds: Bossard, Samtec, Belden, Makino, Arburg, TUV SUD, PT Kobexindo, PT Caltest, etc.

### Step 4 — Filter + dedup + build campaign CSV (`build_tese2.py`)
- Apply score threshold (≥14 = same-domain + meaningful local, eliminates false positives like `redaksi@batam.co.id` which matched media site).
- Dedup vs `recipients` table + `unsubscribed.txt`.
- Classify Tier A (PT/CV) vs Tier B (intl) → generates per-tier trigger + correlation paragraph (Batam-neighbour angle for A, partnership-angle for B).
- Output: broadcaster-compatible CSV with columns `to,first_name,last_name,company,trigger,correlation`.

### Step 5 — Register campaign + seed correlations
- Add CSV path to `broadcaster/broadcast.py` `CAMPAIGNS` dict.
- Add template entry to `broadcaster/stacks/shared.py` `CAMPAIGN_TEMPLATES` (reuse `compro`'s body_md + subject).
- Add campaign key to greeting + trigger-suppress conditions in `broadcast.py` (line ~498 and ~505) — required so international recipients get "Dear FirstName" not "Dear Bapak/Ibu" and so per-row correlation is the personal hook (not the trigger sentence).
- **CRITICAL: run `seed_correlations_<batch>.py` AFTER initial broadcast.py seed** — `seed_recipients()` ignores trigger/correlation columns from CSV; without this seeder every email falls back to generic KLHK-SPARING default correlation.

### Step 6 — Test send → confirm → fire
- `python broadcast.py --campaign <key> --max 1 --only-accounts 8 --test-recipient gifariksuryo@gmail.com --cap 200 --ignore-hours`
- Verify body via IMAP from postmaster@suriota.com inbox (CC's the test).
- Fire real send: drop `--test-recipient` and `--max`.
- Monitor via Monitor tool: `grep -E "OK \(|Traceback|Run summary"` on tee'd log file.

## Bonus pattern — OOO replies as enrichment source

After compro_sgmy fired, <sg-contact>@umsgroup.com.sg returned an Out-of-Office that revealed 4 alternate contacts (Prakash/Moon/Jayakumar/Raman). These became `compro_ums` batch with role-specific correlations (RFQ-driven build lines / commit-date accuracy / PACT quality / escalations). Pattern: **always re-scan reply_check.py output for OOO contact-redirect emails** — proves mailbox active + reveals named contacts.

## Hit rate benchmarks (for forecasting future TESE-style work)

| Filter | Hit rate |
|---|---|
| Heuristic domain guess → DNS alive | **~70%** (Batam 67%, Intl 76%) |
| Alive domain → urllib finds email | **~13%** of alives |
| Alive domain → urllib + Playwright finds email | **~32%** of alives |
| Score ≥14 high-quality (same-domain + meaningful local) | typically half of extracted emails |

So for N "no-email vendor rows" → expect ~0.7 × 0.32 = **~22% deliverable yield** with this pipeline. The TESE 247-row list yielded 46 sends (19%) after dedup against already-sent.

## Pitfalls hit + fixed during this run

1. **Apollo free tier blocks `mixed_companies/search` (403)** — only `organizations/enrich` works (needs domain input). Useless for discovery; pivoted away.
2. **Snov free trial 403 on most endpoints** — only `get-balance` worked. Skipped.
3. **VoilaNorbert legacy URL 404** — needs newer API. Skipped.
4. **Hunter free tier 50/month** — burned through 50 credits in the failed first attempt before quota check showed 0 remaining. Note: "used: 50, available: 50" means MAXED out, not "50 of 50 remaining" — see [[suriota_outreach_gotchas_2026-06-01]].
5. **Playwright sync API + ThreadPoolExecutor — "Cannot switch to a different thread"** — must instantiate Playwright per worker thread, not share single browser.
6. **broadcast.py GA4 emission crashed `batch[0].get("company")`** — sqlite3.Row has no .get(); fixed to `batch[0]["company"] if "company" in batch[0].keys() else ""`. Critical because crash rolled back the in-transaction `mark_sent`, leaving jessica.ma@TDK in "pending" despite SMTP success. Required manual DB backfill.
7. **CSV files with BOM** (EMAIL_CAMPAIGN_EXPANSION_2026-05-29.csv) need `utf-8-sig` encoding or `row.get('to')` returns None and the dedup scan reports 0 SG/MY candidates wrongly.

## Files generated in `tese_prep_2026-05-31/`

- `build_prep.py` — Step 1 segmenter
- `enrich_missing.py` — Step 2 DNS verifier (+ scaffolded Apollo/Hunter code, retained)
- `scrape_emails.py` — Step 3a urllib scraper
- `scrape_emails_playwright.py` — Step 3b JS-rendered scraper
- `build_tese2.py` — Step 4 CSV builder (parameterized by MIN_SCORE + OUT_CSV)
- `build_sgmy.py` — separate builder for SG/MY leftovers from EXPANSION CSV
- `BROADCAST_PLAN_2026-06-01.md` — original execution plan
- 4 lead CSVs + 1 audit XLSX + cache files

Related: [[suriota_compro_outreach_state_2026-06-01]] for end-of-day totals, [[suriota_outreach_gotchas_2026-06-01]] for API + IMAP gotchas.
