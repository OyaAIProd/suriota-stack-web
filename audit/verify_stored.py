import json, re, sys
for pid in sys.argv[1:]:
    d = json.load(open(f'_chk_{pid}.json', encoding='utf-8'))
    ed = d['meta']['_elementor_data']
    # 'Product' as a schema @type token (strip JSON-within-JSON backslashes first)
    flat = ed.replace('\\', '')
    prod = bool(re.search(r'"@type":\s*"Product"', flat))
    brd = 'BreadcrumbList' in ed
    faq = 'FAQPage' in ed
    print(f'page {pid}: len {len(ed)} | Product={prod} | BreadcrumbList={brd} | FAQPage={faq}')
