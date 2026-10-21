"""Retry the 4 product.document records that failed during promote with WinError 10054.

Reads each src doc, finds the dst target (template via __promote__ XID or
variant via ptav signature), checks dedup by (name, res_model, res_id), and
creates if missing.
"""
import os, xmlrpc.client
from pathlib import Path

FAILED_DOC_IDS = [11064, 11066, 11359, 16037]


def connect(lbl):
    url = os.environ[f'{lbl}_URL'].rstrip('/'); db = os.environ[f'{lbl}_DB']
    key = os.environ[f'{lbl}_API_KEY']
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, os.environ[f'{lbl}_LOGIN'], key, {})
    m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    def call(model, method, args, kwargs=None):
        return m.execute_kw(db, uid, key, model, method, args, kwargs or {})
    return call


def ptav_sig(call, ptav_ids):
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
    env = Path(__file__).with_name(".promote.env")
    for raw in env.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip(chr(34)).strip(chr(39)))

    src = connect("SRC"); dst = connect("DST")

    src_doc_meta = src("product.document", "fields_get", [], {"attributes": ["type"]})
    candidate = ['name', 'datas', 'mimetype', 'type', 'url',
                 'res_model', 'res_id',
                 'shown_on_product_page', 'attached_on_mobile', 'attached_on']
    doc_fields = [f for f in candidate if f in src_doc_meta]

    for src_id in FAILED_DOC_IDS:
        doc = src("product.document", "read", [[src_id], doc_fields])
        if not doc:
            print(f"src#{src_id}: not found in SRC")
            continue
        doc = doc[0]
        print(f"\n--- src#{src_id} '{doc['name']}' ({doc['res_model']}#{doc['res_id']}) ---")

        # Resolve dst target by res_model
        if doc["res_model"] == "product.template":
            src_tmpl_id = doc["res_id"]
            xid = dst("ir.model.data", "search_read",
                      [[("module","=","__promote__"),
                        ("name","=",f"tmpl_{src_tmpl_id}"),
                        ("model","=","product.template")]],
                      {"fields": ["res_id"], "limit": 1})
            if not xid:
                print(f"  ! no __promote__ XID for src_tmpl_id={src_tmpl_id}")
                continue
            dst_res_id = xid[0]["res_id"]
        elif doc["res_model"] == "product.product":
            src_var_id = doc["res_id"]
            sv = src("product.product", "read",
                     [[src_var_id], ["product_tmpl_id","product_template_attribute_value_ids"]])
            if not sv:
                print(f"  ! src variant {src_var_id} not found")
                continue
            sv = sv[0]
            src_tmpl_id = sv["product_tmpl_id"][0]
            # Find dst template
            xid = dst("ir.model.data", "search_read",
                      [[("module","=","__promote__"),
                        ("name","=",f"tmpl_{src_tmpl_id}"),
                        ("model","=","product.template")]],
                      {"fields": ["res_id"], "limit": 1})
            if not xid:
                print(f"  ! no __promote__ XID for src_tmpl_id={src_tmpl_id}")
                continue
            dst_tmpl_id = xid[0]["res_id"]
            src_sig = ptav_sig(src, sv["product_template_attribute_value_ids"])
            # Look up dst variant
            dvs = dst("product.product", "search_read",
                      [[("product_tmpl_id","=",dst_tmpl_id)]],
                      {"fields": ["id","product_template_attribute_value_ids"]})
            dst_res_id = None
            for dv in dvs:
                if ptav_sig(dst, dv["product_template_attribute_value_ids"]) == src_sig:
                    dst_res_id = dv["id"]
                    break
            if not dst_res_id:
                print(f"  ! no DST variant for src#{src_var_id} sig={set(src_sig)}")
                continue
        else:
            print(f"  ! unsupported res_model={doc['res_model']}")
            continue

        # Dedup by (name, res_model, res_id)
        existing = dst("product.document", "search",
                       [[("name","=",doc["name"]),
                         ("res_model","=",doc["res_model"]),
                         ("res_id","=",dst_res_id)]], {})
        if existing:
            print(f"  ~ already exists on {doc['res_model']}#{dst_res_id} (id={existing[0]}) -- skip")
            continue

        # Create
        vals = {k: doc[k] for k in doc_fields if k in doc and k != "id"}
        vals["res_id"] = dst_res_id
        # Filter to dst's available fields
        dst_doc_fields = dst("product.document", "fields_get", [], {"attributes": ["readonly"]})
        safe_vals = {}
        for k, v in vals.items():
            info = dst_doc_fields.get(k)
            if not info: continue
            if info.get("readonly"): continue
            safe_vals[k] = v
        try:
            new_id = dst("product.document", "create", [safe_vals])
            size_kb = len(doc.get("datas") or "") * 3 // 4 // 1024
            print(f"  + created dst doc#{new_id} ({size_kb} KB) on {doc['res_model']}#{dst_res_id}")
        except Exception as exc:
            print(f"  ! create failed: {exc}")


if __name__ == "__main__":
    main()
