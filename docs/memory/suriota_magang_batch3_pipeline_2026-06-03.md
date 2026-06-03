---
name: suriota-magang-batch3-pipeline-2026-06-03
description: "End-to-end pipeline for processing Magang Batch 3 internship applications - IMAP scan admin@, classify, extract CV via PDF, export CSV/XLSX, branded reply via Tim HRD persona. Spam mitigation learnings included."
metadata: 
  node_type: memory
  type: project
  originSessionId: afa07d25-2e44-4289-9c0b-7a85d5e3eb04
---

For ALL Magang Batch 3 (internship) applications received at admin@suriota.com, use the pipeline below to scan, triage, extract, and reply. Built 2026-06-03.

**Why:** Pak Gifari asked to check admin@ inbox for magang emails on 2026-06-03. 3 applicants found (Florensia, Putri, Farhan). Two had CVs (Politeknik Negeri Padang students), one had only short cover letter. Required a unified pipeline: scan -> extract -> classify -> branded reply.

**How to apply:** Run scripts in order when new magang applications arrive. The pipeline is in `broadcaster/` directory (Desktop\Suriota AI Analys\04. Sales & Marketing\broadcaster).

## Scripts

| Step | Script | Purpose |
|---|---|---|
| 1. Scan | `scan_admin_internship.py 180 1200` | IMAP scan admin@ INBOX for keywords magang/internship/pkl + .ac.id/.edu sender hints. Tolerant of broken charsets. |
| 2. Pull | `pull_magang_applications.py 180 1200` | Pull full email + save PDF attachments to `logs/magang_batch3/`. Extracts text from PDFs (with letter-spaced text normalizer). Auto-detects school/major/semester/phone/skills. Exports CSV + XLSX. |
| 3. Reply | `reply_magang_batch3.py --dry/--test/--send --who putri\|farhan\|florensia\|both\|all` | Build branded reply via reply_builder.py. Supports 2 variants: `standard` (3 questions: motivation/Batam-vs-domicile/hybrid) and `incomplete` (request docs per suriota.com/internship/). |

## Tim HRD persona (admin@ sending)

The admin@suriota.com account uses `Tim HRD SURIOTA` persona for magang context:

```python
FROM_DISPLAY = "Tim HRD SURIOTA"           # From: header display name
HRD_SIG = {
    "name": "Tim HRD SURIOTA",
    "title": "Human Resources & Internship",
    # phone/website/address inherit from shared.SIGNATURE (Alva Chan defaults)
}
```

This overrides the default ACCOUNT_2_NAME ("SURIOTA Admin") and the Alva Chan signature via `from_name_override` + `signature_override` params on `build_branded_reply()`.

## Spam mitigation (critical learnings 2026-06-03)

**Test #1 from admin@ to gifariksuryo@gmail.com -> went to SPAM, logo blocked.** Root causes:

1. **Subject `[TEST -> applicant@gmail.com] Re: ...` was the biggest spam signal.** Bracket-arrow-email prefix screams automation leak. Drop it entirely.
2. **In-Reply-To header referenced a thread gifariksuryo's inbox didn't have** - test recipient + foreign thread = Gmail spam classifier flags.
3. **admin@ fresh sender** - low reputation for Gmail's algo. Logo (hosted at suriota.com/wp-content/uploads/2026/05/suriota-email-logo.png) was blocked as side-effect of spam classification, NOT a logo problem.

**Fixes applied:**
- Test mode now routes to `postmaster@suriota.com` (internal, bypasses Gmail filter entirely).
- Test subject preserves applicant's original Subject (`Re: Magang Batch 3 Application`) instead of test-marker prefix.
- For real send: keep In-Reply-To intact (matches Gmail thread of applicant).
- Logo: keep hosted HTTPS URL - per `broadcast.py` line 333 comment, CID inline showed as "noname" attachment in Gmail (worse). Hosted URL renders correctly when email is NOT in spam.

## Local SpamAssassin score evidence

Sending admin@ -> postmaster@ measured **-7.0 / -4.0** (well below threshold 50.0). The content itself is clean; the Gmail filter was reacting to subject + thread mismatch + fresh sender combo.

## Files committed (broadcaster/)

- `scan_admin_internship.py` - IMAP scan + keyword filter
- `pull_magang_applications.py` - extract + PDF text + CSV/XLSX export
- `reply_magang_batch3.py` - 3-variant reply (applicant keys: a/b/c, names in local memory only)
- `reply_builder.py` - now supports `signature_override`, `from_name_override`, `cc_addresses`, `greeting`, `closing_signoff`
- `verify_admin_deliverability.py` - postmaster@ inbox header scanner for DKIM/SPF/spam checks
- `logs/magang_batch3_applicants.csv` + `.xlsx` - exported applicant list
- `logs/magang_batch3/` - saved CV PDFs
- `logs/magang_batch3_replies/` - .eml archive (DRY/TEST/SEND per applicant)

## Applicant outcomes 2026-06-03

| Applicant | Email | Variant | Profile | Status |
|---|---|---|---|---|
| Applicant A | <redacted-1>@gmail.com | standard | Politeknik Negeri Padang - Bisnis Digital - WordPress/SocialMedia/Marketing | Sent + threaded (16:00 WIB) |
| Applicant B | <redacted-2>@gmail.com | standard | Politeknik Negeri Padang - D4 TRPL sem 6 - Python/Flutter/Laravel/MySQL/Figma - IPK 3.29 | Sent + threaded (16:00 WIB) |
| Applicant C | <redacted-3>@gmail.com | incomplete | Cover letter 190 chars, no CV/info | Sent (requested full docs per suriota.com/internship/) |

## Internship page reference (suriota.com/internship/)

Required qualifications (per page fetch 2026-06-03):
- Active student, min sem 5 (D3/S1)
- Major: Electrical Engineering, Informatics, or related
- Min GPA 3.00/4.00
- On-site Batam Centre min 3 days/week (hybrid)

Required docs: CV, Academic Transcript, Recommendation Letter, Portfolio

Open positions (4): R&D App Developer, DevOps Engineer, QA Specialist, UI/UX Designer

Email subject convention: `[Your Name] - Internship Batch 3`

## Related

- [[suriota_reply_template_v1_2026-06-02]] - branded reply template (the `reply_builder.py` upgraded for this work)
- [[suriota_compro_outreach_state_2026-06-01]] - broadcast pipeline using same SMTP stack
- [[suriota_user_preferences]] - no em-dash, conservative design
