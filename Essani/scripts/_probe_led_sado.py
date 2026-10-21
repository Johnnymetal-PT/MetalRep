"""Diagnostic probe: compare LED Sado 12V DC / 24V DC across Staging (SRC) and Production (DST).

Reports for each template, in each DB:
- template id, default_code, active
- attribute_line_ids (attribute name + value names)
- product_variant_ids (count + active/archived breakdown + default_code per variant)
- product.image extras (count, linkage: template-only vs variant)
- product.document records (count, name, res_model, res_id, file_size)

Then a cross-DB section: how variants, images and documents match (or fail to)
by ptav key (variant signature) and by document name.

Read-only — issues no write calls.
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
    if not uid:
        raise RuntimeError(f"[{label}] auth failed")
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

    def call(model, method, args, kwargs=None):
        return models.execute_kw(db, uid, key, model, method, args, kwargs or {})

    return call


def ptav_signature(call, ptav_ids):
    if not ptav_ids:
        return frozenset()
    rows = call("product.template.attribute.value", "read",
                [ptav_ids, ["attribute_id", "product_attribute_value_id"]])
    return frozenset(
        (r["attribute_id"][1] if r["attribute_id"] else None,
         r["product_attribute_value_id"][1] if r["product_attribute_value_id"] else None)
        for r in rows
    )


def inspect_template(label, call, name):
    print(f"\n{'=' * 70}")
    print(f"[{label}] Looking for template name LIKE '{name}'")
    print('=' * 70)
    tmpl_ids = call("product.template", "search",
                    [[("name", "=", name)]], {})
    if not tmpl_ids:
        tmpl_ids = call("product.template", "search",
                        [[("name", "ilike", name)]], {})
    if not tmpl_ids:
        print(f"  NOT FOUND")
        return []

    tmpls = call("product.template", "read", [tmpl_ids,
                ["id", "name", "default_code", "active",
                 "attribute_line_ids", "product_variant_ids",
                 "product_template_image_ids", "product_document_ids"]])
    out = []
    for t in tmpls:
        print(f"\n  template id={t['id']}  name='{t['name']}'  default_code={t.get('default_code')!r}  active={t['active']}")
        # attribute_lines
        if t.get("attribute_line_ids"):
            lines = call("product.template.attribute.line", "read",
                         [t["attribute_line_ids"], ["attribute_id", "value_ids"]])
            for line in lines:
                attr_name = line["attribute_id"][1] if line["attribute_id"] else "?"
                if line["value_ids"]:
                    vals = call("product.attribute.value", "read",
                                [line["value_ids"], ["name"]])
                    val_names = [v["name"] for v in vals]
                else:
                    val_names = []
                print(f"    attr_line: '{attr_name}' = {val_names}")
        else:
            print(f"    (no attribute_line_ids)")

        # variants — active + archived
        if t.get("product_variant_ids"):
            all_v_ids = call("product.product", "search",
                             [[("product_tmpl_id", "=", t["id"]),
                               "|", ("active", "=", True), ("active", "=", False)]],
                             {})
            vs = call("product.product", "read", [all_v_ids,
                      ["id", "default_code", "active",
                       "product_template_attribute_value_ids"]])
            n_active = sum(1 for v in vs if v["active"])
            n_arch = sum(1 for v in vs if not v["active"])
            print(f"    variants: total={len(vs)} active={n_active} archived={n_arch}")
            for v in vs:
                sig = ptav_signature(call, v["product_template_attribute_value_ids"])
                marker = "" if v["active"] else "  [ARCHIVED]"
                sig_str = ", ".join(f"{a}={val}" for a, val in sorted(sig))
                print(f"      v#{v['id']} code={v.get('default_code')!r}  [{sig_str}]{marker}")
        else:
            print(f"    variants: 0 (no product_variant_ids)")

        # template-level images (product.image where product_variant_id == False)
        tmpl_imgs = call("product.image", "search_read",
                         [[("product_tmpl_id", "=", t["id"]),
                           ("product_variant_id", "=", False)]],
                         {"fields": ["id", "name", "sequence"]})
        print(f"    product.image (template-level): {len(tmpl_imgs)}")
        for im in tmpl_imgs:
            print(f"      img#{im['id']} '{im['name']}' seq={im.get('sequence')}")

        # variant-level images
        var_imgs = call("product.image", "search_read",
                        [[("product_tmpl_id", "=", t["id"]),
                          ("product_variant_id", "!=", False)]],
                        {"fields": ["id", "name", "sequence", "product_variant_id"]})
        print(f"    product.image (variant-level): {len(var_imgs)}")
        for im in var_imgs:
            v = im.get("product_variant_id")
            v_repr = f"variant#{v[0]} '{v[1]}'" if v else "?"
            print(f"      img#{im['id']} '{im['name']}' -> {v_repr} seq={im.get('sequence')}")

        # documents — both res_model variants
        v_ids = t.get("product_variant_ids") or []
        docs = call("product.document", "search_read",
                    [["|",
                      "&", ("res_model", "=", "product.template"), ("res_id", "=", t["id"]),
                      "&", ("res_model", "=", "product.product"),
                            ("res_id", "in", v_ids or [0])]],
                    {"fields": ["id", "name", "res_model", "res_id", "file_size", "mimetype"]})
        print(f"    product.document: {len(docs)}")
        for d in docs:
            size_kb = (d.get("file_size") or 0) / 1024
            print(f"      doc#{d['id']} '{d['name']}'  {d['res_model']}#{d['res_id']}  {size_kb:.0f} KB  {d.get('mimetype')}")

        out.append(t)
    return out


def main():
    sides = []
    for label in ("SRC", "DST"):
        try:
            sides.append((label, connect(label)))
            print(f">>> {label} = {os.environ[f'{label}_DB']} (connected)")
        except Exception as exc:
            print(f">>> {label} = {os.environ[f'{label}_DB']} (FAILED: {exc})")

    for name in ("LED Sado 12V DC", "LED Sado 24V DC"):
        print("\n\n" + "#" * 70)
        print(f"#  {name}")
        print("#" * 70)
        for label, call in sides:
            inspect_template(label, call, name)


if __name__ == "__main__":
    main()
