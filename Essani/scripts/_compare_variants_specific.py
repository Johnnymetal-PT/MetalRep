import os, xmlrpc.client
from pathlib import Path
env = Path('scripts/.promote.env')
for raw in env.read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or '=' not in line: continue
    k, v = line.split('=', 1)
    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def connect(lbl):
    url = os.environ[f'{lbl}_URL'].rstrip('/'); db = os.environ[f'{lbl}_DB']; key = os.environ[f'{lbl}_API_KEY']
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', allow_none=True)
    uid = common.authenticate(db, os.environ[f'{lbl}_LOGIN'], key, {})
    m = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', allow_none=True)
    def call(model, method, args, kwargs=None):
        return m.execute_kw(db, uid, key, model, method, args, kwargs or {})
    return call

src = connect('SRC'); dst = connect('DST')

for product_name in ('Cabo Alimentação 2 PIN 90°', 'Cabo Distribuicao Y ProLine M1'):
    print(f"\n=== {product_name} ===")
    for lbl, call in (('SRC', src), ('DST', dst)):
        ts = call('product.template', 'search_read',
                  [[('name', '=', product_name)]],
                  {'fields': ['id', 'product_variant_ids']})
        for t in ts:
            vs = call('product.product', 'read', [t['product_variant_ids']],
                      {'fields': ['id', 'default_code', 'hide_on_website', 'active']})
            none_codes = sum(1 for v in vs if not v.get('default_code'))
            hidden = sum(1 for v in vs if v.get('hide_on_website'))
            print(f"  [{lbl}] tmpl#{t['id']} variants={len(vs)} no_code={none_codes} hidden={hidden}")
            for v in vs:
                print(f"    v#{v['id']:>7} code={(v.get('default_code') or '-'):20} "
                      f"active={v.get('active')!s:5} hidden={v.get('hide_on_website')!s}")
