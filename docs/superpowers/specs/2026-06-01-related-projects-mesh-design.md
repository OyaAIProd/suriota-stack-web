# Related-Projects Internal-Link Mesh — Design Spec

**Date:** 2026-06-01
**Author:** Gifari Suriota (CEO) + Claude
**Status:** Approved design, pre-implementation

## Problem

GSC "Crawled – currently not indexed" affects portfolio project posts. Root cause (audited 2026-06-01): the 64 project posts are **internally orphaned** — `/portfolio/` exposes 0 static links to them, and the existing "Related Pillars" snippet (5656) builds links **client-side via JS** (weak crawl signal). Posts are in the sitemap and return 200 with good content, but lack server-rendered inbound internal links, so Google deprioritizes indexing.

## Goal

Give every project post **server-rendered, topically-relevant inbound + outbound internal links** by appending a "Related Projects" block to each post's content. This distributes internal link equity, adds topical context, and bumps `modified` → sitemap lastmod → triggers recrawl.

Non-goal: changing theme/plugin PHP, the portfolio page layout, or the JS pillar snippet.

## Audit findings (validated)

- **64/64 project posts are Gutenberg** (0 Elementor) → uniformly editable via REST `/wp/v2/posts/{id}`.
- **No code-snippets plugin, no child theme** → a PHP `the_content` filter would need risky file-write deploy (MCP file tools down). Rejected in favor of REST content-injection.
- **All 64 are single-language** (default/EN; Polylang `?lang=` returns 64 for all langs, one category set 122–129) → no language-awareness needed.
- **64/64 posts have tags** → tag-based related selection always viable.
- Category sizes: 123→14, 128→14, 127→10, 124→8, 126→7, 129→5, 125→4, **122→1, 164→1** (two singletons need tag fallback).
- Cache (WP-Optimize) auto-purges on post save (observed). Edits reflect live.
- 8 posts already carry the block from the 2026-06-01 first pass (ids 1443,1470,2266,2036,2022,2122,1464,1458).

## Approach (chosen: A — REST content-injection)

A single idempotent, reversible Python script: `tools/py/related_projects_mesh_2026-06-01.py`.

### Selection algorithm (per post P)
1. Candidates = other posts sharing ≥1 **category** with P.
2. Rank by: shared-category count ↓, shared-tag count ↓, date ↓.
3. If < 4 same-category candidates (singletons), augment with posts sharing ≥1 **tag** (rank by tag-overlap ↓).
4. Take **top 4**; exclude self.

### Balancing (anti-orphan)
After computing all outbound lists, tally **inbound** per post (counting links from the 8 pre-existing blocks too, parsed from their content). For any post with **< 2 inbound**, inject it into the related list of its closest tag-match post (replacing that post's weakest/4th link). Guarantees every post ≥ 2 inbound.

### Block markup (identical to first-pass)
```
<!-- wp:html -->
<aside class="sx-related-projects" style="margin:48px auto 8px;max-width:900px;padding:24px 0 0;border-top:1px solid #EAEFF1;">
  <p style="font:600 11px/1 'Geist Mono',ui-monospace,monospace;letter-spacing:.16em;text-transform:uppercase;color:#95A4AB;margin:0 0 14px;">Related Projects</p>
  <ul style="list-style:none;margin:0;padding:0;display:grid;gap:10px;">
    <li><a href="{permalink}" style="color:#0E2530;font:600 15px/1.45 'Geist',system-ui,sans-serif;text-decoration:none;">{title} →</a></li>
    ... ×4
  </ul>
</aside>
<!-- /wp:html -->
```
Server-rendered, user-visible, no JS.

## Safety / guardrails

- **Scope-locked:** operates only on the 64 `post`-type project posts. Never touches pages, pillars, or other post types.
- **Idempotent:** skips any post already containing marker `sx-related-projects` (the 8 done).
- **Append-only:** `content.raw.rstrip() + "\n\n" + block` — preserves all existing blocks incl. trailing JSON-LD `wp:html`.
- **Backup before write:** each post's `content.raw` → `backups/2026-06-01/related-links/<id>-before.html`.
- **Rate-limit friendly:** ~0.4s sleep between writes.
- **Fault isolation:** per-post try/except; one failure logs and continues, never aborts the batch.
- **No production code:** zero PHP/plugin/theme changes → no fatal-error risk to other pages.

## Execution flow (2-phase, validate first)

1. **`--dry-run`** (no writes): print per-post plan (P → 4 related), inbound distribution, count of posts to edit vs skipped, and any post still < 2 inbound. Review gate.
2. After approval → run (backup + append + POST), ~0.4s spacing.
3. **Post-run validation:** re-fetch a sample of edited posts' live HTML → confirm block renders, links resolve 200, content length sane (not truncated/broken), and inbound coverage met.

## Rollback

`--revert` mode: read `backups/2026-06-01/related-links/<id>-before.html` for every edited post and PUT the original `content.raw` back. Full restoration.

## Success criteria

- Every project post has a server-rendered Related Projects block with 4 valid links.
- Every post has ≥ 2 inbound internal links from sibling posts.
- No page (project or otherwise) broken; spot-checks return 200 with intact layout.
- The 4 GSC "crawled-not-indexed" posts retain/gain inbound links + fresh `modified`.
