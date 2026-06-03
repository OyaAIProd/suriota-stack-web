import json, subprocess, sys

import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
BASE = "https://suriota.com/wp-json/wp/v2/pages/12"
Q = chr(92) + '"'   # the escaped quote sequence \"  as it appears in the JSON string

LABELS = [
    "Industrial IoT & System Integration",
    "AI & Industrial Analytics",
    "Digital Transformation Consulting",
    "Industrial Engineering & Automation",
    "SURGE SaaS Platform",
]

d = json.load(open('audit/elementor_backup_2026-06-02/p12_home_orig.json', encoding='utf-8'))
s = d['meta']['_elementor_data']
new = s
removed = 0
for lab in LABELS:
    # the attribute appears as: aria-label=\"LABEL\"  (with a leading space)
    needle = ' aria-label=' + Q + lab + Q
    c = new.count(needle)
    if c == 0:
        # try the &amp; HTML-entity form for the ampersand
        lab2 = lab.replace('&', '&amp;')
        needle = ' aria-label=' + Q + lab2 + Q
        c = new.count(needle)
    if c != 1:
        print(f"  WARN '{lab}' count={c}")
    new = new.replace(needle, '')
    removed += c

print("aria-labels removed:", removed)
if sys.argv[1:] == ['apply'] and removed:
    body = json.dumps({"meta": {"_elementor_data": new}})
    r = subprocess.run(["curl","-s","-X","POST","-u",AUTH,"-H","Content-Type: application/json","--data-binary","@-",BASE],
                       input=body, capture_output=True, text=True)
    try:
        res = json.loads(r.stdout); print("PUT id=", res.get('id'), "modified=", res.get('modified'))
    except Exception:
        print("ERR:", r.stdout[:300])
