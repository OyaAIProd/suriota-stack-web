import json, subprocess
import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
for pid in [1079,1144,1151]:
    r=subprocess.run(["curl","-s","-u",AUTH,f"https://suriota.com/wp-json/wp/v2/elementor_library/{pid}?context=edit"],capture_output=True,text=True)
    try:
        d=json.loads(r.stdout); s=d['meta']['_elementor_data']
        h4=s.count('"header_size":"h4"'); h2=s.count('"header_size":"h2"')
        has=('Our Services' in s, 'Connect with Us' in s)
        print(f"[{pid}] h4={h4} h2={h2} hasOurServices/Connect={has} title={(d.get('title',{}) or {}).get('rendered','')}")
    except Exception as e:
        print(pid,"ERR",r.stdout[:120])
