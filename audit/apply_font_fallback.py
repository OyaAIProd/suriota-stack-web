import json, subprocess, sys
import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
SNIP='https://suriota.com/wp-json/wp/v2/elementor_snippet/5411'
orig=json.load(open('audit/snippet_backup_2026-06-03/5411_orig.json',encoding='utf-8'))
code=orig['meta']['_elementor_code']

FACES = (
"@font-face{font-family:'Geist-fallback';src:local('Roboto'),local('Arial'),local('Helvetica Neue');"
"size-adjust:121.67%;ascent-override:82.6%;descent-override:24.25%;line-gap-override:0%}\n"
"@font-face{font-family:'Geist-Mono-fallback';src:local('Courier New'),local('DejaVu Sans Mono'),local('Liberation Mono');"
"size-adjust:99.98%;ascent-override:100.52%;descent-override:29.5%;line-gap-override:0%}\n"
)

# idempotency: bail if already applied
if 'Geist-fallback' in code:
    print('ALREADY APPLIED — aborting to avoid double-insert'); sys.exit(0)

# 1) insert @font-face right after the opening style tag
anchor='<style id="sx-geist-fonts">\n'
assert anchor in code, 'style anchor not found'
new = code.replace(anchor, anchor + FACES, 1)

# 2) insert metric fallback into every Geist sans + mono literal stack
n_sans = new.count("'Geist', system-ui")
n_mono = new.count("'Geist Mono', ui-monospace")
new = new.replace("'Geist', system-ui", "'Geist', 'Geist-fallback', system-ui")
new = new.replace("'Geist Mono', ui-monospace", "'Geist Mono', 'Geist-Mono-fallback', ui-monospace")

print('sans stacks patched:', n_sans, '| mono stacks patched:', n_mono)

if sys.argv[1:]==['apply']:
    body=json.dumps({'meta':{'_elementor_code':new}})
    r=subprocess.run(['curl','-s','-X','POST','-u',AUTH,'-H','Content-Type: application/json','--data-binary','@-',SNIP],
                     input=body,capture_output=True,text=True)
    res=json.loads(r.stdout)
    r2=subprocess.run(['curl','-s','-u',AUTH,SNIP+'?context=edit'],capture_output=True,text=True)
    rb=json.loads(r2.stdout)['meta']['_elementor_code']
    print('PUT id',res.get('id'),'| @font-face Geist-fallback:', rb.count("font-family:'Geist-fallback'"),
          '| sans-fallback refs:', rb.count("'Geist-fallback'"), '| mono-fallback refs:', rb.count("'Geist-Mono-fallback'"))
else:
    print('DRY. preview stacks:')
    import re
    for m in re.findall(r"font-family:[^;}]*Geist[^;}]*", new)[:6]:
        print('  ', m.strip()[:90])
