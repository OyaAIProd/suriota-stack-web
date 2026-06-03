import json
d=json.load(open('audit/elementor_backup_2026-06-02/footer_1079_orig.json',encoding='utf-8'))
s=d['meta']['_elementor_data']
print("data len:", len(s))
# count header_size occurrences (Elementor heading widget tag)
import re
for m in re.finditer(r'"header_size":"(h[1-6])"', s):
    print("header_size:", m.group(1))
# also titles near
for m in re.finditer(r'"title":"([^"]{0,40})","header_size":"(h[1-6])"', s):
    print("  ", m.group(2), "=>", m.group(1))
