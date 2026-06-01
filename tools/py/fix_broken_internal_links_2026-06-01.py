"""Fix 3 broken internal links (404) in Elementor pages (bucket A).
Path-substring replace in parsed _elementor_data; backup; dry-run default.
"""
import os, sys, json, pathlib, time
import requests
from requests.auth import HTTPBasicAuth
ROOT = pathlib.Path(__file__).resolve().parents[2]
ENV = {}
for line in (ROOT/".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k,v=line.split("=",1); ENV[k.strip()]=v.strip()
AUTH=HTTPBasicAuth("admin",ENV["WP_APP_PASS"])
PAGES="https://suriota.com/wp-json/wp/v2/pages"
BK=ROOT/"backups"/"2026-06-01"/"broken-links-fix"; BK.mkdir(parents=True,exist_ok=True)
EXECUTE="--execute" in sys.argv

# page_id -> list of (bad_path_substr, good_path_substr)
REPL = {
  5275: [("/renewable-energi/","/id/surge-energy-mapping-id/"),("/surge-energi-mapping/","/id/surge-energy-mapping-id/")],
  5276: [("/renewable-energi/","/id/surge-energy-mapping-id/"),("/surge-energi-mapping/","/id/surge-energy-mapping-id/")],
  5541: [("/自动化/","/zh/gongye-wulianwang-jicheng/")],
}

def get_ed(pid):
    r=requests.get(PAGES,auth=AUTH,params={"include":pid,"context":"edit","_fields":"id,slug,meta"},timeout=90)
    r.raise_for_status(); j=r.json(); return j[0]["slug"], j[0]["meta"]["_elementor_data"]

for pid,reps in REPL.items():
    slug,ed=get_ed(pid)
    tree=json.loads(ed)
    cnt={b:0 for b,_ in reps}
    def walk(n):
        if isinstance(n,dict):
            for k,v in list(n.items()):
                if isinstance(v,str):
                    for b,g in reps:
                        if b in v: cnt[b]+=v.count(b); n[k]=v.replace(b,g); v=n[k]
                else: walk(v)
        elif isinstance(n,list):
            for v in n: walk(v)
    walk(tree)
    new=json.dumps(tree,ensure_ascii=False,separators=(",",":"))
    json.loads(new)  # validate
    print(f"[{pid}] {slug}: " + ", ".join(f"{b} x{cnt[b]}" for b,_ in reps) + f"  ed_len {len(ed)}->{len(new)}")
    if EXECUTE and sum(cnt.values())>0:
        (BK/f"{pid}-before.json").write_text(ed,encoding="utf-8")
        r=requests.post(f"{PAGES}/{pid}",auth=AUTH,json={"meta":{"_elementor_data":new}},timeout=90)
        print(f"    POST {r.status_code}")
        time.sleep(0.4)
print("EXECUTED" if EXECUTE else "DRY RUN — re-run with --execute, then flush Elementor cache")
