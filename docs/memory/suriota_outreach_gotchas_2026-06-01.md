---
name: suriota-outreach-gotchas-2026-06-01
description: "Lead-enrichment + broadcaster gotchas: Hunter quota math, Cloudflare Warp blocks IMAP 993, broadcast.py default cap=15 blocks resumes, sync_playwright thread-safety, BOM CSV"
metadata: 
  node_type: memory
  originSessionId: afa07d25-2e44-4289-9c0b-7a85d5e3eb04
---

Hard-won gotchas from the 2026-06-01 TESE outreach session. These are easy to re-burn if forgotten.

## Hunter.io free tier — "used: N / available: N" means MAXED

**Trap:** The `/v2/account` response shows `"searches": {"used": 50, "available": 50}`. This does NOT mean "50 used, 50 still available". It means **"50 used, 50 was your monthly limit"** — i.e. zero remaining.

**Why this matters:** I fired 48 Hunter domain-search calls expecting them to work, all returned 429 quota-exceeded. Wasted ~5 minutes of broadcast time.

**Confirmed correct reading:** "remaining = available − used". Free tier = 50/month, resets monthly.

## Cloudflare One / Warp blocks outbound IMAP port 993

**Trap:** `reply_check.py` times out connecting to `safari.mxrouting.net:993` even though the IMAP creds + host work fine elsewhere. DNS resolve OK, but `Test-NetConnection -Port 993` returns False.

**Cause:** Cloudflare Warp client (visible in DNS resolver as `connectivity-check.warp-svc`) intercepts non-HTTP outbound. Disabling Warp via system tray unblocks IMAP 993 immediately.

**How to apply:** When `python reply_check.py` returns `TimeoutError: [WinError 10060]`, first action is to disable Warp client, not debug the Python or check MXroute. After disabling, retry — works in seconds.

## broadcast.py default `--cap 15` blocks resumes

**Trap:** When alva@suriota.com has already sent N>15 today, ANY new broadcast (real or `--test-recipient`) gets stuck on `[wait] All accounts hit daily cap (15). Sleeping 15 min then retrying...` and never recovers.

**How to apply:** Always pass `--cap 200` (or higher) for any broadcast invocation when reusing a sender that's already been active today. MXroute Onepound AUP is 400/day, so cap 200 is safe headroom.

## sync_playwright NOT thread-safe with ThreadPoolExecutor

**Trap:** Sharing one `browser = pw.chromium.launch(...)` across threads via ThreadPoolExecutor fails with `Cannot switch to a different thread / Cur: <thread-id>`. Caused 144 consecutive playwright errors with 0 results on first attempt.

**Fix:** Each thread must own its own Playwright instance + Chromium browser. Use `threading.local()` to store per-thread `_pw + browser`, lazy-instantiated on first call from each thread. Leak the browser at end (process exits anyway).

## CSV files with BOM break `row.get("to")`

**Trap:** EMAIL_CAMPAIGN_EXPANSION_2026-05-29.csv (and likely most Pandas/Excel-exported CSVs) starts with UTF-8 BOM `﻿`. With default `encoding="utf-8"`, `csv.DictReader` reads the first column key as `"﻿to"`, not `"to"`. Then `row.get("to")` returns None → dedup scan wrongly reports 0 SG/MY candidates.

**Fix:** Use `encoding="utf-8-sig"` in `open()` — strips the BOM automatically.

## broadcast.py `seed_recipients()` ignores trigger/correlation columns

**Trap:** Even though the CSV has columns `to,first_name,last_name,company,trigger,correlation` and the broadcast.py CSV reader iterates them, `seed_recipients()` (broadcast.py line ~200) only inserts email + first_name + last_name + company into `recipients` table. Trigger + correlation are dropped on the floor. Without a separate seeder, every email falls back to the generic KLHK-SPARING default correlation.

**Fix:** Run a `seed_correlations_<batch>.py` script AFTER initial seed. It UPDATEs `recipients.correlation` and `recipients.trigger` by (email, campaign) match. Pattern established in `seed_correlations_batch3.py`, replicated for each new campaign.

## broadcast.py GA4 emission used `.get()` on sqlite3.Row

**Trap (now fixed in code):** Line 648 had `batch[0].get("company")` but `batch[0]` is a `sqlite3.Row` (no .get method, only `["col"]` indexing and `.keys()`). When real broadcast (non-test) reached the GA4 emit path, it crashed with `AttributeError`. The crash propagated up, breaking out of the `with db.conn()` context BEFORE `db.commit()` ran — so mark_sent + log_send + account_record_send all rolled back. Result: SMTP send to TDK succeeded but DB showed jessica.ma still pending. Required manual SQL backfill.

**Fix applied (broadcast.py line 648):** `((batch[0]["company"] if "company" in batch[0].keys() else "") or "")[:64]`

**Lesson:** Wrap analytics emit in try/except — analytics must NEVER break the send pipeline. The body of `_emit_ga4_event()` already has try/except, but the ARGUMENT-CONSTRUCTION (the dict literal) was outside that protection.

Related: [[suriota_compro_outreach_state_2026-06-01]] for current campaign totals, [[suriota_tese_outreach_workflow_2026-06-01]] for the workflow these gotchas appeared in.
