"""Fix 5 broken external Wikipedia links (bucket C) in Gutenberg posts.
Replace bad WP article URL with verified 200 one in post content.raw. Dry-run default.
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
POSTS="https://suriota.com/wp-json/wp/v2/posts"
BK=ROOT/"backups"/"2026-06-01"/"broken-links-fix"; BK.mkdir(parents=True,exist_ok=True)
EXECUTE="--execute" in sys.argv
W="https://en.wikipedia.org/wiki/"
# slug -> (bad_url, good_url)
FIX={
 "electrical-testing-instalasi-electrical-testing-avanti-coffee": (W+"Electrical_installation_testing", W+"Electrical_wiring"),
 "pemesinan-kontur-kompleks-machining-7-tefa-smkn6-batam": (W+"Multi-axis_machining", W+"Multiaxis_machining"),
 "pemesinan-multi-proses-cnc-machining-4-tefa-smkn6-batam": (W+"Turning_(machining)", W+"Turning"),
 "setup-genset-dse-5520": (W+"Automatic_mains_failure", W+"Automatic_transfer_switch"),
 "sistem-kapasitor-bank-automatic-iot-based-mini-capacitor-bank-system": (W+"Capacitor_bank", W+"Capacitor"),
}
for slug,(bad,good) in FIX.items():
    r=requests.get(POSTS,auth=AUTH,params={"slug":slug,"context":"edit","_fields":"id,content"},timeout=60)
    j=r.json()
    if not j: print(f"[?] {slug}: NOT FOUND"); continue
    pid=j[0]["id"]; raw=j[0]["content"]["raw"]
    n=raw.count(bad)
    print(f"[{pid}] {slug}: '{bad.split('/')[-1]}' x{n} -> {good.split('/')[-1]}")
    if EXECUTE and n>0:
        (BK/f"post-{pid}-wiki-before.html").write_text(raw,encoding="utf-8")
        new=raw.replace(bad,good)
        rr=requests.post(f"{POSTS}/{pid}",auth=AUTH,json={"content":new},timeout=90)
        print(f"    POST {rr.status_code}")
        time.sleep(0.4)
print("EXECUTED" if EXECUTE else "DRY RUN — re-run with --execute")
