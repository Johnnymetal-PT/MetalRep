"""Verify the user's reported issues against SRC vs DST data.

For each complaint, queries both DBs and reports the mismatch (if any).
Read-only, no writes.
"""
import os
import xmlrpc.client
from pathlib import Path

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
    login = os.environ[f"{label}_LOGIN"]
    key = os.environ[f"{label}_API_KEY"]
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(db, login, key, {})
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    def call(model, method, args, kwargs=None):
        return models.execute_kw(db, uid, key, model, method, args, kwargs or {})
    return call


def section(title):
    print("\n" + "=" * 76 + f"\n  {title}\n" + "=" * 76)


def main():
    src = connect("SRC")
    dst = connect("DST")

    # ---------- 1) Categories with no products visible on website ----------
    section("CLAIM 1+2: Categorias 'Cabos de alimentação' e 'Acessórios de distribuição' vazias")
    for name in ("Cabos de alimentação", "Acessórios de distribuição",
                 "Acessórios LED-DISTRIBUIÇÃO", "Focos LED",
                 "Sistemas Elevatórios", "Sistemas elevatórios"):
        for label, call in (("SRC", src), ("DST", dst)):
            cat = call("product.public.category", "search_read",
                       [[("name", "ilike", name)]], {"fields": ["id", "name"]})
            if not cat:
                continue
            for c in cat:
                tmpl_ids = call("product.template", "search",
                                [[("public_categ_ids", "in", [c["id"]]),
                                  ("active", "=", True)]], {})
                pub = call("product.template", "search_count",
                           [[("public_categ_ids", "in", [c["id"]]),
                             ("active", "=", True), ("is_published", "=", True)]])
                print(f"  [{label}] public_categ '{c['name']}' (id={c['id']})  "
                      f"templates_active={len(tmpl_ids)}  published={pub}")

    # ---------- 3+5) Hidden products that appeared ----------
    section("CLAIM 3+5: Variantes hide_on_website=True em SRC vs DST")
    # Check field exists
    src_pp_fields = src("product.product", "fields_get", [], {"attributes": ["type"]})
    if "hide_on_website" not in src_pp_fields:
        print("  hide_on_website field NOT in SRC.product.product (module not installed?)")
    else:
        src_hidden_count = src("product.product", "search_count",
                                [[("hide_on_website", "=", True), ("active", "=", True)]])
        dst_hidden_count = dst("product.product", "search_count",
                                [[("hide_on_website", "=", True), ("active", "=", True)]])
        print(f"  SRC variants with hide_on_website=True: {src_hidden_count}")
        print(f"  DST variants with hide_on_website=True: {dst_hidden_count}")
        if dst_hidden_count == 0 and src_hidden_count > 0:
            print("  ! BUG: hide_on_website was not copied to DST during promote")
            # Sample 5 src variants with hide_on_website=True to identify scope
            sample = src("product.product", "search_read",
                         [[("hide_on_website", "=", True), ("active", "=", True)]],
                         {"fields": ["id", "default_code", "product_tmpl_id"], "limit": 10})
            print(f"  Sample of hidden variants in SRC:")
            for s in sample:
                print(f"    src#{s['id']} code={s.get('default_code')!r}  tmpl={s['product_tmpl_id']}")

    # ---------- 6-9) Templates with explosive variant counts ----------
    section("CLAIM 6-9: Templates 'iniciais' com variantes explosivas")
    for name in ("LED Eiffel", "LED EFLEX CX120", "LED Aureola", "LED Glassline"):
        for label, call in (("SRC", src), ("DST", dst)):
            rows = call("product.template", "search_read",
                        [[("name", "ilike", name), ("active", "=", True)]],
                        {"fields": ["id", "name", "product_variant_count",
                                    "default_code", "is_published"]})
            if not rows:
                print(f"  [{label}] '{name}' -> none")
                continue
            for r in rows:
                print(f"  [{label}] tmpl#{r['id']:>5}  variants={r.get('product_variant_count'):>4}  "
                      f"published={r.get('is_published')!s:5}  code={(r.get('default_code') or '-'):>20}  "
                      f"name='{r['name']}'")

    # ---------- 4) Focos LED duplicated by voltage - name verification ----------
    section("CLAIM 4: Templates duplicados por voltagem - nomes em SRC vs DST")
    # Find templates with "12V DC" or "24V DC" or similar voltage suffix in SRC
    src_voltage = src("product.template", "search_read",
                       [[("active", "=", True),
                         "|", "|", "|",
                         ("name", "ilike", "12V DC"),
                         ("name", "ilike", "24V DC"),
                         ("name", "ilike", "110-240"),
                         ("name", "ilike", "230V")]],
                       {"fields": ["id", "name"], "limit": 30})
    print(f"  SRC templates with voltage in name: {len(src_voltage)}")
    for s in src_voltage[:15]:
        # Find counterpart in DST by name
        dst_match = dst("product.template", "search_read",
                        [[("name", "=", s["name"]), ("active", "=", True)]],
                        {"fields": ["id", "name"]})
        marker = "OK" if dst_match else "MISSING"
        dst_id = dst_match[0]["id"] if dst_match else "-"
        print(f"  src#{s['id']:>5} '{s['name'][:60]}' -> dst#{dst_id} [{marker}]")

    # ---------- variants missing default_code ----------
    section("Variant default_code coverage")
    sample_tmpls = src("product.template", "search_read",
                       [[("name", "ilike", "Cabo Alimenta"), ("active", "=", True)]],
                       {"fields": ["id", "name", "product_variant_ids"], "limit": 5})
    for s in sample_tmpls:
        if not s.get("product_variant_ids"):
            continue
        svs = src("product.product", "read", [s["product_variant_ids"][:3]],
                  ["default_code"])
        # Find dst counterpart
        dst_t = dst("product.template", "search_read",
                    [[("name", "=", s["name"]), ("active", "=", True)]],
                    {"fields": ["id", "product_variant_ids"], "limit": 1})
        if not dst_t:
            print(f"  src#{s['id']} '{s['name']}' -> dst counterpart MISSING")
            continue
        dvs = dst("product.product", "read",
                  [dst_t[0]["product_variant_ids"][:3]], ["default_code"])
        print(f"  '{s['name']}'")
        for i, sv in enumerate(svs):
            dv = dvs[i] if i < len(dvs) else {}
            print(f"    src variant#{sv['id']} code={sv.get('default_code')!r}  ->  "
                  f"dst variant#{dv.get('id')} code={dv.get('default_code')!r}")


if __name__ == "__main__":
    main()
