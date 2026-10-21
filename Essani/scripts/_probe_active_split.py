"""Split image/document/variant counts by active vs archived parent, both DBs.

Goal: determine how much of DST's inflation vs the backup is archived residue
vs real duplication on ACTIVE products. Read-only.
"""
import os, xmlrpc.client
from pathlib import Path

env = Path('scripts/.promote.env')
for raw in env.read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def connect(prefix):
    url = os.environ[f'{prefix}_URL'].rstrip('/')
    db = os.environ[f'{prefix}_DB']
    login = os.environ[f'{prefix}_LOGIN']
    key = os.environ[f'{prefix}_API_KEY']
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, login, key, {})
    m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)

    def call(model, method, args, kw=None):
        return m.execute_kw(db, uid, key, model, method, args, kw or {})
    return call


def analyze(tag, call):
    print(f"\n===== {tag} =====")

    def safe(label, fn):
        try:
            fn()
        except Exception as exc:
            print(f"  {label}: ERR {exc!r}")

    act_tmpl_set = set()
    act_var_ids = set()

    def counts():
        t_act = call("product.template", "search_count", [[("active", "=", True), ("sale_ok", "=", True)]])
        t_arch = call("product.template", "search_count", [[("active", "=", False), ("sale_ok", "=", True)]])
        print(f"  templates sale_ok: active={t_act}  archived={t_arch}")
        v_act = call("product.product", "search_count", [[("active", "=", True)]])
        v_arch = call("product.product", "search_count", [[("active", "=", False)]])
        print(f"  variants:          active={v_act}  archived={v_arch}")
    safe("counts", counts)

    def load_active():
        act_tmpl_set.update(call("product.template", "search", [[("active", "=", True)]]))
        act_var_ids.update(call("product.product", "search", [[("active", "=", True)]]))
    safe("load active ids", load_active)

    def timg_block():
        timg = call("product.image", "search_read", [[("product_variant_id", "=", False)]],
                    {"fields": ["product_tmpl_id"]})
        timg_act = sum(1 for r in timg if r["product_tmpl_id"] and r["product_tmpl_id"][0] in act_tmpl_set)
        print(f"  product.image (template-level): total={len(timg)}  on_active_tmpl={timg_act}  on_archived/orphan={len(timg)-timg_act}")
    safe("template images", timg_block)

    def vimg_block():
        vimg = call("product.image", "search_read", [[("product_variant_id", "!=", False)]],
                    {"fields": ["product_variant_id"]})
        vimg_act = sum(1 for r in vimg if r["product_variant_id"] and r["product_variant_id"][0] in act_var_ids)
        print(f"  product.image (variant-level):  total={len(vimg)}  on_active_var={vimg_act}  on_archived/orphan={len(vimg)-vimg_act}")
    safe("variant images", vimg_block)

    def tdoc_block():
        tdoc = call("product.document", "search_read", [[("res_model", "=", "product.template")]],
                    {"fields": ["res_id"]})
        tdoc_act = sum(1 for r in tdoc if r["res_id"] in act_tmpl_set)
        print(f"  product.document on template:   total={len(tdoc)}  on_active_tmpl={tdoc_act}  on_archived/orphan={len(tdoc)-tdoc_act}")
    safe("template docs", tdoc_block)

    def pdoc_block():
        # search ids first, then count active subset via search_count to dodge attachment read traps
        pdoc_ids = call("product.document", "search", [[("res_model", "=", "product.product")]])
        total = len(pdoc_ids)
        pdoc = call("product.document", "read", [pdoc_ids, ["res_id"]])
        pdoc_act = sum(1 for r in pdoc if r["res_id"] in act_var_ids)
        print(f"  product.document on variant:    total={total}  on_active_var={pdoc_act}  on_archived/orphan={total-pdoc_act}")
    safe("variant docs", pdoc_block)


def main():
    analyze("SRC (backup 2026-05-10 18:07)", connect('SRC'))
    analyze("DST (current main)", connect('DST'))


if __name__ == "__main__":
    main()
