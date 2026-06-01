---
name: suriota-compro-outreach-state-2026-06-01
description: "Lifetime state of all compro broadcast campaigns from alva@suriota.com — 696 sends to 589 unique recipients across 6 sub-campaigns, plus engagement funnel"
metadata: 
  node_type: memory
  type: project
  originSessionId: afa07d25-2e44-4289-9c0b-7a85d5e3eb04
---

State as of 2026-06-01 end-of-day for SURIOTA cold outreach (broadcaster located at `Desktop\Suriota AI Analys\04. Sales & Marketing\broadcaster\`).

**Why:** Gifari is running broadcast cold-email outreach via alva@suriota.com (Chan Alva, Marketing Manager) using the broadcaster Python tool with state.sqlite. Tracking total volume, engagement, and which lead sources have been exhausted is needed before planning next batches.

**How to apply:** Before generating any new compro batch, check this file + run `python broadcast.py --status` to verify dedup vs existing recipients table. Don't repeat already-sent companies. Use `--cap >200` always now — default 15/day cap blocks resumes since alva@ has high daily volume.

## Campaigns sent (8 total as of 1 Jun 2026 EOD)

| Campaign | Sent unique | send_log ok | Date(s) | Source |
|---|---|---|---|---|
| `compro` | 313 | 370 | 29-30 May 2026 | Original Indo/Batam leads |
| `compro_short` | 109 | 142 | 30 May 2026 | BATCH3 SG/MY/macro expansion |
| `compro_tese` | 51 | 62 | 1 Jun 2026 | TESE Excel original emails |
| `compro_tese2` | 16 | 18 | 1 Jun 2026 | TESE urllib HTTP scrape |
| `compro_tese3` | 24 | 28 | 1 Jun 2026 | TESE Playwright JS-rendered scrape |
| `compro_sgmy` | 72 | 72 | 1 Jun 2026 | BATCH3 EXPANSION SG/MY leftovers |
| `compro_ums` | 4 | 4 | 1 Jun 2026 | UMS Group contacts from Mohan OOO |
| `compro_inbound_a` | 18 | 18 | 1 Jun 2026 | gkemals+admin inbox scan, Tier A1/A2/B2/C1 warm |
| `compro_inbound_b` | 11 | 11 | 1 Jun 2026 | gkemals+admin inbox scan, surgical ICP from C2 |
| **TOTAL** | **618** | **725** | | |

## Sender used

100% via `alva@suriota.com` (ACCOUNT_8 in broadcaster/.env, Chan Alva display name). MXroute Onepound (Safari node). Per-account AUP cap = 400/day. On 1 Jun reached **213/400** (sisa 187 — closing for the day per Pak Gifari).

## Lead source files (in `campaigns/`)

- `EMAIL_CAMPAIGN_COMPRO.csv` — original 281-row source (Batam/Indo)
- `BATCH3_FINAL_T1_2026-05-29.csv` + `_T2` — SG/MY/macro expansion (compro_short)
- `EMAIL_CAMPAIGN_EXPANSION_2026-05-29.csv` — 208 rows where 72 SG/MY leftover became compro_sgmy
- `tese_prep_2026-05-31/` — TESE supplier outreach materials, see [[suriota_tese_outreach_workflow_2026-06-01]]
- `tese_prep_2026-05-31/EMAIL_CAMPAIGN_COMPRO_UMS.csv` — 4 UMS contacts from Mohan OOO reveal

## Engagement (after sync_clicks.py + reply_check.py on 2026-06-01 ~13:30 WIB)

| Campaign | Clicked unique | Click % | Replied | Notes |
|---|---|---|---|---|
| compro | 126 | 40% | bounce-only | |
| compro_short | 91 | 83% | bounce-only | high % = security-gateway bots |
| compro_tese | 12 | 24% | bounce/security gateway | |
| compro_tese2 | 5 | 31% | bounce | |
| compro_tese3 | 13 | 54% | bounce | |
| compro_sgmy | 62 | 98% | **1 real OOO + bounces** | 98% click = SG corp security-bots; real human rate TBD |
| compro_ums | TBD | — | TBD | fired ~13:35 WIB |

**Real human replies as of 2026-06-01 EOD:** 1 (<sg-contact>@umsgroup.com.sg — OOO until 30-Jun-2026, revealed 4 alternate contacts that became compro_ums batch).

## Known bouncers / security-gateway blockers (filter from future batches)

- `@lottechem.my` — postmaster@<redacted> auto-rejects all 3 sends
- `@exxonmobil.com` (Singapore branch) — postmaster auto-rejects
- `@petronas.com` / `@petronas.com.my` — `<security-gateway>@petronas.com` quarantine for 14 messages
- `@wilmar.com.sg`, `@sats.com.sg`, `@ioigroup.com` — mailer-daemon rejects after delay (postmaster TLS or relay-side filter)
- `@marsilli.it` — postmaster@<redacted> rejection

## Click-rate ceiling caveat

Singapore/Malaysia corporate emails trigger 80-98% click rate because **email security gateways auto-fetch every URL** to scan for malware. Real-human click rate likely 5-15%. Pak Gifari sees the inflated number first; real signal needs 24-72h wait + filter by IP/UA (not currently captured by /go endpoint).

## Resync commands

```bash
cd "C:/Users/Administrator/Desktop/Suriota AI Analys/04. Sales & Marketing/broadcaster"
python sync_clicks.py        # pulls /go click events from WP plugin
python sync_unsubs.py        # pulls /unsub records (one-click vs scanner)
python reply_check.py        # IMAP scan postmaster + alva inbox, marks send_log status=reply
python broadcast.py --status # engagement funnel per campaign
```

## Future-batch checklist

1. **Dedup vs DB first** — `SELECT LOWER(email) FROM recipients` excludes all 589 sent.
2. **Filter unsubscribed.txt** — 72 entries (mostly bounces, 0 real unsubs).
3. **Use `--cap 200+`** to bypass default 15/day cap.
4. **Test send first** via `--test-recipient gifariksuryo@gmail.com --max 1 --cap 200` BEFORE real send.
5. **`--ignore-hours`** if outside Mon-Fri 09:00-17:00 WIB biz hours.

Related: [[suriota_tese_outreach_workflow_2026-06-01]] for the TESE-specific workflow, [[suriota_adsense_readiness]] for GA4/tracking stack context.
