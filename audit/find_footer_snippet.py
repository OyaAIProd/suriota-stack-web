import json, subprocess
import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
r=subprocess.run(["curl","-s","-u",AUTH,"https://suriota.com/wp-json/wp/v2/elementor_snippet?per_page=100&context=edit&status=publish"],capture_output=True,text=True)
d=json.loads(r.stdout)
print("total snippets:", len(d) if isinstance(d,list) else d)
for s in (d if isinstance(d,list) else []):
    pid=s.get('id')
    # content may be in content.raw or meta
    c=json.dumps(s)
    hit_cw = 'Connect with Us' in c
    hit_os = 'Our Services' in c
    h4 = c.count('<h4')
    if hit_cw or (hit_os and h4):
        print(f"  snippet {pid} title={(s.get('title',{}) or {}).get('rendered','')[:30]} ConnectWithUs={hit_cw} OurServices={hit_os} h4count~={h4}")
