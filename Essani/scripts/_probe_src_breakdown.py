"""Breakdown of SRC active templates by type / category / publication state."""
import os, xmlrpc.client
from pathlib import Path
from collections import Counter
env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line: continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
url = os.environ["SRC_URL"].rstrip("/"); db = os.environ["SRC_DB"]
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(db, os.environ["SRC_LOGIN"], os.environ["SRC_API_KEY"], {})
m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

rows = m.execute_kw(db, uid, os.environ["SRC_API_KEY"], "product.template", "search_read",
                    [[("active", "=", True)]],
                    {"fields": ["id", "name", "default_code", "type", "categ_id",
                                "is_published", "sale_ok"]})
print(f"SRC active templates: {len(rows)}\n")

# By type
print("By type:")
for k, v in Counter(r.get("type") for r in rows).items():
    print(f"  {k}: {v}")

# Services likely include system defaults
services = [r for r in rows if r.get("type") == "service"]
print(f"\nService-typed templates ({len(services)}):")
for r in services[:20]:
    print(f"  id={r['id']:>5}  code={(r.get('default_code') or '-'):>18}  "
          f"published={r.get('is_published')!s:5}  sale_ok={r.get('sale_ok')!s:5}  "
          f"categ={r['categ_id'][1] if r.get('categ_id') else '-'}  name='{r['name']}'")
if len(services) > 20:
    print(f"  ... and {len(services)-20} more")

# Counts non-services
non_services = [r for r in rows if r.get("type") != "service"]
print(f"\nNon-service templates: {len(non_services)}")
published_non_svc = [r for r in non_services if r.get("is_published")]
print(f"  ... of which is_published=True: {len(published_non_svc)}")
sale_ok_non_svc = [r for r in non_services if r.get("sale_ok")]
print(f"  ... of which sale_ok=True: {len(sale_ok_non_svc)}")

# Top categories
print("\nTop categories (active templates):")
for k, v in Counter(r["categ_id"][1] if r.get("categ_id") else "-" for r in rows).most_common(15):
    print(f"  {v:>4}  {k}")
