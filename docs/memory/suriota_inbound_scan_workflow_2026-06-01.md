---
name: suriota-inbound-scan-workflow-2026-06-01
description: "Re-targeting via IMAP scan of @suriota.com mailboxes — turn 382 historical senders into 29 deliverable warm-lead sends (10 mailbox accounts, 2y lookback, multi-tier classify)"
metadata: 
  node_type: memory
  type: project
  originSessionId: afa07d25-2e44-4289-9c0b-7a85d5e3eb04
---

The "inbound senders" pattern: anyone who has EVER emailed `@suriota.com` is by definition a warmer lead than cold outreach. This workflow scans IMAP across all SURIOTA mailboxes and turns historical senders into a fresh broadcast list. Results from 2026-06-01 run at `Desktop\Suriota AI Analys\04. Sales & Marketing\campaigns\tese_prep_2026-05-31\`.

**Why:** Cold outreach has 1-3% reply rate. People who already reached out to SURIOTA (asked questions, sent inquiries, attended events, replied to anyone) have 3-5× higher response probability. The mailboxes accumulated 2+ years of inbound traffic from people Pak Gifari has never re-contacted.

**How to apply:** Re-run this scan every 30-60 days for accumulated inbox state. The pipeline is parameterized — only the OUT_FILE name + dedup-vs-DB needs updating each run. Build into a quarterly habit.

## 5-step pipeline (executed 2026-06-01, ~30 minutes)

### Step 1 — Multi-mailbox IMAP scan (`scan_inbound.py`)
- Iterates ACCOUNT_1..10 from broadcaster/.env, IMAP-logins each at `safari.mxrouting.net:993`.
- INBOX folder, last N=730 days (2y default).
- Extracts From: header (or Reply-To: if missing) via `email.utils.parseaddr`.
- Filters at extraction time: drop @suriota.com, @mxroute, @google personal, @facebook, etc. (SKIP_DOMAINS). Drop "no-reply", "mailer-daemon", "newsletter", etc. (SKIP_LOCALS).
- Dedups by sender email; keeps `count_seen` (number of separate messages from this sender).
- 2026-06-01 result: 10 mailboxes → **382 unique senders** from 997 raw rows. Most volume from gkemals@ (550) + admin@ (425). Two accounts dead: `septa.jurdy.mulya@` + `gusswall@` (auth failed = password rotated externally).

### Step 2 — Classify into Tier A/B/C/D (`filter_inbound.py`)
- Hard-block 70+ domains (`NOISE_DOMAINS`) and noise-locals — marketing automation (Terrapinn, Mekari, monday, hubspot), SaaS notifications (atlassian, anthropic, openrouter), system (DMARC, AWS billing), event spam.
- Drop high-frequency (count >= 8 = marketing automation).
- Drop subdomain prefixes (mail./email./noreply./alerts./auto.).
- Classify remaining:
  - **A1** = Indo industrial (PT/CV + `.co.id` + industrial keyword in domain)
  - **A2** = Indo corporate (any `.co.id`/`.id`/`.or.id`)
  - **B1** = SEA industrial (.com.sg/.my/.th/.vn + industrial keyword)
  - **B2** = SEA corporate (.com.sg/.com.my etc.)
  - **C1** = Intl industrial keyword match
  - **C2** = Other intl corporate (mostly cold pitches TO us)
  - **D** = Personal free-mail (gmail/yahoo/hotmail with display name)
- 2026-06-01 result: 257 after noise filter. A1=6, A2=9, B2=3, C1=6, C2=217, D=16, NOISE_dropped=125.

### Step 3 — Build campaign CSV (`build_inbound.py`)
- Accepts `--tiers A1,A2,B2,...` and optional `--include-all-c2`.
- Generates trigger + correlation by tier (Batam-neighbour for A, partnership for B/C).
- Person-name extraction from display name OR email local (first.last pattern).
- Company-from-domain heuristic — but **REQUIRES manual cleanup** for half the rows since display names often contain person names not company names. Inline Python script with FIX dict for ~15-20 critical rows.

### Step 4 — Surgical filter of C2 / lower tiers (was needed)
- C2 (217 rows) is 80%+ noise — phishing (admin@glidarguard "Payroll Dept | suriota.com"), botnet (prod@novaura-8.com pattern with random suffix), SaaS cold-pitchers (Aldagram, TerraConnect, Framence), system (DMARC reports, QuickBooks alerts).
- Hand-curated **11 real ICP** out of 217:
  - Endress+Hauser (2 contacts), AVEVA (1, SCADA software vendor)
  - 1NCE Indonesia (Irsan, IoT SIM provider)
  - Arrow Electronics Indonesia (Reza Herman, distributor)
  - JJ-Lapp Indonesia (industrial cable)
  - Griffin Filter Indonesia (industrial filter)
  - Pertamina Foundation, Pico Indonesia, HT Solar Group
  - Mitra Karya Sarana (Indo SI)
- Each got custom-typed correlation by `kind` (IoT_cellular / OEM_partner / SCADA_partner / industrial_cabling / industrial_filter / oil_gas / solar_ev / distributor / indo_industrial).

### Step 5 — Register + seed + fire
- 2 campaigns registered: `compro_inbound_a` (18 Tier-A warm) + `compro_inbound_b` (11 surgical-C2).
- Pattern same as TESE batches: add to broadcast.py CAMPAIGNS dict + shared.py CAMPAIGN_TEMPLATES + greeting/trigger-suppress condition lists + per-campaign seed_correlations script.
- **Cap=400 mandatory** — alva@ had already sent 184 today; cap=200 made the broadcast sleep mid-run (2 sends short). Use cap=400 (AUP max) for any same-day resume.

## Hit rate

| Stage | Survivors | Of-source |
|---|---|---|
| Mailboxes scanned | 10 (2 dead auth) | — |
| Raw senders | 997 |  |
| Unique senders | 382 | — |
| After noise filter | 257 | 67% |
| ICP-fit tier A1/A2 | 15 | 4% |
| Surgical C2 ICP | 11 (out of 217 raw) | 5% of C2 |
| **Total deliverable** | **29** | 8% of unique |

So expect about 5-10% of mailbox-scan unique-senders to convert into deliverable warm leads after quality filtering.

## Generated artifacts

- `INBOUND_SENDERS_2026-06-01.csv` — raw 382 senders with display/domain/count_seen
- `INBOUND_AUDIT_2026-06-01.csv` — tier-classified, blocklist+DB-filtered audit
- `EMAIL_CAMPAIGN_COMPRO_INBOUND_A.csv` — 18 warm-lead CSV (broadcaster format)
- `EMAIL_CAMPAIGN_COMPRO_INBOUND_B.csv` — 11 surgical ICP CSV (broadcaster format)
- `scan_inbound.py`, `filter_inbound.py`, `build_inbound.py` — pipeline scripts
- `seed_correlations_inbound_a.py`, `seed_correlations_inbound_b.py` — correlation seeders

## Notable finds during scan

- **Panbil + Batamindo** (5 contacts combined) — both major Batam industrial estates. Strong proximity signal.
- **Teltonika IoT Indonesia** — direct partnership angle (we deploy similar gateways).
- **Endress+Hauser** (2 contacts) — premium process instrumentation OEM.
- **AVEVA** — SCADA software platform; partnership angle for system-integration projects.
- **1NCE** — IoT cellular SIM provider, natural connectivity partner for SRT-MGATE.
- **Startup4Industry Kemenperin** — Indonesian Ministry of Industry initiative.

## Caveats / lessons

1. **Display name ≠ company name** — many B2B emails have just first.last display, not company. Manual cleanup needed; can be partially automated by parsing email signatures (not implemented yet).
2. **Phishing/scam patterns** in C2 — `prod@<random>-N.com` pattern is botnet/scam; aggressive filter needed.
3. **Cold-pitchers-TO-us** show up heavily in C2 (217 rows). These are sellers reaching out to SURIOTA, not buyers. Pivoting them into outbound recipients is mostly wasted send.
4. **Mailbox auth failures silent** — 2 accounts (`septa.jurdy.mulya@`, `gusswall@`) failed login. Could be password rotation. Worth running a credential health-check separately.
5. **Cap=200 too tight** when sender already at 184 — always cap=400 for same-day resumes.

Related: [[suriota_compro_outreach_state_2026-06-01]] for end-of-day totals, [[suriota_tese_outreach_workflow_2026-06-01]] for the TESE-list workflow, [[suriota_outreach_gotchas_2026-06-01]] for API + IMAP gotchas.
