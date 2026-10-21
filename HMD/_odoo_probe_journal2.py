"""SO-LEITURA v2: default real do journal_id em out_invoice + ir.default/ir.property."""
import xmlrpc.client

env = {}
for line in open('data_local/odoo_hmd.env', encoding='utf-8'):
    if '=' in line and not line.strip().startswith('#'):
        k, v = line.strip().split('=', 1); env[k] = v
URL, DB, LOGIN, KEY = env['ODOO_URL'], env['ODOO_DB'], env['ODOO_LOGIN'], env['ODOO_KEY']
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
uid = common.authenticate(DB, LOGIN, KEY, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)

# default_get e onchange sao read-only (nao fazem commit); permitidos aqui.
SAFE = {'search_read', 'read', 'search_count', 'fields_get', 'default_get'}
def rpc(m, meth, *a, **k):
    assert meth in SAFE, meth
    return models.execute_kw(DB, uid, KEY, m, meth, list(a), k)

print('uid =', uid)

print('\n===== ir.default para account.move (defaults definidos pelo utilizador/admin) =====')
defs = rpc('ir.default', 'search_read',
           [('field_id.model', '=', 'account.move')],
           fields=['field_id', 'json_value', 'user_id', 'company_id', 'condition'])
if not defs:
    print('  (nenhum ir.default em account.move)')
for d in defs:
    print(f"  field={d['field_id']} value={d['json_value']} user={d['user_id']} "
          f"company={d['company_id']} condition={d.get('condition')}")

print('\n===== default_get(journal_id) num out_invoice (contexto da accao tipica) =====')
for ctx_label, ctx in [
    ("default_move_type=out_invoice", {'default_move_type': 'out_invoice'}),
    ("+ journal_type=sale", {'default_move_type': 'out_invoice', 'journal_type': 'sale'}),
    ("move_type=out_invoice (sem default_)", {'move_type': 'out_invoice'}),
]:
    try:
        vals = models.execute_kw(DB, uid, KEY, 'account.move', 'default_get',
                                 [['journal_id', 'move_type']], {'context': ctx})
        print(f"  ctx[{ctx_label}] -> {vals}")
    except Exception as e:
        print(f"  ctx[{ctx_label}] -> ERRO: {str(e)[:160]}")

print('\n===== Resolver nome dos journal ids referidos =====')
for jid in (11, 12):
    j = rpc('account.journal', 'read', [jid], fields=['name', 'type', 'code'])
    print('  ', j)

print('\n===== Empresa: campos de diario por defeito? (account_journal_id em res.company/config) =====')
try:
    comp = rpc('res.company', 'read', [1], fields=['name'])
    cf = rpc('res.company', 'fields_get', [], attributes=['type', 'string'])
    jcands = {k: v for k, v in cf.items() if 'journal' in k.lower()}
    print('  campos *journal* em res.company:', list(jcands.keys()))
    if jcands:
        vals = rpc('res.company', 'read', [1], fields=list(jcands.keys()))
        print('  valores:', vals)
except Exception as e:
    print('  erro:', str(e)[:160])

print('\nDONE (so-leitura).')
