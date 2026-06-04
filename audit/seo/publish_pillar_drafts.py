#!/usr/bin/env python3
"""Publish the commissioning pillar drafts (ID/EN/ZH) to WordPress as DRAFTS.

Reads docs/seo-content/commissioning-pillar-*.md, strips the leading meta comment
(extracting slug/title-tag/meta-desc) and the trailing FAQ JSON-LD comment
(re-injected as an active <script>), converts the markdown body to HTML, and
creates a status=draft post via the WP REST API (App Password auth).

Idempotent-ish: if a draft/post with the same slug exists, it UPDATES it instead
of creating a duplicate. Prints post IDs + wp-admin edit links + the AIOSEO
title/description to paste manually (AIOSEO Lite has no REST write).

  python audit/seo/publish_pillar_drafts.py
"""
import json, re, sys
from pathlib import Path

import requests
import markdown as md

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "seo-content"

FILES = [
    ("id", DOCS / "commissioning-pillar-id.md"),
    ("en", DOCS / "commissioning-pillar-en.md"),
    ("zh", DOCS / "commissioning-pillar-zh.md"),
]


def envval(name):
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith(name + "="):
            v = line.split("=", 1)[1]
            if " #" in v:
                v = v.split(" #", 1)[0]
            return v.strip().strip('"').strip("'")
    return None


def parse_meta(comment):
    def grab(label):
        m = re.search(rf"{label}\s*:\s*(.+)", comment)
        return m.group(1).strip() if m else None
    return {
        "slug": (grab("Slug") or "").split()[0] if grab("Slug") else None,
        "title_tag": grab("Title tag"),
        "meta_desc": grab("Meta desc"),
    }


def split_doc(text):
    """Return (meta_dict, faq_jsonld_or_None, body_markdown)."""
    comments = re.findall(r"<!--(.*?)-->", text, flags=re.DOTALL)
    meta = parse_meta(comments[0]) if comments else {}
    faq = None
    for c in comments:
        if '"@type": "FAQPage"' in c or '"@type":"FAQPage"' in c:
            j = re.search(r"\{.*\}", c, flags=re.DOTALL)
            if j:
                faq = j.group(0).strip()
    # strip ALL html comments from the body
    body = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL).strip()
    return meta, faq, body


def md_to_html(body):
    # drop the H1 (becomes the WP post title), keep the rest
    lines = body.splitlines()
    title = None
    out = []
    for ln in lines:
        if title is None and ln.startswith("# "):
            title = ln[2:].strip()
            continue
        out.append(ln)
    html = md.markdown("\n".join(out), extensions=["extra", "sane_lists"])
    return title, html


def find_existing(s, base, slug):
    r = s.get(f"{base}/wp-json/wp/v2/posts",
              params={"slug": slug, "status": "draft,publish,pending,private"}, timeout=30)
    if r.status_code == 200 and r.json():
        return r.json()[0]["id"]
    return None


def main():
    base = (envval("WP_BASE") or "https://suriota.com").rstrip("/")
    user = envval("WP_USER") or "admin"
    app = envval("WP_APP_PASS")
    if not app:
        sys.exit("WP_APP_PASS not in .env")

    s = requests.Session()
    s.auth = (user, app)
    s.headers.update({"Content-Type": "application/json"})

    print(f"WP: {base} as {user}\n")
    results = []
    for lang, path in FILES:
        if not path.exists():
            print(f"SKIP {lang}: {path} missing")
            continue
        meta, faq, body = split_doc(path.read_text(encoding="utf-8"))
        title, html = md_to_html(body)
        if faq:
            html += f'\n<!-- FAQ schema -->\n<script type="application/ld+json">\n{faq}\n</script>'

        payload = {
            "title": title,
            "slug": meta.get("slug", "").strip("/").split("/")[-1] or None,
            "content": html,
            "excerpt": meta.get("meta_desc") or "",
            "status": "draft",
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        existing = find_existing(s, base, payload.get("slug", "")) if payload.get("slug") else None
        if existing:
            r = s.post(f"{base}/wp-json/wp/v2/posts/{existing}", data=json.dumps(payload), timeout=60)
            action = f"UPDATED #{existing}"
        else:
            r = s.post(f"{base}/wp-json/wp/v2/posts", data=json.dumps(payload), timeout=60)
            action = "CREATED"

        if r.status_code in (200, 201):
            d = r.json()
            results.append((lang, d["id"], d.get("slug"), meta))
            print(f"[{lang}] {action} id={d['id']}  slug={d.get('slug')}")
            print(f"      edit: {base}/wp-admin/post.php?post={d['id']}&action=edit")
        else:
            print(f"[{lang}] FAIL HTTP {r.status_code}: {r.text[:200]}")

    print("\n=== AIOSEO meta to paste manually (AIOSEO Lite has no REST write) ===")
    for lang, pid, slug, meta in results:
        print(f"\n[{lang}] post #{pid}")
        print(f"  SEO Title : {meta.get('title_tag')}")
        print(f"  Meta Desc : {meta.get('meta_desc')}")
    print("\nNEXT: review drafts in wp-admin → set AIOSEO title/desc → link the 3 as")
    print("translations in Polylang → add internal links → Publish.")


if __name__ == "__main__":
    main()
