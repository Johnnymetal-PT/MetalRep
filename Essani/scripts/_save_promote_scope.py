"""Save the 574 non-service template IDs and report attachment volume."""
import os, xmlrpc.client
from pathlib import Path
env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line: continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
url = os.environ["SRC_URL"].rstrip("/"); db = os.environ["SRC_DB"]
key = os.environ["SRC_API_KEY"]
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(db, os.environ["SRC_LOGIN"], key, {})
m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
def call(model, method, args, kwargs=None):
    return m.execute_kw(db, uid, key, model, method, args, kwargs or {})

ids = call("product.template", "search",
           [[("active", "=", True), ("type", "!=", "service")]])
print(f"non-service active templates: {len(ids)}")
out = Path(__file__).with_name("_to_promote_ids.txt")
out.write_text(",".join(str(i) for i in ids), encoding="utf-8")
print(f"saved to {out.name}")

variants = call("product.product", "search_count",
                [[("product_tmpl_id", "in", ids), ("active", "=", True)]])
print(f"\nactive variants across these templates: {variants}")

tmpl_imgs = call("product.image", "search_count",
                 [[("product_tmpl_id", "in", ids), ("product_variant_id", "=", False)]])
var_imgs = call("product.image", "search_count",
                [[("product_tmpl_id", "in", ids), ("product_variant_id", "!=", False)]])
print(f"product.image template-level: {tmpl_imgs}")
print(f"product.image variant-level: {var_imgs}")

variant_ids = call("product.product", "search",
                   [[("product_tmpl_id", "in", ids), ("active", "=", True)]])
tmpl_docs = call("product.document", "search_count",
                 [[("res_model", "=", "product.template"), ("res_id", "in", ids)]])
var_docs = call("product.document", "search_count",
                [[("res_model", "=", "product.product"), ("res_id", "in", variant_ids)]])
print(f"product.document on templates: {tmpl_docs}")
print(f"product.document on variants: {var_docs}")

print("\nDocument size buckets:")
docs = call("product.document", "search_read",
            ["|",
             "&", ("res_model", "=", "product.template"), ("res_id", "in", ids),
             "&", ("res_model", "=", "product.product"), ("res_id", "in", variant_ids)],
            ) if False else call("product.document", "search_read",
            [[
              "|",
              "&", ("res_model", "=", "product.template"), ("res_id", "in", ids),
              "&", ("res_model", "=", "product.product"), ("res_id", "in", variant_ids),
            ]], {"fields": ["file_size", "mimetype"]})
buckets = {"<100KB": 0, "100KB-1MB": 0, "1-10MB": 0, "10-50MB": 0, "50-95MB": 0, ">95MB": 0}
total_bytes = 0
for d in docs:
    sz = d.get("file_size") or 0
    total_bytes += sz
    if sz < 100*1024: buckets["<100KB"] += 1
    elif sz < 1024*1024: buckets["100KB-1MB"] += 1
    elif sz < 10*1024*1024: buckets["1-10MB"] += 1
    elif sz < 50*1024*1024: buckets["10-50MB"] += 1
    elif sz <= 95*1024*1024: buckets["50-95MB"] += 1
    else: buckets[">95MB"] += 1
for k, v in buckets.items():
    print(f"  {k:>10}: {v}")
print(f"  Total documents bytes: {total_bytes/1024/1024:.1f} MB")
