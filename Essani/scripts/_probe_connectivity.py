"""Connectivity probe for promote_products.py — read-only."""
import os, sys, xmlrpc.client
from pathlib import Path

env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def probe(label):
    url = os.environ[f"{label}_URL"].rstrip("/")
    db = os.environ[f"{label}_DB"]
    login = os.environ[f"{label}_LOGIN"]
    key = os.environ[f"{label}_API_KEY"]
    print(f"[{label}] {url}  db={db}  login={login}  key=***{key[-6:]}")
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    info = common.version()
    print(f"  server version: {info.get('server_version')}")
    uid = common.authenticate(db, login, key, {})
    print(f"  uid={uid}")
    if not uid:
        return False
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    counts = {m: models.execute_kw(db, uid, key, m, "search_count", [[]])
              for m in ("product.template", "product.product", "product.image")}
    try:
        counts["product.document"] = models.execute_kw(db, uid, key, "product.document", "search_count", [[]])
    except Exception:
        counts["product.document"] = "N/A"
    print(f"  counts: {counts}")
    return True

ok_src = probe("SRC"); print()
ok_dst = probe("DST")
sys.exit(0 if (ok_src and ok_dst) else 1)
