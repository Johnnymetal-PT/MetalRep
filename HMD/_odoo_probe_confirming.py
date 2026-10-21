"""Verificacao SO-LEITURA no Odoo HMD via XML-RPC.
APENAS metodos de leitura: search_read / search_count / read. Nao escreve nada.
Credenciais lidas de data_local/odoo_hmd.env (gitignored)."""
import xmlrpc.client, os

env = {}
with open('data_local/odoo_hmd.env', encoding='utf-8') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env[k] = v
URL, DB, LOGIN, KEY = env['ODOO_URL'], env['ODOO_DB'], env['ODOO_LOGIN'], env['ODOO_KEY']

common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
print('server version:', common.version().get('server_version'))
uid = common.authenticate(DB, LOGIN, KEY, {})
print('AUTH uid =', uid)
if not uid:
    raise SystemExit('Autenticacao falhou.')
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

READONLY = {'search_read', 'search_count', 'read', 'fields_get'}
def rpc(model, method, *args, **kw):
    assert method in READONLY, f'BLOQUEADO metodo nao-leitura: {method}'
    return models.execute_kw(DB, uid, KEY, model, method, list(args), kw)

print('\n========== 1) DIARIOS com "confirm" ==========')
js = rpc('account.journal', 'search_read',
         ['|', ('name', 'ilike', 'confirm'), ('code', 'ilike', 'confirm')],
         fields=['name', 'code', 'type'])
print(js or '  (nenhum diario com "confirm")')

print('\n========== 2) CONTAS com "confirm" ==========')
accs = rpc('account.account', 'search_read',
           [('name', 'ilike', 'confirm')],
           fields=['code', 'name', 'account_type'])
print(accs or '  (nenhuma conta com "confirm")')

print('\n========== 3) MOVIMENTOS na(s) conta(s) de confirming ==========')
for a in accs:
    n = rpc('account.move.line', 'search_count', [('account_id', '=', a['id'])])
    print(f"  conta {a['code']} {a['name']}: {n} linhas")
    if n:
        sample = rpc('account.move.line', 'search_read',
                     [('account_id', '=', a['id'])],
                     fields=['date', 'move_id', 'journal_id', 'debit', 'credit',
                             'payment_id', 'parent_state'],
                     limit=8, order='date desc')
        for s in sample:
            print('    ', s.get('date'), '| jrn', s.get('journal_id'),
                  '| pay', s.get('payment_id'), '| D', s.get('debit'), 'C', s.get('credit'))

print('\n========== 4) BONUS: modulos contabilidade (C2) ==========')
mods = rpc('ir.module.module', 'search_read',
           [('name', 'in', ['account_reports', 'account_accountant',
                            'account_intrastat', 'account_loans', 'hr_expense',
                            'sale_management', 'quality_control'])],
           fields=['name', 'state', 'shortdesc'])
for m in sorted(mods, key=lambda x: x['name']):
    print(f"  {m['name']:22} {m['state']:12} {m['shortdesc']}")

print('\nDONE (so-leitura).')
