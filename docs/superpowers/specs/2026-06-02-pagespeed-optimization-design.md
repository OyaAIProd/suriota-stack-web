# PageSpeed Optimization — Design Spec (2026-06-02)

## Goal
Raise Lighthouse/PageSpeed scores on suriota.com priority pages to: **Accessibility / Best-Practices / SEO ≥ 95** and **Performance ≥ 90 (green) on mobile** (push as high as possible without dismantling Elementor), verified on **mobile + desktop**. Authoritative scoring via the PageSpeed Insights API (same engine as pagespeed.web.dev, incl. CrUX field data).

## Scope
Priority set (~10 EN pages), since most fixes are sitewide and cascade to translations/other pages:
- `/` (homepage)
- 6 product pages: `suriota-modbus-gateway`, `thm-30md`, `pm1611-wd`, `iso-m485-series`, `rs-485-surge-protector-spd-t485-105`, `waste-water-logger`
- Key pillar/service: `industrial-iot-system-integration`, `system-integration`, `surge-saas-platform`

Out of scope (for now): /id/ and /zh/ translations (revisit after EN is green — they share Elementor templates so fixes carry over).

## Approach (chosen: A — measure → prioritize → sitewide-first → re-measure)
Rejected: Lighthouse CI + budgets (overkill for one-time push); manual PSI web UI (not batchable).

## Tooling
- `audit/psi_audit.py` — reads `PSI_API_KEY` from `.env`; takes a URL list; runs **mobile + desktop** via PSI API v5; saves raw JSON to `audit/psi/<YYYY-MM-DD>/<slug>-<strategy>.json`; emits:
  1. Per-page scorecard (4 categories) + core metrics (FCP, LCP, TBT, CLS, SI).
  2. Cross-page **opportunity matrix** (each opportunity/diagnostic ranked by frequency × estimated ms saved) to find highest-leverage sitewide fixes.
  - Polite rate-limiting between calls; resumable (skips already-saved JSON).
- Local Lighthouse (`npx lighthouse`, system Chrome) — quick before/after on a single fix only (absolute scores noisier than PSI; use for trend, confirm final via PSI).

## Execution waves (data-driven; order may shift after baseline)
Mapped to known stack constraints (see memory `suriota_perf_optimization_2026-06-01`, `suriota_adsense_readiness`):
- **W1 — Third-party JS / TBT:** Tawk, GA4, AdSense, LinkedIn/Meta pixels are the largest TBT contributors. Defer / delay-until-interaction. Likely the key lever for mobile Performance.
- **W2 — Images:** EWWW Image Optimizer (already installed) → bulk WebP + compression; explicit width/height; lazy-load below fold → fixes LCP and "properly sized / next-gen images". (Poster file-replace is blocked, but EWWW WebP conversion is the sanctioned path.)
- **W3 — Render-blocking CSS/JS & CLS (0.209):** Elementor "Improved/Optimized asset loading", `font-display: swap`, reserve space to kill layout shift. Critical-CSS / minify only per-page with verification (Elementor minify is risky per memory → test, rollback if breakage).
- **W4 — Best-Practices / A11y / SEO:** usually quick — color contrast, form labels, heading order, console/mixed-content errors, meta. Drives the non-perf categories to 95+.

Re-measure via PSI after each wave. Backup `_elementor_data` before any Elementor edit (proven pattern). Flush Elementor "Clear Files & Data" + WP-Optimize purge after edits (browser login: admin / `vyBm#…`).

## Definition of done
Each priority page: A11y/BP/SEO ≥ 95 and Performance ≥ 90 (mobile), confirmed by PSI API (mobile + desktop captured).

## Risks / non-goals
- Mobile Performance ≥ 95 is NOT guaranteed on Elementor; target is green (≥90), best-effort beyond.
- No theme replacement, no page-builder migration, no removal of business-critical tracking (defer, don't delete).
- Some diagnostics may be Elementor/theme-bound and irreducible; documented if hit.
