"""Bucket Y: replace internal redirect-hop links with canonical targets (clear ones only).
Sweeps all pages (_elementor_data) + posts (content.raw). Path-substring replace in
parsed/raw string. Dry-run default. Ambiguous slugs intentionally NOT touched.
"""
import os, sys, json, pathlib, time
import requests
from requests.auth import HTTPBasicAuth
ROOT=pathlib.Path(__file__).resolve().parents[2]
ENV={}
for line in (ROOT/".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k,v=line.split("=",1); ENV[k.strip()]=v.strip()
AUTH=HTTPBasicAuth("admin",ENV["WP_APP_PASS"])
BASE="https://suriota.com/wp-json/wp/v2"
BK=ROOT/"backups"/"2026-06-01"/"redirect-hop-fix"; BK.mkdir(parents=True,exist_ok=True)
EXECUTE="--execute" in sys.argv

# clear canonical mappings only (leading+trailing slash to avoid partial matches)
MAP={
 "/automation/":"/industrial-engineering-automation/",
 "/internet-of-things/":"/industrial-iot-system-integration/",
 "/data-analytics/":"/ai-industrial-analytics/",
 "/software-as-a-service/":"/surge-saas-platform/",
 "/digital-consulting/":"/digital-transformation-consulting/",
 "/waste-water-loger/":"/waste-water-logger/",
}

def fetch_all(kind, field):
    out,page=[],1
    while True:
        r=requests.get(f"{BASE}/{kind}",auth=AUTH,params={"per_page":100,"page":page,"context":"edit","_fields":f"id,slug,{field}"},timeout=90)
        if r.status_code!=200: break
        ch=r.json()
        if not ch: break
        out+=ch
        if len(ch)<100: break
        page+=1
    return out

def repl_count(s):
    c=0
    for b,g in MAP.items(): c+=s.count(b)
    return c
def repl(s):
    for b,g in MAP.items(): s=s.replace(b,g)
    return s

total_pages=total_posts=0
def do(kind, field):
    global total_pages,total_posts
    items=fetch_all(kind, field)
    print(f"-- {kind}: {len(items)} scanned --")
    for it in items:
        if field=="meta": val=(it.get("meta") or {}).get("_elementor_data") or ""
        else: val=(it.get(field) or {}).get("raw","") if isinstance(it.get(field),dict) else ""
        if not isinstance(val,str): continue
        n=repl_count(val)
        if n==0: continue
        newval=repl(val)
        if field=="meta": json.loads(newval)  # validate elementor json
        print(f"  [{it['id']}] {it['slug']}: {n} hop-link(s)")
        if kind=="pages": total_pages+=1
        else: total_posts+=1
        if EXECUTE:
            (BK/f"{kind}-{it['id']}-before.txt").write_text(val,encoding="utf-8")
            body={"meta":{"_elementor_data":newval}} if field=="meta" else {"content":newval}
            r=requests.post(f"{BASE}/{kind}/{it['id']}",auth=AUTH,json=body,timeout=90)
            print(f"      POST {r.status_code}"); time.sleep(0.4)

do("pages","meta")
do("posts","content")
print(f"\n{'EXECUTED' if EXECUTE else 'DRY RUN'} — pages={total_pages} posts={total_posts} to change")
