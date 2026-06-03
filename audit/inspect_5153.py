import json, subprocess
import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
r=subprocess.run(["curl","-s","-u",AUTH,"https://suriota.com/wp-json/wp/v2/elementor_snippet/5153?context=edit"],capture_output=True,text=True)
d=json.loads(r.stdout)
# content location
content = d.get('content',{})
raw = content.get('raw') if isinstance(content,dict) else None
meta = d.get('meta',{})
# elementor snippet may store code in meta
print("top keys:", list(d.keys()))
print("content.raw len:", len(raw) if raw else 0)
print("meta keys:", list(meta.keys()))
# dump where the code is
code = raw or ''
for k,v in meta.items():
    if isinstance(v,str) and ('<h4' in v or 'Connect with Us' in v):
        print("CODE IN META KEY:", k, "len", len(v)); code=v
# save backup
open("audit/snippet_backup_2026-06-02/5153_orig.txt","w",encoding='utf-8').write(code)
import re
print("\n--- h4 occurrences with context ---")
for m in re.finditer(r'.{0,30}<h4[^>]*>(.*?)</h4>', code, re.S):
    print(repr(m.group(0)[:90]))
print("total <h4:", code.count('<h4'), " </h4>:", code.count('</h4>'))
