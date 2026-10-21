"""Inspect doc sizes for src#2103 to identify oversize documents."""
import os, base64, xmlrpc.client
from pathlib import Path

env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

url = os.environ["SRC_URL"].rstrip("/")
db = os.environ["SRC_DB"]; login = os.environ["SRC_LOGIN"]; key = os.environ["SRC_API_KEY"]
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(db, login, key, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

# Find variants of src#2103
tmpl = models.execute_kw(db, uid, key, "product.template", "read",
                         [[2103], ["product_variant_ids"]])[0]
variant_ids = tmpl["product_variant_ids"]

domain = ["|",
          "&", ("res_model", "=", "product.template"), ("res_id", "=", 2103),
          "&", ("res_model", "=", "product.product"),  ("res_id", "in", variant_ids or [0])]
doc_ids = models.execute_kw(db, uid, key, "product.document", "search", [domain])
print(f"src#2103 has {len(doc_ids)} documents")
# Read only metadata + file_size if present; avoid pulling binaries
fields = models.execute_kw(db, uid, key, "product.document", "fields_get", [], {"attributes":["type"]})
size_field = "file_size" if "file_size" in fields else None
read_fields = ["name", "mimetype", "res_model", "res_id"] + ([size_field] if size_field else [])
docs = models.execute_kw(db, uid, key, "product.document", "read", [doc_ids, read_fields])
docs.sort(key=lambda d: -(d.get(size_field) or 0) if size_field else 0)
total = 0
for d in docs:
    sz = d.get(size_field, "?") if size_field else "?"
    if isinstance(sz, int): total += sz
    print(f"  [{sz!s:>10}]  {d['name']:55} {d['mimetype']:25} {d['res_model']}#{d['res_id']}")
if size_field:
    print(f"  TOTAL bytes: {total:,}  ({total/1024/1024:.2f} MB)")
