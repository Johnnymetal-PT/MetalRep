"""SO-LEITURA: localizar a accao/menu do ir.default (Valores por Defeito) e estado dev mode."""
import xmlrpc.client
env = {}
for line in open('data_local/odoo_hmd.env', encoding='utf-8'):
    if '=' in line and not line.strip().startswith('#'):
        k, v = line.strip().split('=', 1); env[k] = v
URL, DB, LOGIN, KEY = env['ODOO_URL'], env['ODOO_DB'], env['ODOO_LOGIN'], env['ODOO_KEY']
uid = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True).authenticate(DB, LOGIN, KEY, {})
ex = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)
def rpc(m, meth, *a, **k):
    assert meth in {'search_read', 'read', 'search_count', 'fields_get'}, meth
    return ex.execute_kw(DB, uid, KEY, m, meth, list(a), k)

print('=== ir.actions.act_window com res_model=ir.default ===')
acts = rpc('ir.actions.act_window', 'search_read', [('res_model', '=', 'ir.default')],
           fields=['id', 'name'])
print(acts or '  (nenhuma)')

print('\n=== menus que apontam para essas accoes ===')
for a in acts:
    menus = rpc('ir.ui.menu', 'search_read', [('action', '=', f'ir.actions.act_window,{a["id"]}')],
                fields=['id', 'name', 'complete_name'])
    for m in menus:
        print(f"  -> {m.get('complete_name') or m['name']}")
    if not menus:
        print(f"  accao {a['id']} '{a['name']}' NAO tem menu (so acessivel por URL/dev).")

print('\n=== xmlid base.action_default / base.ir_default_menu (se existir) ===')
for xmlid in ('base.action_default', 'base.ir_default_menu', 'base.menu_action_default'):
    try:
        mod, name = xmlid.split('.')
        d = rpc('ir.model.data', 'search_read',
                [('module', '=', mod), ('name', '=', name)],
                fields=['model', 'res_id', 'complete_name'])
        print(f"  {xmlid}: {d or 'inexistente'}")
    except Exception as e:
        print(f"  {xmlid}: erro {str(e)[:80]}")

print('\nDONE.')
