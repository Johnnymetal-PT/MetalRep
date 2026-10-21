"""Inspect FOCOS LED category templates names + scope of duplicate categories."""
import os, xmlrpc.client
from pathlib import Path
env = Path('scripts/.promote.env')
for raw in env.read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or '=' not in line: continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip().strip(chr(34)).strip(chr(39)))

def connect(lbl):
    url = os.environ[f'{lbl}_URL'].rstrip('/'); db = os.environ[f'{lbl}_DB']
    key = os.environ[f'{lbl}_API_KEY']
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, os.environ[f'{lbl}_LOGIN'], key, {})
    m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    def call(model, method, args, kwargs=None):
        return m.execute_kw(db, uid, key, model, method, args, kwargs or {})
    return call

src = connect('SRC'); dst = connect('DST')

print("="*70)
print("FOCOS LED — templates in this category in SRC")
print("="*70)
# Find FOCOS LED in SRC
src_cat = src("product.public.category", "search",
              [[("name", "=", "FOCOS LED")]], {})
if src_cat:
    for cat_id in src_cat:
        cat = src("product.public.category", "read",
                  [[cat_id]], {"fields": ["name","parent_id","display_name"]})[0]
        print(f"\n  SRC category id={cat_id}: {cat.get('display_name')}")
        tmpls = src("product.template", "search_read",
                    [[("public_categ_ids", "in", [cat_id]), ("active", "=", True)]],
                    {"fields": ["id","name","default_code","is_published"]})
        print(f"  Total templates: {len(tmpls)}")
        for t in sorted(tmpls, key=lambda x: x.get('name') or ''):
            # Match by name in DST
            dst_match = dst("product.template", "search_read",
                            [[("name", "=", t["name"]), ("active", "=", True)]],
                            {"fields": ["id","name"]})
            dst_str = f"dst#{dst_match[0]['id']}" if dst_match else "MISSING"
            print(f"    src#{t['id']:>5} pub={t.get('is_published')!s:5} '{t['name']}' -> {dst_str}")

print("\n" + "="*70)
print("Scope of duplicate categories (created during promote)")
print("="*70)
# Categories with create_date around the promote window
# Find DST categories created today
import datetime
today = datetime.date.today().isoformat()
dst_cats = dst("product.public.category", "search_read",
               [[("create_date", ">=", f"{today} 17:00:00")]],
               {"fields": ["id","name","parent_id","display_name","create_date"]})
print(f"DST categories created today (after promote start 17:00): {len(dst_cats)}")
for c in dst_cats:
    parent = c['parent_id'][1] if c.get('parent_id') else '(root)'
    # Find sibling categories with same name in DST
    others = dst("product.public.category", "search_count",
                 [[("name", "=", c["name"]), ("id", "!=", c["id"])]])
    flag = f" [+{others} other(s) same name]" if others else ""
    print(f"  id={c['id']:>4} '{c['name']}' parent='{parent}'  created={c['create_date']}{flag}")

print("\n" + "="*70)
print("Templates referencing duplicate categories (created today)")
print("="*70)
if dst_cats:
    new_cat_ids = [c["id"] for c in dst_cats]
    tmpl_count = dst("product.template", "search_count",
                     [[("public_categ_ids", "in", new_cat_ids), ("active", "=", True)]])
    print(f"Active templates referencing any of the {len(new_cat_ids)} new categories: {tmpl_count}")
