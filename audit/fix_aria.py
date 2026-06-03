import json, re, subprocess, sys, os

import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
BASE = "https://suriota.com/wp-json/wp/v2/pages"
BK = "audit/elementor_backup_2026-06-02"
os.makedirs(BK, exist_ok=True)

PAGES = {934:"modbus", 929:"waste-water", 1740:"iso-m485", 1741:"thm-30md", 1742:"pm1611-wd", 1765:"spd-t485"}
mode = sys.argv[1] if len(sys.argv) > 1 else "dry"

def fetch(pid):
    r = subprocess.run(["curl","-s","-u",AUTH,f"{BASE}/{pid}?context=edit"], capture_output=True, text=True)
    return json.loads(r.stdout)

def transform(data):
    # operate on escaped aria-label attributes inside the JSON string
    n = 0
    def p(m):
        nonlocal n; n += 1
        return 'aria-label=\\"Order on Tokopedia — ' + m.group(1) + '\\"'
    data = re.sub(r'aria-label=\\"Order ([^"\\]+?) on Tokopedia\\"', p, data)
    def s(m):
        nonlocal n; n += 1
        return 'aria-label=\\"Download Datasheet — ' + m.group(1) + '\\"'
    data = re.sub(r'aria-label=\\"Download ([^"\\]+?) datasheet(?: PDF)?\\"', s, data)
    return data, n

def visible_spans(data):
    out = {}
    for m in re.finditer(r'<a class=\\"sx-action-btn[^>]*?aria-label=\\"([^"\\]+)\\".*?</a>', data, re.S):
        block = m.group(0)
        vis = re.sub(r'<svg.*?</svg>', '', block, flags=re.S)
        vis = re.sub(r'<[^>]+>', '', vis).replace('\\n',' ').replace('→','').strip()
        vis = re.sub(r'\s+',' ',vis)
        out[m.group(1)] = vis
    return out

for pid, name in PAGES.items():
    d = fetch(pid)
    data = d['meta']['_elementor_data']
    open(f"{BK}/{pid}_{name}_orig.json","w",encoding='utf-8').write(json.dumps(data, ensure_ascii=False))
    new, n = transform(data)
    vis_old = visible_spans(data)
    vis_new = visible_spans(new)
    print(f"\n[{pid} {name}] replacements={n}")
    for aria, vis in vis_new.items():
        ok = vis in aria
        print(f"   {'OK ' if ok else 'FAIL'} visible={vis!r}  aria={aria!r}")
    if mode == "apply" and n > 0:
        body = json.dumps({"meta": {"_elementor_data": new}})
        r = subprocess.run(["curl","-s","-X","POST","-u",AUTH,"-H","Content-Type: application/json","--data-binary","@-",f"{BASE}/{pid}"],
                           input=body, capture_output=True, text=True)
        try:
            res = json.loads(r.stdout); print(f"   PUT -> id={res.get('id')} modified={res.get('modified')}")
        except Exception:
            print("   PUT ERR:", r.stdout[:200])
