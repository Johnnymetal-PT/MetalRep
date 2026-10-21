"""Diagnose: archived templates without active counterpart + verify one specific case."""
import os, xmlrpc.client
from pathlib import Path

env = Path('scripts/.promote.env')
for raw in env.read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or '=' not in line: continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

url = os.environ['DST_URL'].rstrip('/'); db = os.environ['DST_DB']; key = os.environ['DST_API_KEY']
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
uid = common.authenticate(db, os.environ['DST_LOGIN'], key, {})
m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
def call(model, method, args, kwargs=None):
    return m.execute_kw(db, uid, key, model, method, args, kwargs or {})

# 1) Archived templates with no active counterpart
arch = call("product.template", "search_read",
            [[("active","=",False), ("sale_ok","=",True)]],
            {"fields": ["id","name","default_code","product_variant_count"]})
active_names = set()
for t in call("product.template", "search_read",
              [[("active","=",True), ("sale_ok","=",True)]],
              {"fields": ["name"]}):
    active_names.add(t["name"])
unmatched = [t for t in arch if t["name"] not in active_names]
print(f"Archived templates with no active counterpart by name: {len(unmatched)}")
for t in unmatched:
    print(f"  arch#{t['id']:>5} variants={t.get('product_variant_count'):>4} "
          f"code={t.get('default_code')!r}  name='{t['name']}'")

# 2) Variant code coverage in archived without active counterpart
unmatched_ids = [t["id"] for t in unmatched]
if unmatched_ids:
    vs = call("product.product", "search_count",
              [[("product_tmpl_id", "in", unmatched_ids), ("default_code", "!=", False)]])
    vs_total = call("product.product", "search_count",
                    [[("product_tmpl_id", "in", unmatched_ids)]])
    print(f"\nVariants in those unmatched archived templates: total={vs_total} with_code={vs}")

# 3) Spot check: pick one matched pair and inspect variant data
print("\n--- Spot check: variant default_code in one matched pair ---")
# Pick template 1925 'Conector NT Pro M1' from earlier samples
arch_pick = call("product.template", "search_read",
                 [[("active","=",False), ("name","=","Conector NT Pro M1")]],
                 {"fields": ["id","name","product_variant_ids"]})
act_pick = call("product.template", "search_read",
                [[("active","=",True), ("name","=","Conector NT Pro M1")]],
                {"fields": ["id","name","product_variant_ids"]})
if arch_pick and act_pick:
    a = arch_pick[0]; v = act_pick[0]
    print(f"  archived: tmpl#{a['id']} variants={len(a['product_variant_ids'])}")
    print(f"  active:   tmpl#{v['id']} variants={len(v['product_variant_ids'])}")
    avs = call("product.product", "read",
               [a["product_variant_ids"],
                ["id","default_code","active","product_template_attribute_value_ids"]])
    print(f"  archived variants read returned: {len(avs)}  active={sum(1 for x in avs if x.get('active'))}")
    for av in avs[:5]:
        print(f"    arch_v#{av['id']} active={av.get('active')} code={av.get('default_code')!r}")
    vvs = call("product.product", "read",
               [v["product_variant_ids"],
                ["id","default_code","active","product_template_attribute_value_ids"]])
    print(f"  active variants read returned: {len(vvs)}")
    for vv in vvs[:5]:
        print(f"    act_v#{vv['id']} code={vv.get('default_code')!r}")
