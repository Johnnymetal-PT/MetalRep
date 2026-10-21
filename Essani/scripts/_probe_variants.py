"""Inspect variant limit setting on both DBs."""
import os, xmlrpc.client
from pathlib import Path

env = Path(__file__).with_name(".promote.env")
for raw in env.read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def check(label):
    url = os.environ[f"{label}_URL"].rstrip("/")
    db = os.environ[f"{label}_DB"]
    login = os.environ[f"{label}_LOGIN"]; key = os.environ[f"{label}_API_KEY"]
    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(db, login, key, {})
    m = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)
    rows = m.execute_kw(db, uid, key, "ir.config_parameter", "search_read",
                        [[("key", "like", "variant")]],
                        {"fields": ["key", "value"]})
    print(f"[{label}] ir.config_parameter keys mentioning 'variant':")
    for r in rows:
        print(f"  {r['key']:45} = {r['value']!r}")
    if not rows:
        print(f"  (none)")

check("SRC")
print()
check("DST")
