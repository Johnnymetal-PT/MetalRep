"""SO-LEITURA: diagnostico do diario por defeito nas Faturas de Cliente (out_invoice)."""
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

print('uid =', uid)

print('\n===== TODOS os account.journal (id, type, code, sequence, name, company) =====')
fields = ['id', 'name', 'code', 'type', 'sequence', 'company_id', 'active']
# campo pg_allowed_user_ids pode nao existir se o modulo nao estiver instalado
jf = rpc('account.journal', 'fields_get', [], attributes=['type'])
has_pg = 'pg_allowed_user_ids' in jf
if has_pg:
    fields.append('pg_allowed_user_ids')
print('campo pg_allowed_user_ids presente?', has_pg)
journals = rpc('account.journal', 'search_read', [('active', 'in', [True, False])],
               fields=fields, order='sequence,type,code')
for j in journals:
    allowed = j.get('pg_allowed_user_ids') if has_pg else 'n/a'
    print(f"  id={j['id']:>4} seq={j['sequence']:>3} type={j['type']:<10} code={str(j['code']):<8} "
          f"active={j['active']} allowed_users={allowed} name={j['name']}")

print('\n===== Diarios type=sale (ordem usada pelo _search_default_journal limit=1) =====')
sales = rpc('account.journal', 'search_read', [('type', '=', 'sale')],
            fields=['id', 'name', 'code', 'sequence', 'company_id'], order='sequence,type,code')
for j in sales:
    print(f"  -> id={j['id']} seq={j['sequence']} code={j['code']} name={j['name']} company={j['company_id']}")

print('\n===== Acao "Customer Invoices" e variantes (context default_journal_id?) =====')
acts = rpc('ir.actions.act_window', 'search_read',
           [('res_model', '=', 'account.move'),
            '|', '|', ('name', 'ilike', 'invoice'), ('name', 'ilike', 'fatura'),
            ('name', 'ilike', 'client')],
           fields=['id', 'name', 'context', 'domain'], limit=40)
for a in acts:
    ctx = a.get('context') or ''
    flag = '  <<< default_journal_id!' if 'journal' in str(ctx).lower() else ''
    print(f"  [{a['id']}] {a['name']}{flag}")
    if 'journal' in str(ctx).lower() or 'out_invoice' in str(ctx):
        print(f"        context={ctx}")

print('\n===== res.users xmlrpc (quem somos) e grupos contab =====')
me = rpc('res.users', 'read', [uid], fields=['login', 'name', 'company_id', 'company_ids'])
print('  ', me)

print('\nDONE (so-leitura).')
