"""Investigate why product.public.category was duplicated during promote."""
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

src = connect('SRC'); dst = connect('DST')

# For each problematic category name, dump full record from both DBs
for name in ('Cabos de Alimentação', 'Acessórios de distribuição',
             'Acessórios LED-DISTRIBUIÇÃO', 'Sistemas Elevatórios'):
    print(f"\n{'='*70}\n{name}\n{'='*70}")
    for label, call in (('SRC', src), ('DST', dst)):
        rows = call("product.public.category", "search_read",
                    [[("name", "ilike", name)]],
                    {"fields": ["id","name","parent_id","display_name","website_id","sequence"]})
        for r in rows:
            parent = r['parent_id'][1] if r.get('parent_id') else '(root)'
            parent_id = r['parent_id'][0] if r.get('parent_id') else False
            website = r['website_id'][1] if r.get('website_id') else '(no website)'
            print(f"  [{label}] id={r['id']:>4} parent_id={parent_id!s:>5} '{r.get('display_name')}'  "
                  f"website='{website}'  seq={r.get('sequence')}")
