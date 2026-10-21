"""Check the state of src#2139 and src#2015 in Production after specials run."""
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

for sid in (2015, 2139):
    imd = m.execute_kw(db, uid, key, "ir.model.data", "search_read",
                       [[("module", "=", "__promote__"), ("name", "=", f"tmpl_{sid}")]],
                       {"fields": ["res_id"]})
    if not imd:
        print(f"src#{sid} -> NO XID")
        continue
    dst_id = imd[0]["res_id"]
    tmpl = m.execute_kw(db, uid, key, "product.template", "read",
                        [[dst_id], ["name", "attribute_line_ids", "product_variant_ids"]])[0]
    print(f"\nsrc#{sid} -> dst#{dst_id}  name={tmpl['name']!r}")
    print(f"  variants: {len(tmpl['product_variant_ids'])}")
    lines = m.execute_kw(db, uid, key, "product.template.attribute.line", "read",
                         [tmpl["attribute_line_ids"], ["attribute_id", "value_ids"]])
    for line in lines:
        attr_id, attr_name = line["attribute_id"]
        attr = m.execute_kw(db, uid, key, "product.attribute", "read",
                            [[attr_id], ["create_variant"]])[0]
        print(f"    attr {attr_name!r:35} create_variant={attr['create_variant']:8} values={len(line['value_ids'])}")
    # Inspect first variant's PTAVs
    if tmpl["product_variant_ids"]:
        v = m.execute_kw(db, uid, key, "product.product", "read",
                         [[tmpl["product_variant_ids"][0]], ["product_template_attribute_value_ids", "default_code"]])[0]
        if v["product_template_attribute_value_ids"]:
            ptavs = m.execute_kw(db, uid, key, "product.template.attribute.value", "read",
                                 [v["product_template_attribute_value_ids"], ["attribute_id", "product_attribute_value_id"]])
            print(f"  sample variant ptp.var dst#{tmpl['product_variant_ids'][0]} default_code={v.get('default_code') or '-'}")
            for p in ptavs:
                print(f"    PTAV {p['attribute_id'][1]!r} = {p['product_attribute_value_id'][1]!r}")
