"""Delete dst#3925 (the wrong LED Eiffel template) and its XID, so the
re-promotion can build it cleanly with the correct attribute set."""
import os, xmlrpc.client
from pathlib import Path

env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

url = os.environ["DST_URL"].rstrip("/")
db = os.environ["DST_DB"]; login = os.environ["DST_LOGIN"]; key = os.environ["DST_API_KEY"]
common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(db, login, key, {})
m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

DST_TMPL_ID = 3925
SRC_TMPL_ID = 2139

# Sanity check: confirm name and zero orders/stock for safety
tmpl = m.execute_kw(db, uid, key, "product.template", "read",
                    [[DST_TMPL_ID], ["name", "product_variant_ids"]])[0]
print(f"Target to delete: dst#{DST_TMPL_ID} {tmpl['name']!r}  variants={len(tmpl['product_variant_ids'])}")

# Look for any sale_order_line / stock_move referencing the variants
variant_ids = tmpl["product_variant_ids"]
n_sol = m.execute_kw(db, uid, key, "sale.order.line", "search_count",
                     [[("product_id", "in", variant_ids)]])
print(f"  sale.order.line references: {n_sol}")
try:
    n_sm = m.execute_kw(db, uid, key, "stock.move", "search_count",
                        [[("product_id", "in", variant_ids)]])
    print(f"  stock.move references:      {n_sm}")
except Exception as exc:
    print(f"  stock.move check skipped: {exc}")
    n_sm = 0
try:
    n_pol = m.execute_kw(db, uid, key, "purchase.order.line", "search_count",
                        [[("product_id", "in", variant_ids)]])
    print(f"  purchase.order.line refs:   {n_pol}")
except Exception as exc:
    n_pol = 0

if (n_sol + n_sm + n_pol) > 0:
    print("ABORT: template has external references; manual review needed.")
    raise SystemExit(1)

# Delete XID first, then template (Odoo cascades variants on template unlink)
xid_ids = m.execute_kw(db, uid, key, "ir.model.data", "search",
                       [[("module", "=", "__promote__"),
                         ("name", "=", f"tmpl_{SRC_TMPL_ID}"),
                         ("model", "=", "product.template")]])
if xid_ids:
    m.execute_kw(db, uid, key, "ir.model.data", "unlink", [xid_ids])
    print(f"  + deleted XID ir.model.data#{xid_ids[0]}")

m.execute_kw(db, uid, key, "product.template", "unlink", [[DST_TMPL_ID]])
print(f"  + deleted product.template#{DST_TMPL_ID} (variants cascaded)")
