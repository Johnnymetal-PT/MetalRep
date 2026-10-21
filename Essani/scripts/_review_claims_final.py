"""Final review: each original claim cross-checked with current DST state."""
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


def title(s):
    print("\n" + "="*78 + f"\n  {s}\n" + "="*78)


def categ_products(call, name):
    """Find category in DB by name (any case/accent) and report product count + sample."""
    cats = call("product.public.category", "search_read",
                [[("name", "ilike", name)]], {"fields": ["id","name","display_name","image_1920"]})
    for c in cats:
        c["has_image"] = bool(c.pop("image_1920", None))
        c["tmpl_ids"] = call("product.template", "search",
                             [[("public_categ_ids", "in", [c["id"]])]], {})
    return cats


title("CLAIM 1: Cabos de Alimentação — sem produtos no website + variantes sem refs")
for lbl, call in (("SRC", src), ("DST", dst)):
    cats = categ_products(call, "Cabos de Alimentação")
    for c in cats:
        print(f"  [{lbl}] categ#{c['id']} has_image={c['has_image']} "
              f"products={len(c['tmpl_ids'])}  display='{c['display_name']}'")
# Variant default_code coverage on these products (DST)
dst_cats = categ_products(dst, "Cabos de Alimentação")
if dst_cats:
    canonical = max(dst_cats, key=lambda c: len(c["tmpl_ids"]))
    print(f"\n  Variant default_code coverage on canonical categ#{canonical['id']}:")
    tmpls = canonical["tmpl_ids"][:5]
    for tid in tmpls:
        t = dst("product.template", "read", [[tid]], {"fields": ["name", "product_variant_ids"]})[0]
        vs = dst("product.product", "read", [t["product_variant_ids"]],
                 {"fields": ["id","default_code","active","hide_on_website"]})
        codes = [v.get("default_code") for v in vs]
        nones = sum(1 for c in codes if not c)
        hidden = sum(1 for v in vs if v.get("hide_on_website"))
        print(f"    '{t['name']}' variants={len(vs)} no_default_code={nones} hidden={hidden}  "
              f"sample_codes={codes[:3]}")

title("CLAIM 2: Acessórios de distribuição — sem produtos no website + variantes sem refs")
# This name didn't match anything earlier; try variants
for search in ("Acessórios de distribuição", "Distribuição"):
    print(f"\n  Searching '{search}':")
    for lbl, call in (("SRC", src), ("DST", dst)):
        cats = categ_products(call, search)
        for c in cats:
            print(f"    [{lbl}] categ#{c['id']} has_image={c['has_image']} "
                  f"products={len(c['tmpl_ids'])}  display='{c['display_name']}'")

# Variant codes on Distribuição
dst_cats = categ_products(dst, "Distribuição")
if dst_cats:
    canonical = max(dst_cats, key=lambda c: len(c["tmpl_ids"]))
    print(f"\n  Variant default_code coverage on canonical categ#{canonical['id']}:")
    for tid in canonical["tmpl_ids"][:5]:
        t = dst("product.template", "read", [[tid]], {"fields": ["name", "product_variant_ids"]})[0]
        vs = dst("product.product", "read", [t["product_variant_ids"]],
                 {"fields": ["id","default_code","hide_on_website"]})
        codes = [v.get("default_code") for v in vs]
        nones = sum(1 for c in codes if not c)
        hidden = sum(1 for v in vs if v.get("hide_on_website"))
        print(f"    '{t['name']}' variants={len(vs)} no_default_code={nones} hidden={hidden}")


title("CLAIM 3: Acessórios LED-DISTRIBUIÇÃO — produtos visíveis que estavam ocultos")
# Look for templates in that category and compare hide_on_website count
for lbl, call in (("SRC", src), ("DST", dst)):
    cats = categ_products(call, "Acessórios LED-DISTRIBUIÇÃO")
    for c in cats:
        n_hidden = call("product.product", "search_count",
                        [[("product_tmpl_id", "in", c["tmpl_ids"]),
                          ("hide_on_website", "=", True)]])
        n_visible = call("product.product", "search_count",
                         [[("product_tmpl_id", "in", c["tmpl_ids"]),
                           ("hide_on_website", "=", False),
                           ("active", "=", True)]])
        print(f"  [{lbl}] categ#{c['id']} products={len(c['tmpl_ids'])}  "
              f"variants_hidden={n_hidden}  variants_visible={n_visible}  display='{c['display_name']}'")


title("CLAIM 4: Focos LED — produtos duplicados por voltagem com nome original")
# Show all SRC products in any FOCOS LED category, and their dst names
for lbl, call in (("SRC", src), ("DST", dst)):
    cats = categ_products(call, "FOCOS LED")
    for c in cats:
        if not c["tmpl_ids"]: continue
        ts = call("product.template", "read", [c["tmpl_ids"]],
                  {"fields": ["id","name","is_published"]})
        print(f"\n  [{lbl}] categ#{c['id']} '{c['display_name']}' — {len(ts)} produtos:")
        for t in sorted(ts, key=lambda x: x.get('name') or ''):
            print(f"    id={t['id']:>5} pub={t.get('is_published')!s:5} '{t['name']}'")


title("CLAIM 5: Sistemas Elevatórios — produtos visíveis que estavam ocultos")
for lbl, call in (("SRC", src), ("DST", dst)):
    cats = categ_products(call, "Sistemas Elevatórios")
    for c in cats:
        if not c["tmpl_ids"]: continue
        n_hidden = call("product.product", "search_count",
                        [[("product_tmpl_id", "in", c["tmpl_ids"]),
                          ("hide_on_website", "=", True)]])
        n_visible = call("product.product", "search_count",
                         [[("product_tmpl_id", "in", c["tmpl_ids"]),
                           ("hide_on_website", "=", False),
                           ("active", "=", True)]])
        print(f"  [{lbl}] categ#{c['id']} products={len(c['tmpl_ids'])}  "
              f"variants_hidden={n_hidden}  variants_visible={n_visible}  display='{c['display_name']}'")


title("CLAIMS 6-9: Templates 'iniciais' com variantes explosivas (data faithful to Test)")
for name in ("LED Eiffel", "LED EFLEX CX120", "LED Aureola", "LED Glassline"):
    print(f"\n  Templates LIKE '{name}':")
    for lbl, call in (("SRC", src), ("DST", dst)):
        rows = call("product.template", "search_read",
                    [[("name", "ilike", name), ("active", "=", True)]],
                    {"fields": ["id","name","product_variant_count","is_published"]})
        for r in sorted(rows, key=lambda x: -x.get('product_variant_count', 0)):
            print(f"    [{lbl}] id={r['id']:>5} variants={r.get('product_variant_count'):>4} "
                  f"pub={r.get('is_published')!s:5} '{r['name']}'")


title("OVERALL hide_on_website count check")
for lbl, call in (("SRC", src), ("DST", dst)):
    n = call("product.product", "search_count",
             [[("hide_on_website", "=", True), ("active", "=", True)]])
    print(f"  [{lbl}] variants with hide_on_website=True: {n}")
