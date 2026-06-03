import json, subprocess, re
import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
r=subprocess.run(["curl","-s","-u",AUTH,"https://suriota.com/wp-json/wp/v2/elementor_snippet?per_page=100&context=edit&status=publish"],capture_output=True,text=True)
d=json.loads(r.stdout)
for s in (d if isinstance(d,list) else []):
    c=json.dumps(s)
    if 'sx-related-pillar' in c or 'related-pillars' in c:
        pid=s.get('id'); code=s.get('meta',{}).get('_elementor_code','') or ''
        loc=s.get('meta',{}).get('_elementor_location','')
        print(f"=== snippet {pid} ({(s.get('title',{}) or {}).get('rendered','')[:30]}) loc={loc} codelen={len(code)} ===")
        # injection mechanism
        for m in re.finditer(r'(insertBefore|appendChild|prepend|insertAdjacent\w*|\.before\(|\.after\(|querySelector\([^)]*\)|\.innerHTML)', code):
            print("   inj:", m.group(0)[:60])
        # min-height / height on container
        for m in re.finditer(r'\.sx-related-pillars[^{]*\{[^}]*\}', code):
            t=m.group(0).replace('\n',' ')
            if 'height' in t or 'min-height' in t or 'margin' in t: print("   css:", t[:120])
