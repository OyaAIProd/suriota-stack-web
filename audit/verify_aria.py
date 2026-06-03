import json, re, subprocess
import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
r=subprocess.run(["curl","-s","-u",AUTH,"https://suriota.com/wp-json/wp/v2/pages/934?context=edit"],capture_output=True,text=True)
d=json.loads(r.stdout); s=d['meta']['_elementor_data']
pat = 'aria-label=' + chr(92) + '"'
arias=[]
i=0
while True:
    j=s.find(pat,i)
    if j<0: break
    k=s.find(chr(92)+'"', j+len(pat))
    arias.append(s[j+len(pat):k])
    i=k+1
print("modbus arias now:", arias)
