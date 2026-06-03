import json, re, sys

path = sys.argv[1] if len(sys.argv) > 1 else 'audit/elementor_backup_2026-06-02/p934_full.json'
d = json.load(open(path, encoding='utf-8'))
s = d['meta']['_elementor_data']

for m in re.finditer(r'<a class=\\"sx-action-btn.*?</a>', s, re.S):
    block = m.group(0).replace('\\"', '"').replace('\\n', ' ').replace('\\/', '/')
    block = re.sub(r'<svg.*?</svg>', '[svg]', block, flags=re.S)
    block = re.sub(r'\s+', ' ', block)
    print(block)
    # extract visible text (strip tags)
    vis = re.sub(r'<[^>]+>', '', block)
    vis = vis.replace('[svg]', '').replace('→', '').strip()
    aria = re.search(r'aria-label="([^"]+)"', block)
    print("  VISIBLE:", repr(vis), "| ARIA:", aria.group(1) if aria else None)
    print('---')
