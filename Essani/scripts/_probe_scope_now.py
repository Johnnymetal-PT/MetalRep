"""Scope probe — count templates in SRC and inspect DST state.

Reports:
- SRC: total templates (active), with default_code, with attribute_lines, is_published
- DST: total templates (active + archived counts), templates that share default_code with SRC
- Cross-DB: how many SRC templates would currently match DST by default_code
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


def main():
    src = connect("SRC")
    dst = connect("DST")
    print(f">>> SRC = {os.environ['SRC_DB']}")
    print(f">>> DST = {os.environ['DST_DB']}")

    print("\n--- SRC ---")
    src_total = src("product.template", "search_count", [[]])
    src_active = src("product.template", "search_count", [[("active", "=", True)]])
    src_published = src("product.template", "search_count",
                        [[("active", "=", True), ("is_published", "=", True)]])
    src_with_code = src("product.template", "search_count",
                        [[("active", "=", True), ("default_code", "!=", False)]])
    src_with_attrs = src("product.template", "search_count",
                         [[("active", "=", True), ("attribute_line_ids", "!=", False)]])
    print(f"  total templates (any active state): {src_total}")
    print(f"  active templates: {src_active}")
    print(f"  active + is_published: {src_published}")
    print(f"  active + has default_code: {src_with_code}")
    print(f"  active + has attribute_lines: {src_with_attrs}")

    print("\n--- DST ---")
    dst_active = dst("product.template", "search_count", [[("active", "=", True)]])
    dst_archived = dst("product.template", "search_count",
                       [[("active", "=", False)]])
    print(f"  active templates: {dst_active}")
    print(f"  archived templates: {dst_archived}")

    print("\n--- Stale __promote__ XIDs in DST ---")
    stale_xids = dst("ir.model.data", "search_count",
                     [[("module", "=", "__promote__"),
                       ("model", "=", "product.template")]])
    print(f"  ir.model.data rows with module=__promote__ on product.template: {stale_xids}")

    print("\n--- SRC active templates that share default_code with DST active ---")
    src_codes = [r["default_code"] for r in src("product.template", "search_read",
                  [[("active", "=", True), ("default_code", "!=", False)]],
                  {"fields": ["default_code"]})]
    if src_codes:
        sample = src_codes[:5]
        collisions = dst("product.template", "search_count",
                         [[("active", "=", True), ("default_code", "in", src_codes)]])
        print(f"  src codes total: {len(src_codes)}, sample={sample}")
        print(f"  active DST templates colliding with SRC codes: {collisions}")
        collisions_arch = dst("product.template", "search_count",
                              [[("active", "=", False), ("default_code", "in", src_codes)]])
        print(f"  archived DST templates with same codes: {collisions_arch}")


if __name__ == "__main__":
    main()
