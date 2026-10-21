"""Detect attributes whose names differ only by accents/case in SRC."""
import os, xmlrpc.client, unicodedata
from pathlib import Path
from collections import defaultdict
env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line: continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
url = os.environ["SRC_URL"].rstrip("/"); db = os.environ["SRC_DB"]; key = os.environ["SRC_API_KEY"]
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(db, os.environ["SRC_LOGIN"], key, {})
m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
def call(model, method, args, kwargs=None):
    return m.execute_kw(db, uid, key, model, method, args, kwargs or {})

def norm(s):
    if not s: return ""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower().strip()) if unicodedata.category(c) != "Mn")

attrs = call("product.attribute", "search_read", [[]],
             {"fields": ["id", "name", "create_variant", "display_type"]})
buckets = defaultdict(list)
for a in attrs:
    buckets[norm(a["name"])].append(a)
print(f"Total product.attribute in SRC: {len(attrs)}")
print("Duplicates (case/accent-insensitive):")
dupes = {k: v for k, v in buckets.items() if len(v) > 1}
if not dupes:
    print("  (none)")
for k, group in dupes.items():
    print(f"  normalized='{k}':")
    for a in group:
        print(f"    id={a['id']:>4}  name='{a['name']}'  create_variant={a['create_variant']}  display={a['display_type']}")

# Same for values
vals = call("product.attribute.value", "search_read", [[]],
            {"fields": ["id", "name", "attribute_id"]})
val_buckets = defaultdict(list)
for v in vals:
    attr_id = v["attribute_id"][0] if v.get("attribute_id") else 0
    val_buckets[(attr_id, norm(v["name"]))].append(v)
dupe_vals = {k: v for k, v in val_buckets.items() if len(v) > 1}
print(f"\nDuplicate values within same attribute (case/accent-insensitive): {len(dupe_vals)}")
for (attr_id, nm), group in list(dupe_vals.items())[:10]:
    print(f"  attr#{attr_id} normalized='{nm}':")
    for v in group:
        print(f"    id={v['id']:>5}  name='{v['name']}'")
