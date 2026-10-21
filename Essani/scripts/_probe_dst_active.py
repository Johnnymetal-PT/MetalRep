"""List the 7 still-active templates in DST so the user can decide."""
import os, xmlrpc.client
from pathlib import Path
env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line: continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
url = os.environ["DST_URL"].rstrip("/"); db = os.environ["DST_DB"]
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(db, os.environ["DST_LOGIN"], os.environ["DST_API_KEY"], {})
m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
rows = m.execute_kw(db, uid, os.environ["DST_API_KEY"], "product.template", "search_read",
                    [[("active", "=", True)]],
                    {"fields": ["id", "name", "default_code", "categ_id", "type", "is_published",
                                "product_variant_count", "create_date", "write_date"]})
print(f"DST has {len(rows)} active templates:")
for r in rows:
    print(f"  id={r['id']:>5}  code={(r.get('default_code') or '-'):>20}  "
          f"published={r.get('is_published')!s:5}  variants={r.get('product_variant_count')}  "
          f"categ={r['categ_id'][1] if r.get('categ_id') else '-'}  "
          f"type={r.get('type')}  name='{r['name']}'  created={r.get('create_date')}")
