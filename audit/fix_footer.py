import json, subprocess
import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
BASE="https://suriota.com/wp-json/wp/v2/elementor_library/1079"
d=json.load(open('audit/elementor_backup_2026-06-02/footer_1079_orig.json',encoding='utf-8'))
s=d['meta']['_elementor_data']
n=s.count('"header_size":"h4"')
new=s.replace('"header_size":"h4"','"header_size":"h2"')
print("h4->h2 replacements:", n)
body=json.dumps({"meta":{"_elementor_data":new}})
r=subprocess.run(["curl","-s","-X","POST","-u",AUTH,"-H","Content-Type: application/json","--data-binary","@-",BASE],
                 input=body,capture_output=True,text=True)
try:
    res=json.loads(r.stdout); print("PUT id=",res.get('id'),"modified=",res.get('modified'))
except Exception:
    print("ERR:",r.stdout[:300])
