"""SO-LEITURA: apurar a colisao exata no diario 12 (Vendor Bills) para o out_invoice draft id=4337."""
import xmlrpc.client
env = {}
for line in open('data_local/odoo_hmd.env', encoding='utf-8'):
    if '=' in line and not line.strip().startswith('#'):
        k, v = line.strip().split('=', 1); env[k] = v
URL, DB, LOGIN, KEY = env['ODOO_URL'], env['ODOO_DB'], env['ODOO_LOGIN'], env['ODOO_KEY']
uid = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True).authenticate(DB, LOGIN, KEY, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)
def rpc(m, meth, *a, **k):
    assert meth in {'search_read', 'read', 'search_count', 'fields_get'}, meth
    return models.execute_kw(DB, uid, KEY, m, meth, list(a), k)

print('===== Diario 12: movimento de referencia (date<=2026-06-15, date desc) =====')
ref = rpc('account.move', 'search_read',
          [('journal_id', '=', 12), ('name', 'not in', ('/', '', False)), ('date', '<=', '2026-06-15')],
          fields=['name', 'date', 'move_type', 'state', 'sequence_prefix', 'sequence_number'],
          order='date desc, id desc', limit=8)
for m in ref:
    print(f"  {m['name']!r:22} date={m['date']} type={m['move_type']:11} state={m['state']:7} "
          f"prefix={m.get('sequence_prefix')!r} seq#={m.get('sequence_number')}")

print('\n===== Diario 12: todos os FT A/ (sequencia) =====')
fta = rpc('account.move', 'search_read',
          [('journal_id', '=', 12), ('name', 'like', 'FT A/')],
          fields=['name', 'date', 'move_type', 'state', 'sequence_number'],
          order='sequence_number', limit=200)
print(f"  total FT A/ no diario 12: {len(fta)}")
for m in fta:
    print(f"    {m['name']!r:14} date={m['date']} type={m['move_type']:11} state={m['state']}")

print('\n===== Diario 12: refund_sequence/payment_sequence + codigo =====')
j = rpc('account.journal', 'read', [12], fields=['name', 'code', 'type', 'refund_sequence', 'payment_sequence'])[0]
print(f"  {j}")
print('\nDONE (so-leitura).')
