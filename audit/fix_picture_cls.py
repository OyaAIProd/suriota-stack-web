"""CLS fix: reserve space for EWWW <picture>-wrapped content images.

Root cause (PSI layout-shifts, 2026-06-03 after Optimized Markup): on the
portfolio/project/service post template, content images are EWWW-rewritten to
figure.wp-block-image > picture > img. The <picture> wrapper is display:inline
(no size), and Optimized Markup ('Improved CSS Loading') reordered the
wp-block-image stylesheet so the img aspect-ratio box isn't reserved before the
bytes load -> 'Media element lacking an explicit size' shift (+~0.05 desktop CLS
on ~40 pages: main#content/.page-content move down when the image lays out).

Fix (kit-5 custom_css, autonomous): make the <picture> a block so it reserves
the img's aspect-ratio box from first layout. Scoped to .page-content (post
content only) — does NOT touch Elementor widget images. Idempotent via marker.

  python audit/fix_picture_cls.py          # DRY (print resulting custom_css tail)
  python audit/fix_picture_cls.py apply     # write + verify + flush elementor css
"""
import json, subprocess, sys, os

WP_APP_PASS = next((l.split("=",1)[1].strip() for l in
                    open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..",".env"),encoding="utf-8")
                    if l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
KIT = "https://suriota.com/wp-json/wp/v2/elementor_library/5"

MARKER = "/* === SURIOTA CLS fix: wp-block-image picture wrapper"
CLS_CSS = """
/* === SURIOTA CLS fix: wp-block-image picture wrapper (EWWW Picture-WebP) 2026-06-03 ===
   <picture> is display:inline (no space reservation); make it block so the inner
   img's width/height attrs reserve the aspect-ratio box before the image loads.
   Scoped to .page-content (post content) — Elementor widget images untouched. */
.page-content figure.wp-block-image picture{display:block}
.page-content figure.wp-block-image img{height:auto;max-width:100%}
/* === end CLS fix === */
""".strip()


def get_ps():
    r = subprocess.run(["curl","-s","-u",AUTH,KIT+"?context=edit"], capture_output=True, text=True)
    d = json.loads(r.stdout)
    ps = d['meta']['_elementor_page_settings']
    if isinstance(ps, str):
        ps = json.loads(ps)
    return ps


def main():
    ps = get_ps()
    old = ps.get('custom_css','') or ''
    if MARKER in old:                       # idempotent: strip prior copy
        old = old[:old.index(MARKER)].rstrip()
    ps['custom_css'] = (old + "\n" + CLS_CSS).strip()

    if sys.argv[1:] == ['apply']:
        body = json.dumps({"meta": {"_elementor_page_settings": ps}})
        r = subprocess.run(["curl","-s","-X","POST","-u",AUTH,"-H","Content-Type: application/json",
                            "--data-binary","@-",KIT], input=body, capture_output=True, text=True)
        try:
            print("PUT kit id=", json.loads(r.stdout).get('id'))
        except Exception:
            print("ERR:", r.stdout[:300]); sys.exit(1)
        ps2 = get_ps()
        print("readback has CLS block:", MARKER in (ps2.get('custom_css','') or ''))
        f = subprocess.run(["curl","-s","-u",AUTH,"-X","DELETE",
                            "https://suriota.com/wp-json/elementor/v1/cache","-o","/dev/null","-w","%{http_code}"],
                           capture_output=True, text=True)
        print("elementor flush http=", f.stdout)
        print("NOTE: now purge WP-Optimize page cache so HTML references the regenerated post-5.css.")
    else:
        print("DRY — resulting custom_css tail:\n")
        print(ps['custom_css'][-600:])


if __name__ == "__main__":
    main()
