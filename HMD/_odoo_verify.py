"""Verificacao SO-LEITURA no Odoo HMD: relatorios (C2) + campos assumidos nos tutoriais."""
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

print('===== C2: account.report disponiveis =====')
try:
    reps = rpc('account.report', 'search_read', [], fields=['name'], limit=60)
    for r in sorted(reps, key=lambda x: x['name']):
        print('  -', r['name'])
except Exception as e:
    print('  erro:', str(e)[:150])

print('\n===== C2: menus de Contabilidade > Relatorios (amostra) =====')
try:
    acts = rpc('ir.actions.act_window', 'search_read',
               ['|', '|', ('name', 'ilike', 'aged'), ('name', 'ilike', 'antig'),
                ('name', 'ilike', 'cash')], fields=['name', 'res_model'], limit=20)
    for a in acts:
        print('  -', a['name'], '->', a['res_model'])
except Exception as e:
    print('  erro:', str(e)[:150])

print('\n===== Modulos relevantes =====')
mods = rpc('ir.module.module', 'search_read',
           [('name', 'in', ['sale_advance_payment', 'ptplus_sale_advance_payment',
                            'pg_sale_advance_payment_access', 'quality', 'quality_control',
                            'sale_management', 'account_reports'])],
           fields=['name', 'state'])
for m in sorted(mods, key=lambda x: x['name']):
    print(f"  {m['name']:32} {m['state']}")

print('\n===== V1: sale.order.template =====')
try:
    n = rpc('sale.order.template', 'search_count', [])
    print('  templates existentes:', n)
    if n:
        for t in rpc('sale.order.template', 'search_read', [], fields=['name'], limit=10):
            print('    -', t['name'])
    fg = rpc('sale.order.template', 'fields_get', [],
             attributes=['type'])
    for f in ['name', 'note', 'number_of_days', 'require_signature', 'require_payment',
              'prepayment_percent', 'sale_order_template_line_ids', 'sale_order_template_option_ids']:
        print(f"    campo {f}: {'OK' if f in fg else 'EM FALTA'}")
except Exception as e:
    print('  erro:', str(e)[:150])

print('\n===== QC: quality.check campos + quality_state =====')
try:
    fg = rpc('quality.check', 'fields_get',
             ['quality_state', 'test_type_id', 'partner_id', 'team_id', 'product_id'],
             attributes=['type', 'selection', 'string'])
    for f, meta in fg.items():
        extra = meta.get('selection') if meta.get('selection') else meta.get('type')
        print(f"  {f}: {extra}")
    tts = rpc('quality.point.test_type', 'search_read', [], fields=['name', 'technical_name'])
    print('  test types:', [t['technical_name'] for t in tts])
except Exception as e:
    print('  erro:', str(e)[:150])

print('\n===== Adiantamentos: sale.order campos =====')
try:
    fg = rpc('sale.order', 'fields_get',
             ['advance_payment_status', 'account_payment_ids', 'amount_residual'],
             attributes=['type', 'string'])
    for f, meta in fg.items():
        print(f"  {f}: {meta.get('type')} ({meta.get('string')})")
except Exception as e:
    print('  erro:', str(e)[:150])

print('\nDONE (so-leitura).')
