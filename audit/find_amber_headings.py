import json, os

BK = "audit/elementor_backup_2026-06-02"
PAGES = {934:"modbus", 929:"waste-water", 1740:"iso-m485", 1741:"thm-30md", 1742:"pm1611-wd", 1765:"spd-t485"}

def walk(el, out):
    if isinstance(el, dict):
        if el.get('widgetType') == 'heading':
            s = el.get('settings', {}) or {}
            col = (s.get('title_color') or '').upper()
            glob = (s.get('__globals__', {}) or {}).get('title_color', '')
            is_amber = col in ('#C8851F', '#C8851E') or 'accent' in (glob or '')
            if is_amber:
                out.append((el.get('id'), col or glob, (s.get('title','') or '')[:30]))
        for v in el.values():
            walk(v, out)
    elif isinstance(el, list):
        for v in el:
            walk(v, out)

all_ids = []
for pid, name in PAGES.items():
    p = f"{BK}/{pid}_{name}_orig.json"
    if not os.path.exists(p):
        print(f"[{pid} {name}] no backup"); continue
    raw = json.load(open(p, encoding='utf-8'))      # this is the _elementor_data STRING
    data = json.loads(raw) if isinstance(raw, str) else raw
    out = []
    walk(data, out)
    print(f"[{pid} {name}] amber headings: {out}")
    all_ids += [i for i, _, _ in out if i]

print("\nALL amber heading element IDs:", sorted(set(all_ids)))
