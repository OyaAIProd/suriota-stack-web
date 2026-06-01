"""Fix JobPosting structured-data warnings on /internship/ (page 1127, Elementor).
- educationRequirements.credentialCategory invalid enum -> array of 2 valid EOC
  (associate degree = D3, bachelor degree = D4/S1); detail moved to qualifications.
- baseSalary missing -> add MonetaryAmount IDR 500k-5jt / MONTH.

Robust: json.loads the _elementor_data tree, locate the HTML widget holding the
JSON-LD, parse+modify the JobPosting dict, re-serialize, write back. Backups +
validation + dry-run default (--execute to write).
"""
import os, re, sys, json, pathlib
import requests
from requests.auth import HTTPBasicAuth

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENV = {}
for line in (ROOT / ".env").read_text().splitlines():
    if "=" in line and not line.strip().startswith("#"):
        k, v = line.split("=", 1); ENV[k.strip()] = v.strip()
AUTH = HTTPBasicAuth("admin", ENV["WP_APP_PASS"])
PAGE = "https://suriota.com/wp-json/wp/v2/pages/1127"
BK = ROOT / "backups" / "2026-06-01" / "internship-schema"; BK.mkdir(parents=True, exist_ok=True)
EXECUTE = "--execute" in sys.argv

r = requests.get(PAGE, auth=AUTH, params={"context": "edit", "_fields": "meta"}, timeout=90)
r.raise_for_status()
ed_str = r.json()["meta"]["_elementor_data"]
(BK / "elementor_data-before.json").write_text(ed_str, encoding="utf-8")
tree = json.loads(ed_str)

# locate the HTML widget settings whose 'html' contains the JobPosting JSON-LD
hits = []
def walk(node):
    if isinstance(node, dict):
        s = node.get("settings")
        if isinstance(s, dict):
            for key in ("html", "editor", "text"):
                v = s.get(key)
                if isinstance(v, str) and "JobPosting" in v:
                    hits.append((s, key))
        for v in node.values(): walk(v)
    elif isinstance(node, list):
        for v in node: walk(v)
walk(tree)
assert len(hits) == 1, f"expected 1 JobPosting widget, found {len(hits)}"
settings, key = hits[0]
html = settings[key]

m = re.search(r'(<script[^>]*application/ld\+json[^>]*>)(.*?)(</script>)', html, re.S)
assert m, "JSON-LD script not found in widget"
jp = json.loads(m.group(2))
assert jp.get("@type") == "JobPosting", jp.get("@type")

# --- modifications ---
jp["educationRequirements"] = [
    {"@type": "EducationalOccupationalCredential", "credentialCategory": "associate degree"},
    {"@type": "EducationalOccupationalCredential", "credentialCategory": "bachelor degree"},
]
jp["baseSalary"] = {
    "@type": "MonetaryAmount", "currency": "IDR",
    "value": {"@type": "QuantitativeValue", "minValue": 500000, "maxValue": 5000000, "unitText": "MONTH"},
}
jp["qualifications"] = ("Active D3/D4/S1 student (minimum 5th semester), minimum GPA 3.00, "
                        "Electrical Engineering or Informatics major preferred, "
                        "willing to work on-site in Batam 3 days/week")

new_jsonld = json.dumps(jp, indent=2, ensure_ascii=False)
new_html = html[:m.start(2)] + new_jsonld + html[m.end(2):]
settings[key] = new_html
new_ed = json.dumps(tree, ensure_ascii=False, separators=(",", ":"))

# --- validate before write ---
assert "JobPosting" in new_ed and "bachelor degree" in new_ed and "baseSalary" in new_ed
# old invalid enum must be gone from the JSON-LD (visible page copy may still carry it — that's fine)
assert "Active student, minimum 5th semester" not in new_jsonld
assert "credentialCategory" in new_jsonld and new_jsonld.count("EducationalOccupationalCredential") == 2
json.loads(new_ed)            # whole tree still valid JSON
json.loads(json.dumps(jp))    # jp valid
(BK / "elementor_data-after.json").write_text(new_ed, encoding="utf-8")

print(f"widget key={key}  old_ed_len={len(ed_str)}  new_ed_len={len(new_ed)}")
print("--- new JobPosting JSON-LD ---")
print(new_jsonld)

if not EXECUTE:
    print("\nDRY RUN — validated, not written. Re-run with --execute.")
    sys.exit(0)

resp = requests.post(PAGE, auth=AUTH, json={"meta": {"_elementor_data": new_ed}}, timeout=90)
print(f"\nPOST status={resp.status_code}")
if resp.status_code in (200, 201):
    # verify persisted
    chk = requests.get(PAGE, auth=AUTH, params={"context": "edit", "_fields": "meta"}, timeout=90).json()
    cur = chk["meta"]["_elementor_data"]
    print("persisted bachelor degree:", "bachelor degree" in cur, "| baseSalary:", "baseSalary" in cur,
          "| old value gone:", "Active student, minimum 5th semester" not in cur)
else:
    print("ERR:", resp.text[:300])
