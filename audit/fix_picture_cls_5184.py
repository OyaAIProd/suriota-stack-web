"""CLS fix in the RIGHT carrier: snippet 5184 (SX/V3 Article Layout - All Single
Posts Sitewide) outputs <style id=sxa-css-sitewide> on every single-post/portfolio
page (NON-Elementor -> kit-5 custom_css does NOT load there). It styles figure /
.wp-block-image but has NO rule for the EWWW <picture> wrapper, which is
display:inline => no space reservation => 'Media element lacking explicit size'
shift (+~0.05 desktop CLS on ~40 pages after Optimized Markup).

Inserts a picture{display:block} reservation rule right after the existing
figure-margin rule, inside the sxa-css-sitewide <style>. Idempotent via marker.
Snippet edits go LIVE via REST immediately (no Elementor flush); page-cache
purge still needed for cached HTML.

  python audit/fix_picture_cls_5184.py        # DRY
  python audit/fix_picture_cls_5184.py apply
"""
import json, subprocess, sys, os

WP_APP_PASS = next((l.split("=",1)[1].strip() for l in
                    open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"..",".env"),encoding="utf-8")
                    if l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
SNIP = "https://suriota.com/wp-json/wp/v2/elementor_snippet/5184"

ANCHOR = "body.single-post .sxa-main figure,body.single-post .sxa-main .wp-block-image{margin:32px 0}"
MARKER = "/*SXA-CLS-FIX*/"
FIX = (MARKER +
       ".page-content figure.wp-block-image picture{display:block}"
       ".page-content figure.wp-block-image img{height:auto;max-width:100%}"
       "/*end-SXA-CLS-FIX*/")


def get_code():
    r = subprocess.run(["curl","-s","-u",AUTH,SNIP+"?context=edit"], capture_output=True, text=True)
    d = json.loads(r.stdout)
    code = d['meta']['_elementor_code']
    was_list = isinstance(code, list)
    if was_list:
        code = code[0] if code else ''
    return d, code, was_list


def main():
    d, code, was_list = get_code()
    if ANCHOR not in code:
        sys.exit("ANCHOR rule not found in snippet 5184 — aborting (snippet changed).")
    # idempotent strip
    if MARKER in code:
        import re
        code = re.sub(re.escape(MARKER) + r".*?/\*end-SXA-CLS-FIX\*/", "", code, flags=re.S)
    new = code.replace(ANCHOR, ANCHOR + FIX, 1)

    if sys.argv[1:] == ['apply']:
        meta_val = [new] if was_list else new
        body = json.dumps({"meta": {"_elementor_code": meta_val}})
        r = subprocess.run(["curl","-s","-X","POST","-u",AUTH,"-H","Content-Type: application/json",
                            "--data-binary","@-",SNIP], input=body, capture_output=True, text=True)
        try:
            print("PUT snippet id=", json.loads(r.stdout).get('id'))
        except Exception:
            print("ERR:", r.stdout[:300]); sys.exit(1)
        _, code2, _ = get_code()
        print("readback has fix:", MARKER in code2)
    else:
        i = new.index(MARKER)
        print("DRY — insertion context:\n", new[i-80:i+220])


if __name__ == "__main__":
    main()
