"""Recover the 8 product.document records that didn't make it during the
main run. For each one:

  1. Read metadata from Staging via XML-RPC.
  2. Resolve the destination (product.template or product.product) in Production.
  3. Dedup-skip if a non-empty document already exists in DST.
  4. Read the binary `datas` from Staging via XML-RPC (response side --
     typically larger limit than request side on Odoo.sh).
  5. Save the decoded file to scripts/_failed_docs/ for manual UI upload.
  6. ALSO try uploading via XML-RPC `product.document.create`. Some of the
     ~70 MB files may now pass (server-side conditions may have stabilised).
  7. Write a manifest CSV with: src_id, name, target dst record,
     local file path, upload status (UPLOADED | LOCAL_ONLY).

The XML-RPC body limit (~100 MB after base64 expansion -> ~75 MB raw) means
files above that range can only be uploaded by hand via the Odoo backend.
"""

import base64
import csv
import os
import re
import sys
import xmlrpc.client
from pathlib import Path


DOC_IDS_TO_RECOVER = [
    12090,  # 3D - EFL2.12671.dxf       (134.9 MB)  src#2103
    11387,  # 3D - ES31.3-V2-F1.dxf     (122.7 MB)
    12743,  # 3D - EF25.V1.F1.3000.dxf  (142.0 MB)
    13070,  # 3D - ESEL5.V1-F3.dxf      (152.3 MB)
    11064,  # 3D - EAFT6.7.V1.F1.dxf    (TCP reset, smaller)
    11066,  # 3D - EAFT6.7.V1.F1.dxf    (TCP reset, smaller)
    16037,  # 3D - EAFT.007.001-V1-F1.dxf (TCP reset)
    11359,  # 3D - ES16.V1-F1.dxf       (TCP reset)
]

env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class OdooRPC:
    def __init__(self, url, db, login, api_key, label):
        self.url = url.rstrip("/")
        self.db = db
        self.api_key = api_key
        self.label = label
        common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common", allow_none=True)
        self.uid = common.authenticate(db, login, api_key, {})
        if not self.uid:
            raise RuntimeError(f"[{label}] auth failed")
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)
        print(f"[{label}] uid={self.uid}")

    def kw(self, model, method, args, kwargs=None):
        return self.models.execute_kw(self.db, self.uid, self.api_key, model, method, args, kwargs or {})


def ptav_key(rpc, ptav_ids):
    if not ptav_ids:
        return frozenset()
    rows = rpc.kw("product.template.attribute.value", "read",
                  [ptav_ids, ["attribute_id", "product_attribute_value_id"]])
    return frozenset(
        (r["attribute_id"][1] if r["attribute_id"] else None,
         r["product_attribute_value_id"][1] if r["product_attribute_value_id"] else None)
        for r in rows
    )


def resolve_target(src_rpc, dst_rpc, meta):
    src_model, src_id = meta["res_model"], meta["res_id"]
    if src_model == "product.template":
        imd = dst_rpc.kw("ir.model.data", "search_read",
                         [[("module", "=", "__promote__"), ("name", "=", f"tmpl_{src_id}")]],
                         {"fields": ["res_id"], "limit": 1})
        return ("product.template", imd[0]["res_id"]) if imd else None
    if src_model == "product.product":
        sv = src_rpc.kw("product.product", "read",
                        [[src_id], ["product_tmpl_id", "product_template_attribute_value_ids"]])[0]
        src_tmpl_id = sv["product_tmpl_id"][0]
        imd = dst_rpc.kw("ir.model.data", "search_read",
                         [[("module", "=", "__promote__"), ("name", "=", f"tmpl_{src_tmpl_id}")]],
                         {"fields": ["res_id"], "limit": 1})
        if not imd:
            return None
        dst_tmpl_id = imd[0]["res_id"]
        want = ptav_key(src_rpc, sv["product_template_attribute_value_ids"])
        for v in dst_rpc.kw("product.product", "search_read",
                            [[("product_tmpl_id", "=", dst_tmpl_id)]],
                            {"fields": ["product_template_attribute_value_ids"]}):
            if ptav_key(dst_rpc, v["product_template_attribute_value_ids"]) == want:
                return ("product.product", v["id"])
        return None
    return None


def sanitize(name):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)


def process(src_rpc, dst_rpc, src_doc_id, local_dir):
    print(f"\n--- src#{src_doc_id} ---")
    meta = src_rpc.kw("product.document", "read",
                       [[src_doc_id],
                        ["name", "mimetype", "res_model", "res_id", "file_size",
                         "shown_on_product_page"]])[0]
    name = meta["name"]
    raw_mb = (meta.get("file_size") or 0) / 1024 / 1024
    print(f"  name={name!r}  src target={meta['res_model']}#{meta['res_id']}  size={raw_mb:.1f} MB")

    target = resolve_target(src_rpc, dst_rpc, meta)
    if not target:
        print(f"  ! could not resolve dst target -- SKIPPED")
        return {"src_id": src_doc_id, "name": name, "size_mb": raw_mb,
                "target": "UNRESOLVED", "local_file": "", "status": "SKIPPED"}
    tmodel, tid = target
    print(f"  -> dst target = {tmodel}#{tid}")

    # Dedup
    existing = dst_rpc.kw("product.document", "search_read",
                          [[("name", "=", name),
                            ("res_model", "=", tmodel),
                            ("res_id", "=", tid)]],
                          {"fields": ["file_size"], "limit": 1})
    if existing and (existing[0].get("file_size") or 0) > 0:
        sz_exist = (existing[0]["file_size"] or 0) / 1024 / 1024
        print(f"  ~ already in DST (id={existing[0]['id']}, {sz_exist:.1f} MB) -- skipped")
        return {"src_id": src_doc_id, "name": name, "size_mb": raw_mb,
                "target": f"{tmodel}#{tid}", "local_file": "",
                "status": f"ALREADY_IN_DST (id={existing[0]['id']})"}

    # Read binary from Staging via XML-RPC (response side)
    print(f"  + reading binary from Staging ({raw_mb:.1f} MB raw, ~{raw_mb * 4 / 3:.1f} MB base64)...")
    try:
        src_full = src_rpc.kw("product.document", "read", [[src_doc_id], ["datas"]])[0]
        datas_b64 = src_full.get("datas")
    except Exception as exc:
        print(f"  ! read from Staging failed: {type(exc).__name__}: {exc}")
        return {"src_id": src_doc_id, "name": name, "size_mb": raw_mb,
                "target": f"{tmodel}#{tid}", "local_file": "",
                "status": f"READ_FAILED: {exc}"}
    if not datas_b64:
        print(f"  ! source has no datas")
        return {"src_id": src_doc_id, "name": name, "size_mb": raw_mb,
                "target": f"{tmodel}#{tid}", "local_file": "",
                "status": "NO_DATAS"}

    # Save locally for manual upload fallback
    local_name = f"{src_doc_id:06d}__{sanitize(name)}"
    local_path = local_dir / local_name
    raw_bytes = base64.b64decode(datas_b64)
    local_path.write_bytes(raw_bytes)
    actual_mb = local_path.stat().st_size / 1024 / 1024
    print(f"  + saved locally: {local_path.name} ({actual_mb:.1f} MB)")

    # Skip upload attempt for very large files (definitely > XML-RPC limit)
    if actual_mb > 70:
        print(f"  ! {actual_mb:.1f} MB > 70 MB -- not attempting XML-RPC upload (would TCP-reset)")
        return {"src_id": src_doc_id, "name": name, "size_mb": round(actual_mb, 1),
                "target": f"{tmodel}#{tid}", "local_file": str(local_path),
                "status": "LOCAL_ONLY (oversize)"}

    # Attempt XML-RPC upload
    print(f"  + attempting product.document.create via XML-RPC...")
    vals = {
        "name": name,
        "mimetype": meta.get("mimetype") or "application/octet-stream",
        "res_model": tmodel,
        "res_id": tid,
        "type": "binary",
        "datas": datas_b64,
    }
    if "shown_on_product_page" in meta:
        vals["shown_on_product_page"] = meta.get("shown_on_product_page")
    try:
        new_id = dst_rpc.kw("product.document", "create", [vals])
        print(f"    + UPLOADED dst#{new_id}")
        # Clean up local file since upload succeeded
        try:
            local_path.unlink()
        except OSError:
            pass
        return {"src_id": src_doc_id, "name": name, "size_mb": round(actual_mb, 1),
                "target": f"{tmodel}#{tid}", "local_file": "",
                "status": f"UPLOADED (dst#{new_id})"}
    except Exception as exc:
        print(f"    ! upload failed: {type(exc).__name__}: {str(exc)[:200]}")
        return {"src_id": src_doc_id, "name": name, "size_mb": round(actual_mb, 1),
                "target": f"{tmodel}#{tid}", "local_file": str(local_path),
                "status": f"LOCAL_ONLY (upload failed: {type(exc).__name__})"}


def main():
    src_rpc = OdooRPC(os.environ["SRC_URL"], os.environ["SRC_DB"],
                       os.environ["SRC_LOGIN"], os.environ["SRC_API_KEY"], "SRC")
    dst_rpc = OdooRPC(os.environ["DST_URL"], os.environ["DST_DB"],
                       os.environ["DST_LOGIN"], os.environ["DST_API_KEY"], "DST")

    local_dir = Path(__file__).parent / "_failed_docs"
    local_dir.mkdir(exist_ok=True)
    print(f"local_dir = {local_dir}")

    results = []
    for sid in DOC_IDS_TO_RECOVER:
        try:
            results.append(process(src_rpc, dst_rpc, sid, local_dir))
        except Exception as exc:
            print(f"  FAILED src#{sid}: {type(exc).__name__}: {exc}")
            results.append({"src_id": sid, "name": "", "size_mb": 0,
                            "target": "ERROR", "local_file": "",
                            "status": f"ERROR: {type(exc).__name__}"})

    # Write manifest CSV
    manifest = local_dir / "_manifest.csv"
    with open(manifest, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["src_id", "name", "size_mb", "target", "local_file", "status"])
        w.writeheader()
        for r in results:
            w.writerow(r)
    print(f"\nmanifest written to {manifest}")

    uploaded = sum(1 for r in results if r["status"].startswith("UPLOADED"))
    already = sum(1 for r in results if r["status"].startswith("ALREADY_IN_DST"))
    local_only = sum(1 for r in results if r["status"].startswith("LOCAL_ONLY"))
    other = len(results) - uploaded - already - local_only
    print(f"=== uploaded={uploaded}  already_in_dst={already}  local_only={local_only}  other={other} ===")


if __name__ == "__main__":
    main()
