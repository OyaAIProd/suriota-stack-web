import json, re

d = json.load(open('audit/elementor_backup_2026-06-02/p12_home_orig.json', encoding='utf-8'))
s = d['meta']['_elementor_data']
txt = s.replace('\\"', '"').replace('\\/', '/').replace('\\n', ' ')

for m in re.finditer(r'<a\b[^>]*aria-label="([^"]+)"[^>]*>(.*?)</a>', txt, re.S):
    aria = m.group(1)
    inner = re.sub(r'<[^>]+>', '', m.group(2)).strip()[:45]
    ok = inner and inner in aria
    print(("OK  " if ok else "MISMATCH"), "vis=" + repr(inner), "| aria=" + repr(aria))

print("--- attr-style aria-labels ---")
for m in re.finditer(r'"aria[-_]label":"([^"]+)"', txt):
    print("aria:", m.group(1)[:50])
