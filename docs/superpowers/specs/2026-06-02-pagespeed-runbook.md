# PageSpeed Remediation Runbook — snippet-free, CF-free (2026-06-02)

Constraints honored: **no code-snippet plugin** (avoid WP errors), **no Cloudflare**. Execution channels = Elementor native settings + EWWW (image plugin) + WP-Optimize + `_elementor_data` edits (with Elementor flush) + a **child theme** for head/CSS/font changes (the proper non-snippet place). All require WP admin tooling (Playwright/admin UI) + Elementor "Clear Files & Data" after `_elementor_data` edits.

Baseline + root causes: see `suriota_pagespeed_project_2026-06-02.md` memory and `audit/psi/2026-06-02/`. Targets: A11y/BP/SEO ≥95 (BP 96 & SEO 100 already pass), Perf ≥90 mobile. Re-measure each step: `python audit/psi_audit.py` (delete a page's JSON to refresh).

## Prereq: create a child theme (one-time)
Hello-Elementor child theme → `functions.php` + `style.css`. This is the snippet-free home for font preloads, `font-display`, render-blocking tweaks, and contrast CSS. (Site currently has none — that's why past head/CSS changes went into snippets.)

## W1 — Images / LCP (biggest lever; LCP mobile 5–8s)
Channel: **EWWW Image Optimizer** (already installed) — NOT a code snippet.
1. EWWW → Settings: enable **WebP conversion** + **lossless/auto compress**; delivery via `<picture>` rewrite (EWWW's "JS WebP" or `.htaccess`). (CF skipped per user.)
2. EWWW → **Bulk Optimize** (background) — convert/compress all media. Posters like `GTWY-SRT-VD-726x1024.png` are the LCP elements → biggest gain.
3. Per priority page `_elementor_data`: ensure LCP poster has `fetchpriority="high"` (modbus already does) and **no `loading="lazy"`** on the LCP image; add explicit `width`/`height` to any image missing them (header logo `Logo-Suriota-Putih-512x109.png` currently lacks dimensions → CLS).
4. Child theme: `<link rel="preload" as="image">` for each page's LCP poster (conditional by page) — optional, after WebP.
Expected: LCP 5–8s → <2.5s mobile; large Perf jump.

## W2 — CLS (modbus mobile 0.883)
- **0.722 whole-`<main>` shift = fonts** (Geist/Geist-Mono: no preload, no inline @font-face, likely `font-display:auto` → FOUT reflow). Child theme fix:
  - `<link rel="preload" as="font" type="font/woff2" crossorigin>` for the 1–2 critical Geist weights.
  - `@font-face { font-display: optional; }` (or `swap` + `size-adjust`/`ascent-override` fallback-metric overrides) to eliminate reflow.
- Header **logo** missing width/height → add dimensions (theme/header template).
- **Related-pillars** (currently injected client-side near footer): reserve space with `min-height` on its container, or insert lower / after first paint with reserved box (contributes a smaller 0.088 but easy).
Expected: CLS → <0.1 (mobile), big Perf + UX gain.

## W3 — Unused JavaScript / TBT (opportunity 4990ms across all pages)
Third-party: Tawk, GA4, AdSense, Meta/LinkedIn pixels.
- Prefer the plugins'/Elementor's own **"delay JS until interaction"** if available (WP-Optimize Minify has a delay-JS option) — non-snippet. Enable delay-until-interaction for third-party tags only; keep consent/AdSense compliant.
- Do NOT delete tracking; only defer. Re-verify GA4/AdSense still fire after first interaction.
Expected: TBT down, unused-JS opportunity cleared, Perf up.

## W4 — Best-Practices / A11y → 95
- BP already 96, SEO 100 → no work.
- A11y `color-contrast` (all-or-nothing, 13 nodes) — child-theme CSS (per-context, NOT blanket — blanket would break text on dark sections):
  - amber `#c8851f` **as text on light bg** → `#A66A12`: `.sx-hero-eyebrow`, `.sx-related-pillar__num` (done in 5656), `.sx-whyus-num`, the specific amber heading. Leave amber on dark bg untouched.
  - label `#95a4ab` → `#5C6B73` (done in 5656).
  - body `#7a7a7a` (4.29:1) → `#5f5f5f` — ONLY on light sections (target specific section classes, verify no dark-section text breaks).
- `heading-order` (an h4 skip) → fix heading tag level in the relevant Elementor widget (`_elementor_data`).
- `label-content-name-mismatch` → make `.sx-action-btn` aria-label contain visible text, e.g. visible "Order on Tokopedia" → aria-label "Order on Tokopedia — SRT-MGATE-1210" (per product page `_elementor_data`, EN/ID/ZH).
Verify each with visual check; re-run PSI.

## Already applied this session (live, verified)
- Snippet 5656 contrast: `.sx-related-pillars__label` → `#5C6B73`, `.sx-related-pillar__num` → `#A66A12` (backup `audit/snippet_backup_2026-06-02/5656_orig.txt`). (Done before the no-snippet rule; safe, kept.)

## Verification (every wave)
`python audit/psi_audit.py` → compare scorecard vs baseline; confirm no regression in BP/SEO; spot-check pages render correctly (no broken layout/colors) before/after Elementor flush.
