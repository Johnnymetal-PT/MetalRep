"""Quantify the default_code discrepancy between archived (Ana's pre-archive state)
and active (just promoted from backup) templates in DST.

Reports:
- counts (templates / variants with vs without default_code, active vs archived)
- pairs by template name: archived has ref but active doesn't
"""
import os, xmlrpc.client
from pathlib import Path
from collections import defaultdict

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

print("=== Counts ===")
# Templates
t_active_total = call("product.template", "search_count", [[("active","=",True), ("sale_ok","=",True)]])
t_active_nocode = call("product.template", "search_count",
                       [[("active","=",True), ("sale_ok","=",True), ("default_code","=",False)]])
t_arch_total = call("product.template", "search_count", [[("active","=",False), ("sale_ok","=",True)]])
t_arch_nocode = call("product.template", "search_count",
                     [[("active","=",False), ("sale_ok","=",True), ("default_code","=",False)]])
print(f"  templates active total={t_active_total}  no_code={t_active_nocode}  with_code={t_active_total-t_active_nocode}")
print(f"  templates archived total={t_arch_total}  no_code={t_arch_nocode}  with_code={t_arch_total-t_arch_nocode}")

# Variants
v_active_total = call("product.product", "search_count", [[("active","=",True)]])
v_active_nocode = call("product.product", "search_count",
                       [[("active","=",True), ("default_code","=",False)]])
v_arch_total = call("product.product", "search_count", [[("active","=",False)]])
v_arch_nocode = call("product.product", "search_count",
                     [[("active","=",False), ("default_code","=",False)]])
print(f"  variants active total={v_active_total}  no_code={v_active_nocode}  with_code={v_active_total-v_active_nocode}")
print(f"  variants archived total={v_arch_total}  no_code={v_arch_nocode}  with_code={v_arch_total-v_arch_nocode}")

print("\n=== Template-level: archived has code but no active with same name has code ===")
# Get archived templates with default_code set
arch_tmpls = call("product.template", "search_read",
                  [[("active","=",False), ("sale_ok","=",True),
                    ("default_code","!=",False)]],
                  {"fields": ["id","name","default_code"]})
# Get active templates by name
arch_by_name = defaultdict(list)
for t in arch_tmpls:
    arch_by_name[t["name"]].append(t)

# For each, check active counterpart
active_by_name = {}
matches_active_nocode = 0
matches_active_diff = 0
no_active_match = 0
samples = []
for name, group in arch_by_name.items():
    # We pick the most-recently-created archived for the comparison
    arch = max(group, key=lambda x: x["id"])
    active_match = call("product.template", "search_read",
                        [[("active","=",True), ("name","=",name)]],
                        {"fields": ["id","default_code"], "limit": 1})
    if not active_match:
        no_active_match += 1
        continue
    am = active_match[0]
    if am.get("default_code"):
        if am["default_code"] != arch["default_code"]:
            matches_active_diff += 1
            if len(samples) < 5:
                samples.append(("DIFF", arch, am))
        continue  # active already has a code
    # active has no code, archived has one → recover candidate
    matches_active_nocode += 1
    if len(samples) < 10:
        samples.append(("RECOVER", arch, am))
print(f"  archived templates with default_code: {len(arch_tmpls)} (by-name groups: {len(arch_by_name)})")
print(f"  active counterpart matches:")
print(f"    has no code (recover candidate): {matches_active_nocode}")
print(f"    has different code (manual review): {matches_active_diff}")
print(f"    no active counterpart by name:    {no_active_match}")
for tag, arch, am in samples:
    print(f"  [{tag}] '{arch['name']}' arch#{arch['id']} code={arch['default_code']!r}  "
          f"-> active#{am['id']} code={am.get('default_code')!r}")
