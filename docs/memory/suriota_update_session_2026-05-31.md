---
name: suriota-update-session-2026-05-31
description: WordPress/Codex skill/plugin update snapshot before Codex restart
type: project
originSessionId: 2026-05-31-update-session
---

## Summary

User asked to update all relevant WordPress/Codex skills/plugins and agreed not to install conflicting plugins.

Do **not** install Yoast, Rank Math, duplicate cache/minify plugins, or extra Elementor addon packs unless explicitly requested.

## Live WordPress Versions After Update

- WordPress core: `7.0`
- Elementor: `4.1.1`
- Elementor Pro: `4.1.0`
- AIOSEO: `4.9.7.2`
- Polylang: `3.8.4`
- Redirection: `5.7.5`
- WP-Optimize: `4.5.4`
- EWWW Image Optimizer: `8.7.0`
- WP Mail SMTP: `4.8.0`
- WP Table Builder: `2.1.14`
- Tawk.to Live Chat: `0.9.3`
- MCP Adapter: `0.5.0` updated from `0.4.1`
- MCP Tools for Elementor: `1.7.4` updated from `1.4.3`

## MCP Verification

- MCP initialize endpoint returned HTTP 200.
- MCP `tools/list` requires the `Mcp-Session-Id` header returned by initialize under MCP Adapter v0.5.0.
- `tools/list` returned HTTP 200 and `113` tools.
- Homepage returned HTTP 200 after update.

## Backup

Pre-update REST backup:

- `backups/2026-05-31`

It includes Elementor snippets, pages, posts, redirects, AIOSEO options, media metadata, plugins, and themes.

## Elementor MCP Upload Detail

Official Elementor MCP v1.7.4 ZIP failed through WP Admin upload with:

- `413 Request Entity Too Large`

The helper script minimized the package from `1368377` bytes to `894507` bytes by removing optional language packs, docs/sample prompts, and Freemius pricing media. The core plugin files were preserved, upload succeeded, and WordPress reports Elementor MCP `1.7.4` active.

## Codex Skills Installed

- `playwright`
- `screenshot`
- `security-best-practices`
- `security-threat-model`
- `security-ownership-map`

Restart Codex to load these skills.

## Local Node State

- `@modelcontextprotocol/sdk@1.29.0`
- `playwright@1.60.0`
- `puppeteer@25.1.0`

`npm outdated --json` returned `{}`.

## Files Added / Modified

- Added `docs/skill-plugin-update-audit-2026-05-31.md`
- Added `tools/py/wp_update_github_plugins.py`
- Added `backups/2026-05-31/`
- Added `package-lock.json`
- Modified `package.json`
- Modified `docs/AGENTS.md`
- `.gitignore` has `tmp/` added; check before attributing ownership.

## Helper

`tools/py/wp_update_github_plugins.py`:

- Creates a temporary WP admin via REST Application Password.
- Logs into WP Admin with cookie auth.
- Uploads GitHub release ZIPs.
- Confirms WordPress "Replace current with uploaded".
- Deletes the temporary admin user.

No temporary `codex_update_*` admin users were left behind after the run.

## Credential Safety

`.env` contains WordPress credentials/Application Password. Do not echo secrets in chat.
