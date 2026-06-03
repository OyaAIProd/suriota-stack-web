import subprocess, time
import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
GB="Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)"
pages={12:"https://suriota.com/",934:"https://suriota.com/suriota-modbus-gateway/",
1741:"https://suriota.com/thm-30md/",1742:"https://suriota.com/pm1611-wd/",
1740:"https://suriota.com/iso-m485-series/",1765:"https://suriota.com/rs-485-surge-protector-spd-t485-105/",
929:"https://suriota.com/waste-water-logger/",5554:"https://suriota.com/industrial-iot-system-integration/",
5031:"https://suriota.com/system-integration/",5558:"https://suriota.com/surge-saas-platform/"}
for pid,url in pages.items():
    r=subprocess.run(["curl","-s","-u",AUTH,"-X","POST",f"https://suriota.com/wp-json/wp/v2/pages/{pid}",
        "-H","Content-Type: application/json","-d",'{"meta":{"_elementor_edit_mode":"builder"}}',
        "-o","/dev/null","-w","%{http_code}"],capture_output=True,text=True)
    # prime rebuild
    p=subprocess.run(["curl","-s","-L","--max-time","45","-A",GB,url,"-o","/dev/null","-w","%{http_code}"],capture_output=True,text=True)
    print(f"  {pid:5} touch={r.stdout} prime={p.stdout} {url}")
