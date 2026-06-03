import json, subprocess, sys

import os as _os
WP_APP_PASS = next((_l.split("=",1)[1].strip() for _l in open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)),"..",".env"),encoding="utf-8") if _l.startswith("WP_APP_PASS=")), "")
AUTH = "admin:" + WP_APP_PASS
KIT = "https://suriota.com/wp-json/wp/v2/elementor_library/5"

CONTRAST_CSS = """
/* === SURIOTA A11y contrast fixes (kit Custom CSS, non-snippet) 2026-06-02 ===
   Scoped to components that only render on LIGHT backgrounds. Brand amber stays
   bright where it sits on dark sections (global accent var untouched). */
body.elementor-kit-5{--e-global-color-text:#646464}
.sx-hero-eyebrow,.sx-eyebrow{color:#946012 !important}
/* section eyebrows (industries/whyus/faq) — amber text on light; beat base .sx-eyebrow */
.sx-industries-inner span.sx-eyebrow,
.sx-whyus-inner span.sx-eyebrow,
.sx-faq-inner span.sx-eyebrow{color:#946012 !important}
/* page-specific post-XXXX.css uses `html body .sx-industries .sx-eyebrow{var(--sx-accent)!important}`
   (specificity 0,2,2) + `.sx-cta-final .sx-cta-eyebrow{#c8851f!important}`. Beat it with
   `html body.elementor-kit-5 ...` (0,3,2). All four eyebrows sit on white/near-white bg. */
html body.elementor-kit-5 .sx-industries .sx-eyebrow,
html body.elementor-kit-5 .sx-whyus .sx-eyebrow,
html body.elementor-kit-5 .sx-faq .sx-eyebrow,
html body.elementor-kit-5 .sx-cta-final .sx-cta-eyebrow{color:#946012 !important}
/* primary CTA: white text on amber bg -> darken bg+border to pass AA */
.sx-action-btn.sx-action-btn--primary{background:#946012 !important;border-color:#946012 !important}
/* secondary CTA: amber text on white -> darken */
a.sx-action-btn.sx-action-btn--secondary,
a.sx-action-btn.sx-action-btn--secondary span{color:#946012 !important}
.sx-whyus-num{color:#946012 !important}
.sx-related-pillar__num{color:#946012 !important}
.sx-related-pillars__label{color:#5C6B73 !important}
.sx-portfolio-live .sx-pl-yb.y-2025{color:#946012 !important}
.sx-portfolio-live .sx-pl-count,
.sx-portfolio-live .sx-pl-count span{color:#5C6B73 !important}
/* amber section H2 on product pages (accent-colored heading on white) */
.elementor-element-cfb6020 .elementor-heading-title,
.elementor-element-4212c44 .elementor-heading-title{color:#946012 !important}
/* --- CLS fix: JS-injected header (snippet 5153) shifts main#content 0.722.
   Take header out of flow + reserve its 66px height so nothing shifts on inject.
   Keeps current non-sticky scroll behaviour (absolute, not fixed). --- */
header.sx-hf-v5{position:absolute;top:0;left:0;right:0}
body{padding-top:66px}
body.admin-bar header.sx-hf-v5{top:32px}
/* === end A11y contrast === */
""".strip()

# Read LIVE kit (not backup) to avoid clobbering any other current custom_css.
_r = subprocess.run(["curl","-s","-u",AUTH,KIT+"?context=edit"], capture_output=True, text=True)
d = json.loads(_r.stdout)
ps = d['meta']['_elementor_page_settings']
if isinstance(ps, str):
    ps = json.loads(ps)
old = ps.get('custom_css', '') or ''
# strip any prior copy of our block to stay idempotent
marker = '/* === SURIOTA A11y contrast'
if marker in old:
    old = old[:old.index(marker)].rstrip()
ps['custom_css'] = (old + "\n" + CONTRAST_CSS).strip()

if sys.argv[1:] == ['apply']:
    body = json.dumps({"meta": {"_elementor_page_settings": ps}})
    r = subprocess.run(["curl","-s","-X","POST","-u",AUTH,"-H","Content-Type: application/json","--data-binary","@-",KIT],
                       input=body, capture_output=True, text=True)
    try:
        res = json.loads(r.stdout); print("PUT kit id=", res.get('id'), "modified=", res.get('modified'))
    except Exception:
        print("ERR:", r.stdout[:300]); sys.exit(1)
    # verify readback
    r2 = subprocess.run(["curl","-s","-u",AUTH,KIT+"?context=edit"], capture_output=True, text=True)
    ps2 = json.loads(r2.stdout)['meta']['_elementor_page_settings']
    if isinstance(ps2, str): ps2 = json.loads(ps2)
    print("readback custom_css has contrast block:", marker in ps2.get('custom_css',''))
    # flush elementor css
    f = subprocess.run(["curl","-s","-u",AUTH,"-X","DELETE","https://suriota.com/wp-json/elementor/v1/cache","-o","/dev/null","-w","%{http_code}"], capture_output=True, text=True)
    print("elementor flush http=", f.stdout)
else:
    print("DRY — new custom_css:\n", ps['custom_css'])
