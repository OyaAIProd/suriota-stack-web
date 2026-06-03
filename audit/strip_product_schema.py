#!/usr/bin/env python3
"""Strip @type:Product node from Elementor HTML-widget JSON-LD @graph on 16 product pages.
Dry-run by default; pass --write to POST changes back via WP REST (App Password in WP_APP_PASS).
Preserves BreadcrumbList and all other @graph nodes + every other widget/content.
"""
import json, re, os, sys, subprocess

BK = r'C:/Users/Administrator/Music/Website Suriota/audit/elementor_backup_2026-06-02'
IDS = [929,934,1740,1741,1742,1765,5287,5291,5292,5293,5294,5295,5455,5456,5462,5464]
SCRIPT_RE = re.compile(r'(<script[^>]*application/ld\+json[^>]*>)(.*?)(</script>)', re.S | re.I)

def strip_product_from_html(html):
    """Return (new_html, removed_count, note). Removes Product from @graph; drops script if it becomes Product-only."""
    removed = 0
    notes = []
    def repl(m):
        nonlocal removed
        head, body, tail = m.group(1), m.group(2), m.group(3)
        try:
            ld = json.loads(body)
        except Exception as e:
            notes.append(f'unparseable ld+json: {e}')
            return m.group(0)  # leave untouched
        def is_product(t):
            tl = t if isinstance(t, list) else [t]
            return 'Product' in tl
        if isinstance(ld, dict) and '@graph' in ld and isinstance(ld['@graph'], list):
            before = len(ld['@graph'])
            kept = [n for n in ld['@graph'] if not (isinstance(n, dict) and is_product(n.get('@type')))]
            removed += before - len(kept)
            if not kept:
                notes.append('graph emptied -> drop whole script')
                return ''  # nothing left worth keeping
            ld['@graph'] = kept
            new_body = json.dumps(ld, ensure_ascii=False, indent=2)
            return head + new_body + tail
        if isinstance(ld, dict) and is_product(ld.get('@type')):
            removed += 1
            notes.append('top-level Product -> drop whole script')
            return ''
        return m.group(0)
    new_html = SCRIPT_RE.sub(repl, html)
    return new_html, removed, '; '.join(notes)

def walk(node, cb):
    if isinstance(node, dict):
        cb(node)
        for v in node.values():
            walk(v, cb)
    elif isinstance(node, list):
        for v in node:
            walk(v, cb)

def process(ed_str):
    obj = json.loads(ed_str)
    total_removed = 0
    notes_all = []
    def cb(d):
        nonlocal total_removed
        s = d.get('settings')
        if isinstance(s, dict) and isinstance(s.get('html'), str) and 'application/ld+json' in s['html']:
            new_html, removed, note = strip_product_from_html(s['html'])
            if removed:
                s['html'] = new_html
                total_removed += removed
                if note: notes_all.append(note)
    walk(obj, cb)
    new_ed = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    return new_ed, total_removed, '; '.join(notes_all)

def main():
    write = '--write' in sys.argv
    pw = os.environ.get('WP_APP_PASS', '')
    for pid in IDS:
        f = f'{BK}/page_{pid}.json'
        d = json.load(open(f, encoding='utf-8'))
        ed = d['meta']['_elementor_data']
        new_ed, removed, note = process(ed)
        # sanity: ensure no Product type remains
        still = 'Product' in new_ed and re.search(r'"@type"\s*:\s*"Product"', new_ed.replace('\\', ''))
        status = 'WROTE' if write else 'DRY'
        print(f'page {pid}: removed={removed} len {len(ed)}->{len(new_ed)} residual_product={bool(still)} note=[{note}]')
        if write and removed:
            body = json.dumps({'meta': {'_elementor_data': new_ed}})
            bf = f'{BK}/_post_{pid}.json'
            open(bf, 'w', encoding='utf-8').write(body)
            r = subprocess.run([
                'curl','-s','-u',f'admin:{pw}','-X','POST',
                '-H','Content-Type: application/json',
                '--data-binary', f'@{bf}',
                f'https://suriota.com/wp-json/wp/v2/pages/{pid}',
                '-w','\nHTTP %{http_code}'
            ], capture_output=True, text=True)
            tail = r.stdout[-120:]
            print(f'    POST -> {tail}')
            os.remove(bf)

if __name__ == '__main__':
    main()
