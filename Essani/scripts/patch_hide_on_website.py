"""One-shot patch: copy hide_on_website from SRC variants to DST variants.

The original promote run missed this field (it wasn't in VARIANT_FIELDS).
This script:
1. Walks all SRC variants with hide_on_website=True
2. For each, finds the dst counterpart via the template's __promote__ XID and
   ptav signature matching
3. Writes hide_on_website=True on the dst variant

Idempotent: reading the dst current state first and only writing if different.
"""
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


def main():
    src = connect('SRC'); dst = connect('DST')
    print(">>> SRC =", os.environ['SRC_DB'])
    print(">>> DST =", os.environ['DST_DB'])

    # 1) Find all SRC variants with hide_on_website=True (active only)
    src_hidden = src("product.product", "search_read",
                     [[("hide_on_website", "=", True), ("active", "=", True)]],
                     {"fields": ["id","default_code","product_tmpl_id",
                                 "product_template_attribute_value_ids","active"]})
    print(f"\nSRC variants with hide_on_website=True: {len(src_hidden)}")

    # 2) Group by SRC template
    by_tmpl = {}
    for v in src_hidden:
        if not v.get("product_tmpl_id"):
            continue
        tmpl_id = v["product_tmpl_id"][0]
        by_tmpl.setdefault(tmpl_id, []).append(v)

    print(f"Across {len(by_tmpl)} SRC templates\n")

    fixed = 0; missing_xid = 0; missing_dst_var = 0; already_ok = 0
    for src_tmpl_id, src_vars in by_tmpl.items():
        # Find dst template by XID
        xid = dst("ir.model.data", "search_read",
                  [[("module","=","__promote__"),
                    ("name","=",f"tmpl_{src_tmpl_id}"),
                    ("model","=","product.template")]],
                  {"fields": ["res_id"], "limit": 1})
        if not xid:
            missing_xid += len(src_vars)
            print(f"  ! src_tmpl_id={src_tmpl_id}: no __promote__ XID found ({len(src_vars)} variants skipped)")
            continue
        dst_tmpl_id = xid[0]["res_id"]
        # Get all DST variants of this template + their ptav sigs
        dst_vars = dst("product.product", "search_read",
                       [[("product_tmpl_id","=",dst_tmpl_id)]],
                       {"fields": ["id","hide_on_website",
                                   "product_template_attribute_value_ids"]})
        dst_key_to = {}
        for dv in dst_vars:
            key = ptav_signature(dst, dv["product_template_attribute_value_ids"])
            dst_key_to[key] = dv
        # For each src variant, find dst counterpart and write
        for sv in src_vars:
            key = ptav_signature(src, sv["product_template_attribute_value_ids"])
            dv = dst_key_to.get(key)
            if not dv:
                missing_dst_var += 1
                print(f"  ! src#{sv['id']} ptav={set(key)}: no DST counterpart in tmpl#{dst_tmpl_id}")
                continue
            if dv.get("hide_on_website"):
                already_ok += 1
                continue
            dst("product.product", "write", [[dv["id"]], {"hide_on_website": True}])
            fixed += 1
            print(f"  + src#{sv['id']} -> dst#{dv['id']} hide_on_website=True (tmpl#{dst_tmpl_id})")

    print(f"\n=== summary ===")
    print(f"  fixed (write applied):      {fixed}")
    print(f"  already correct:            {already_ok}")
    print(f"  missing __promote__ XID:    {missing_xid}")
    print(f"  no DST variant match:       {missing_dst_var}")


if __name__ == "__main__":
    main()
