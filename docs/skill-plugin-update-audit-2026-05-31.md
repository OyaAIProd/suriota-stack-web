# Skill & Plugin Update Audit - 2026-05-31

## Local Context

Project ini adalah workspace otomasi untuk suriota.com:

- Platform live: WordPress + Elementor Pro.
- SEO/indexing: AIOSEO, Polylang, sitemap/noindex/redirect/schema automation.
- Automation: Python REST scripts, Playwright/Puppeteer visual audit, MCP Tools for Elementor.
- Local Node packages: `@modelcontextprotocol/sdk@1.29.0`, `playwright@1.60.0`, `puppeteer@24.43.1`.
- Current live MCP stack after update: MCP Tools for Elementor v1.7.4 via WordPress MCP Adapter v0.5.0.

## Install / Update Priority

### P0 - Update on staging first

| Area | Action | Latest found | Why |
|---|---:|---:|---|
| WordPress Core | Check staging upgrade path to 7.0 | 7.0 released 2026-05-20 | Latest official release exists, but this site has many Elementor/snippet overrides, so test before production. |
| Elementor free | Update after backup/regenerate CSS | 4.0.9 | Relevant because project depends on Elementor structures, sticky/header behavior, and Atomic Editor compatibility. |
| Elementor Pro | Update in lockstep with Elementor core | 4.0.4 found in official Pro changelog | Keep Pro/Core compatible; test forms, popups, nav/menu, custom CSS, carousel, dynamic tags. |
| WordPress MCP Adapter | Updated v0.4.1 -> v0.5.0 | v0.5.0 | v0.5.0 adds protocol negotiation, typed schema handling, stricter validation, and WP 6.9/7.0 notes. |
| MCP Tools for Elementor | Updated v1.4.3 -> v1.7.4 | v1.7.4 | Live endpoint now reports 113 tools with Elementor Pro + Elementor 4.x support. |

### P1 - Keep / update existing production plugins

| Plugin | Latest found | Recommendation |
|---|---:|---|
| AIOSEO | 4.9.7.2 | Keep and update. It already owns meta, schema, XML sitemap, webmaster verification, robots, Search Console features. Avoid installing Yoast/RankMath in parallel. |
| Polylang | 3.8.2 | Keep and update. Consider Polylang Pro if you want to remove custom hreflang/language-switcher snippets and manage translation links cleanly. |
| Redirection | 5.7.5 | Keep and update. This repo already depends on redirect-chain fixes and 404 redirects. |
| Code Snippets | 3.9.6 | Keep and update if this is the plugin storing SX snippets. It is central to sitewide schema/nav/font/CLS workarounds. |
| WP-Optimize | 4.5.4 | Keep if active, but test CPU/cache behavior. Disable overlapping minify/merge features if Cloudflare/APO or Elementor generated CSS is used. |
| Tawk.To Live Chat | 0.9.3 | Update only after fixing the broken property/widget ID. Current local notes say a blocking snippet exists because the configured Tawk property is invalid. |

### P1 - Install if not already installed

| Plugin | Latest found | Use for Suriota |
|---|---:|---|
| Site Kit by Google | 1.179.0 | Best fit for Search Console, GA4, PageSpeed Insights, Tag Manager visibility from WP admin. Use alongside AIOSEO; do not duplicate meta/schema duties. |
| IndexNow Plugin | 1.0.3 | Useful for instant Bing/Yandex/Naver/Seznam update pings after page/slug/redirect changes. Does not replace Google Search Console. |
| UpdraftPlus | 1.26.4 | Production backup safety before plugin/core updates. Local repo has exports/backups, but a WP-native rollback path is still useful. |
| Wordfence Security | 8.2.1 | Recommended if no equivalent WAF/security plugin is active. Enable carefully to avoid blocking REST/MCP endpoints. |
| Cloudflare | 4.14.3 | Install only if DNS/CDN is Cloudflare or APO is planned. Useful for cache purge and edge HTML caching; avoid if host/CDN is different. |

### P2 - Local Codex skills to install

Curated skill list fetched from `openai/skills` shows these relevant options not installed as user skills:

| Skill | Recommendation |
|---|---|
| `playwright` | Install. The repo relies on screenshot and visual regression workflows. |
| `screenshot` | Install. Helpful for quick visual QA artifacts and before/after inspection. |
| `security-best-practices` | Install. Useful before WordPress/plugin updates and REST/MCP exposure reviews. |
| `security-threat-model` | Install. Useful for MCP/API credentials, WordPress Application Passwords, and admin endpoints. |
| `security-ownership-map` | Optional. Useful if the project grows more plugins/snippets and needs ownership boundaries. |
| `cloudflare-deploy` | Optional. Only install if Cloudflare is confirmed as DNS/CDN. |

Already covered in this Codex session: Browser, GitHub, Google Drive/Docs/Sheets/Slides, Documents, Presentations, Spreadsheets, `imagegen`, `openai-docs`, `skill-installer`, `skill-creator`, `plugin-creator`.

## Do Not Install

- Do not install Yoast SEO or Rank Math while AIOSEO is active. It increases duplicate meta/schema/sitemap risk.
- Do not install multiple cache/minify plugins at once. Pick one layer: WP-Optimize or host cache or Cloudflare APO, then verify.
- Do not add more Elementor addon packs unless a specific widget gap exists. This site already has many JS/CSS workarounds.
- Do not remove SX snippets until the matching upstream/root fix is verified.

## Local Package Updates

`npm outdated --json` found:

- `puppeteer`: current `24.43.1`, wanted `24.43.1`, latest `25.1.0`.

No update needed for:

- `@modelcontextprotocol/sdk`: current/latest `1.29.0`.
- `playwright`: current/latest `1.60.0`.

Recommended local action: defer Puppeteer major update unless scripts need it. Playwright is the primary audit dependency here.

## Suggested Update Order

1. Create WP-native backup and export Elementor templates/snippets.
2. Clone/stage site and verify PHP version, memory, REST API, Application Passwords, and MCP endpoint.
3. Update WordPress MCP Adapter to v0.5.0.
4. Update MCP Tools for Elementor and confirm tool list/connection.
5. Update Elementor core + Elementor Pro together.
6. Regenerate Elementor CSS/data, clear WP-Optimize/host/CDN cache.
7. Update AIOSEO, Polylang, Redirection, Code Snippets, WP-Optimize.
8. Add Site Kit and connect Search Console/GA4/PageSpeed/Tag Manager.
9. Add IndexNow only after sitemap/canonical/noindex state is stable.
10. Run Playwright desktop/mobile screenshots and schema/hreflang/sitemap checks.

## Sources

- WordPress versions: https://wordpress.org/documentation/article/wordpress-versions/
- Elementor plugin: https://wordpress.org/plugins/elementor/
- Elementor Pro changelog: https://elementor.com/old/pro/changelog/
- WordPress MCP Adapter releases: https://github.com/WordPress/mcp-adapter/releases
- Elementor MCP: https://github.com/msrbuilds/elementor-mcp
- AIOSEO: https://wordpress.org/plugins/all-in-one-seo-pack/
- Polylang: https://wordpress.org/plugins/polylang/
- Redirection: https://wordpress.org/plugins/redirection/
- Code Snippets: https://wordpress.org/plugins/code-snippets/
- WP-Optimize: https://wordpress.org/plugins/wp-optimize/
- Site Kit by Google: https://wordpress.org/plugins/google-site-kit/
- IndexNow: https://wordpress.org/plugins/indexnow/
- UpdraftPlus: https://wordpress.org/plugins/updraftplus/
- Wordfence: https://wordpress.org/plugins/wordfence/
- Cloudflare: https://wordpress.org/plugins/cloudflare/
- Tawk.To Live Chat: https://wordpress.org/plugins/tawkto-live-chat/
