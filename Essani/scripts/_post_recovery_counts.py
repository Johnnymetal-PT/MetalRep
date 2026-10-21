"""Verify counts after recovery."""
import os, xmlrpc.client
from pathlib import Path
env = Path('scripts/.promote.env')
for raw in env.read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or '=' not in line: continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
url = os.environ['DST_URL'].rstrip('/'); db = os.environ['DST_DB']; key = os.environ['DST_API_KEY']
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
uid = common.authenticate(db, os.environ['DST_LOGIN'], key, {})
m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
def call(model, method, args, kw=None):
    return m.execute_kw(db, uid, key, model, method, args, kw or {})

print("Post-recovery counts:")
print(f"  active templates total = {call('product.template','search_count',[[('active','=',True),('sale_ok','=',True)]])}")
print(f"  active templates no_code = {call('product.template','search_count',[[('active','=',True),('sale_ok','=',True),('default_code','=',False)]])}")
print(f"  active variants total = {call('product.product','search_count',[[('active','=',True)]])}")
print(f"  active variants no_code = {call('product.product','search_count',[[('active','=',True),('default_code','=',False)]])}")
print()
print(f"  archived templates total = {call('product.template','search_count',[[('active','=',False),('sale_ok','=',True)]])}")
print(f"  archived templates no_code = {call('product.template','search_count',[[('active','=',False),('sale_ok','=',True),('default_code','=',False)]])}")
