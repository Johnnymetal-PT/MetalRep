"""Build the final set of Staging product.template IDs to promote.

Excludes:
  1. Default-Odoo products (those with `ir.model.data.module` outside
     {'__export__','__promote__'}).
  2. Products already in Production whose names match the 89 entries in
     `ids in main.xlsx` -- matched name-by-name on the Staging side.
  3. Products already promoted via this script (XID `__promote__.tmpl_*`).
Read-only.
"""
import os, json, xmlrpc.client
from collections import Counter
from pathlib import Path
import openpyxl

env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def connect(label):
    url = os.environ[f"{label}_URL"].rstrip("/")
    db = os.environ[f"{label}_DB"]
    login = os.environ[f"{label}_LOGIN"]; key = os.environ[f"{label}_API_KEY"]
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(db, login, key, {})
    m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    return db, uid, key, m

src_db, src_uid, src_key, src_m = connect("SRC")
dst_db, dst_uid, dst_key, dst_m = connect("DST")
db, uid, key, models = src_db, src_uid, src_key, src_m  # keep below code using src vars

# All active templates (search with a non-empty domain to dodge the ir.rule that
# blocks `search([])` on this server)
active_rows = src_m.execute_kw(src_db, src_uid, src_key, "product.template", "search_read",
                               [[("active", "=", True)]], {"fields": ["id", "name", "default_code"]})
active_ids = {r["id"] for r in active_rows}
name_to_src_ids = {}
code_to_src_ids = {}
for r in active_rows:
    name_to_src_ids.setdefault((r["name"] or "").strip(), []).append(r["id"])
    if r.get("default_code"):
        code_to_src_ids.setdefault(r["default_code"].strip(), []).append(r["id"])

# Templates with XID from any module
xids = models.execute_kw(db, uid, key, "ir.model.data", "search_read",
                         [[("model", "=", "product.template")]],
                         {"fields": ["res_id", "module", "name"]})
module_counts = Counter(x["module"] for x in xids)
print("ir.model.data on product.template — modules in Staging:")
for mod, n in sorted(module_counts.items(), key=lambda kv: -kv[1]):
    print(f"  {mod:30} {n}")

user_modules = {"__export__", "__promote__"}
default_odoo_ids = {x["res_id"] for x in xids if x["module"] not in user_modules}

# Already promoted: XIDs live on the DESTINATION side, with name like `tmpl_<src_id>`
promoted_xids = dst_m.execute_kw(dst_db, dst_uid, dst_key, "ir.model.data", "search_read",
                                  [[("module", "=", "__promote__"),
                                    ("model", "=", "product.template")]],
                                  {"fields": ["name", "res_id"]})
promoted_ids = set()
for x in promoted_xids:
    if x["name"].startswith("tmpl_"):
        try:
            promoted_ids.add(int(x["name"][5:]))
        except ValueError:
            pass

# Read the Excel list of 'already in main' — only IDs (names are encoding-corrupt)
wb = openpyxl.load_workbook("ids in main.xlsx", read_only=True, data_only=True)
ws = wb["Sheet1"]
main_ids = []
for i, row in enumerate(ws.iter_rows(values_only=True)):
    if i == 0 or not row or row[0] is None:
        continue
    try:
        main_ids.append(int(row[0]))
    except (TypeError, ValueError):
        pass
print(f"\n'ids in main.xlsx': {len(main_ids)} IDs")

# Read those Production templates DIRECTLY (correct encoding) to get name+default_code
main_rows = dst_m.execute_kw(dst_db, dst_uid, dst_key, "product.template", "read",
                              [main_ids, ["id", "name", "default_code"]])
main_by_id = {r["id"]: r for r in main_rows}
missing_in_main = [i for i in main_ids if i not in main_by_id]
if missing_in_main:
    print(f"  ! {len(missing_in_main)} of the Excel IDs no longer exist in Production: {missing_in_main[:10]}")

# Map Production templates -> Staging templates by (1) default_code, (2) name
already_in_main_src_ids = set()
matched_by_code = matched_by_name = 0
unmatched = []
for r in main_rows:
    code = (r.get("default_code") or "").strip()
    name = (r.get("name") or "").strip()
    found = None
    if code and code in code_to_src_ids:
        found = code_to_src_ids[code]
        matched_by_code += 1
    elif name and name in name_to_src_ids:
        found = name_to_src_ids[name]
        matched_by_name += 1
    if found:
        already_in_main_src_ids.update(found)
    else:
        unmatched.append(r)

print(f"Production -> Staging match: by code={matched_by_code} by name={matched_by_name} unmatched={len(unmatched)}")
if unmatched:
    print(f"  unmatched in Staging (manual check needed):")
    for r in unmatched[:25]:
        print(f"    main#{r['id']:5} code={r.get('default_code') or '-':25} name={r['name']!r}")
    if len(unmatched) > 25:
        print(f"    ... +{len(unmatched) - 25} more")

# Final candidate set
candidates = active_ids - default_odoo_ids - already_in_main_src_ids - promoted_ids

print(f"\nStaging counts:")
print(f"  active templates                  {len(active_ids):>5}")
print(f"  - default Odoo (XID in module)    {len(default_odoo_ids):>5}")
print(f"  - already in main (Excel match)   {len(already_in_main_src_ids):>5}")
print(f"  - already promoted (XID)          {len(promoted_ids):>5}")
print(f"  = candidates to promote           {len(candidates):>5}")

# Save the list of IDs for the run
ids_out = Path(__file__).with_name("_to_promote_ids.txt")
ids_out.write_text(",".join(str(i) for i in sorted(candidates)), encoding="utf-8")
print(f"\nIDs written to {ids_out.name}")

# Sample preview
sample_ids = sorted(candidates)[:8]
if sample_ids:
    sample = models.execute_kw(db, uid, key, "product.template", "read",
                               [sample_ids, ["id", "name", "default_code"]])
    print(f"\nSample of candidates:")
    for s in sample:
        print(f"  src#{s['id']:5} {(s['name'] or '')[:60]:60}  default_code={s.get('default_code') or '-'}")

# Also save unmatched-names for a manual review
if unmatched:
    unmatched_out = Path(__file__).with_name("_unmatched_main_names.txt")
    unmatched_out.write_text(
        "\n".join(f"main#{r['id']}\t{(r.get('default_code') or '').strip()}\t{r['name']}" for r in unmatched),
        encoding="utf-8",
    )
    print(f"Unmatched Production templates dumped to {unmatched_out.name}")
