"""Probe auth on both DBs separately to pinpoint which credential is dead."""
import os, xmlrpc.client
from pathlib import Path

env = Path('scripts/.promote.env')
for raw in env.read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def probe(tag, url, db, login, key):
    print(f"\n--- {tag}: {url}  db={db} ---")
    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
        ver = common.version()
        print(f"  version ok: {ver.get('server_version')}")
    except Exception as e:
        print(f"  common.version FAILED: {e!r}")
        return
    try:
        uid = common.authenticate(db, login, key, {})
        print(f"  authenticate -> uid={uid!r}")
    except Exception as e:
        print(f"  authenticate FAILED: {e!r}")
        return
    if not uid:
        print("  >>> authenticate returned falsy: login/key invalid for this DB")
        return
    try:
        m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
        n = m.execute_kw(db, uid, key, 'product.template', 'search_count',
                         [[('sale_ok', '=', True)]])
        print(f"  execute_kw search_count product.template(sale_ok) = {n}")
    except Exception as e:
        print(f"  execute_kw FAILED: {e!r}")


probe("SRC (backup)", os.environ['SRC_URL'].rstrip('/'), os.environ['SRC_DB'],
      os.environ['SRC_LOGIN'], os.environ['SRC_API_KEY'])
probe("DST (main)", os.environ['DST_URL'].rstrip('/'), os.environ['DST_DB'],
      os.environ['DST_LOGIN'], os.environ['DST_API_KEY'])
