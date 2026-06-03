import json, subprocess, sys

import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
BASE = "https://suriota.com/wp-json/wp/v2/elementor_snippet/5656"

r = subprocess.run(["curl","-s","-u",AUTH,BASE+"?context=edit"], capture_output=True, text=True)
d = json.loads(r.stdout)
code = d['meta']['_elementor_code']
open("audit/snippet_backup_2026-06-02/5656_pre_cls.txt","w",encoding='utf-8').write(code)

OLD = """    var target = null;
    if (faq) {
      target = faq.closest('.elementor-section') || faq.closest('section') || faq.parentElement;
    }
    if (!target) {
      // Fallback: insert before footer
      target = document.querySelector('footer') || document.body.lastElementChild;
    }"""

NEW = """    var target = null;
    // CLS fix: always insert just before the footer (end of content) instead of
    // before the FAQ section, so injecting it only shifts the below-the-fold footer.
    target = document.querySelector('footer') || document.body.lastElementChild;"""

if OLD not in code:
    print("OLD block NOT found — aborting (check whitespace).")
    sys.exit(1)

new = code.replace(OLD, NEW)
print("replacement done; len", len(code), "->", len(new))

if sys.argv[1:] == ['apply']:
    body = json.dumps({"meta": {"_elementor_code": new}})
    r2 = subprocess.run(["curl","-s","-X","POST","-u",AUTH,"-H","Content-Type: application/json","--data-binary","@-",BASE],
                        input=body, capture_output=True, text=True)
    try:
        res = json.loads(r2.stdout); print("PUT id=", res.get('id'), "modified=", res.get('modified'))
    except Exception:
        print("ERR:", r2.stdout[:300])
else:
    print("DRY (pass 'apply' to write)")
