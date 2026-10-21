"""SO-LEITURA: que diario o standard _search_default_journal escolheria por tipo (limit=1)."""
import xmlrpc.client
env = {}
for line in open('data_local/odoo_hmd.env', encoding='utf-8'):
    if '=' in line and not line.strip().startswith('#'):
        k, v = line.strip().split('=', 1); env[k] = v
URL, DB, LOGIN, KEY = env['ODOO_URL'], env['ODOO_DB'], env['ODOO_LOGIN'], env['ODOO_KEY']
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
uid = common.authenticate(DB, LOGIN, KEY, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)
def rpc(m, meth, *a, **k):
    assert meth in {'search_read', 'read', 'search_count', 'fields_get'}, meth
    return models.execute_kw(DB, uid, KEY, m, meth, list(a), k)

for jtype in ('sale', 'purchase'):
    print(f'\n=== type={jtype} | ordem standard (sequence,type,code), company=1 ===')
    js = rpc('account.journal', 'search_read',
             [('type', '=', jtype), ('company_id', '=', 1)],
             fields=['id', 'name', 'code', 'sequence'])  # ordem default do modelo
    for i, j in enumerate(js):
        mark = '  <-- ESCOLHIDO (limit=1)' if i == 0 else ''
        print(f"  seq={j['sequence']} code={j['code']:<6} id={j['id']:<3} {j['name']}{mark}")
print('\nDONE (so-leitura).')
