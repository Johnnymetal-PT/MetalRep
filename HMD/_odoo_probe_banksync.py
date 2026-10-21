"""Probe SO-LEITURA: estado da sincronizacao bancaria online (account_online_synchronization)."""
import xmlrpc.client, datetime

env = {}
for line in open('data_local/odoo_hmd.env', encoding='utf-8'):
    if '=' in line and not line.strip().startswith('#'):
        k, v = line.strip().split('=', 1); env[k] = v
URL, DB, LOGIN, KEY = env['ODOO_URL'], env['ODOO_DB'], env['ODOO_LOGIN'], env['ODOO_KEY']
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
uid = common.authenticate(DB, LOGIN, KEY, {})
print('uid =', uid, '| version =', common.version().get('server_version'))
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

def rpc(m, meth, *a, **k):
    assert meth in {'search_read', 'read', 'search_count', 'fields_get'}, meth
    return models.execute_kw(DB, uid, KEY, m, meth, list(a), k)

def dump(model, domain, fields):
    print(f'\n===== {model} =====')
    try:
        fg = set(rpc(model, 'fields_get', [], attributes=['string']).keys())
        flds = [f for f in fields if f in fg]
        recs = rpc(model, 'search_read', domain, fields=flds, limit=50)
        print(f'  ({len(recs)} registos)')
        for r in recs:
            print('  ' + ' | '.join(f'{f}={r.get(f)}' for f in flds))
    except Exception as e:
        print('  ERRO:', str(e)[:200])

# DB uuid + eventual flag de duplicacao
print('\n===== ir.config_parameter (uuid / online sync) =====')
try:
    ps = rpc('ir.config_parameter', 'search_read',
             ['|', '|', ('key', 'ilike', 'uuid'), ('key', 'ilike', 'online'),
              ('key', 'ilike', 'ocn')], fields=['key', 'value'])
    for p in ps:
        print(f"  {p['key']} = {p['value']}")
except Exception as e:
    print('  ERRO:', str(e)[:200])

dump('account.online.link',
     [],
     ['id', 'name', 'state', 'provider_data', 'last_refresh',
      'next_refresh', 'expiring_synchronization_date', 'auto_sync', 'company_id',
      'has_unlinked_accounts', 'provider_type'])

dump('account.online.account',
     [],
     ['id', 'name', 'account_online_link_id', 'account_number', 'journal_ids',
      'last_sync', 'balance', 'account_data'])

dump('account.journal',
     [('bank_statements_source', '!=', False)],
     ['id', 'name', 'bank_statements_source', 'account_online_account_id',
      'account_online_link_id'])
