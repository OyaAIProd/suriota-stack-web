import json, subprocess
import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
BASE="https://suriota.com/wp-json/wp/v2/elementor_snippet/5153"
code=open('audit/snippet_backup_2026-06-02/5153_orig.txt',encoding='utf-8').read()
reps=[
 ('<h4>Our Services</h4>','<h2>Our Services</h2>'),
 ('<h4>Products</h4>','<h2>Products</h2>'),
 ('<h4>Connect with Us</h4>','<h2>Connect with Us</h2>'),
 ('.sx-hf-v5-col h4{','.sx-hf-v5-col h2{'),
]
new=code; n=0
for a,b in reps:
    c=new.count(a); 
    if c!=1: print(f"WARN '{a[:30]}' count={c}")
    new=new.replace(a,b); n+=c
print("total replacements:", n, "| remaining <h4:", new.count('<h4'), "| col h4 selector:", new.count('.sx-hf-v5-col h4'))
body=json.dumps({"meta":{"_elementor_code":new}})
r=subprocess.run(["curl","-s","-X","POST","-u",AUTH,"-H","Content-Type: application/json","--data-binary","@-",BASE],input=body,capture_output=True,text=True)
try:
    res=json.loads(r.stdout); print("PUT id=",res.get('id'),"modified=",res.get('modified'))
except Exception: print("ERR:",r.stdout[:300])
