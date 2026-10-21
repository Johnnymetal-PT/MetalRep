"""Fix do diario por defeito nas Faturas de Cliente.

Dry-run (sem args): SO-LEITURA, lista os ir.default de account.move.journal_id.
Com '--apply': APAGA o(s) ir.default desse campo (corrige o bug).

Uso:
    python _odoo_fix_journal_default.py            # dry-run (nao altera nada)
    python _odoo_fix_journal_default.py --apply     # aplica (unlink)
"""
import sys
import xmlrpc.client

env = {}
for line in open('data_local/odoo_hmd.env', encoding='utf-8'):
    if '=' in line and not line.strip().startswith('#'):
        k, v = line.strip().split('=', 1); env[k] = v
URL, DB, LOGIN, KEY = env['ODOO_URL'], env['ODOO_DB'], env['ODOO_LOGIN'], env['ODOO_KEY']
common = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/common', allow_none=True)
uid = common.authenticate(DB, LOGIN, KEY, {})
models = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)
APPLY = '--apply' in sys.argv

print('uid =', uid, '| modo =', 'APPLY (escreve)' if APPLY else 'DRY-RUN (so-leitura)')

# So mexemos no campo journal_id de account.move.
recs = models.execute_kw(DB, uid, KEY, 'ir.default', 'search_read',
    [[('field_id.model', '=', 'account.move'), ('field_id.name', '=', 'journal_id')]],
    {'fields': ['id', 'field_id', 'json_value', 'user_id', 'company_id', 'condition']})

print('\nir.default em account.move.journal_id encontrados:')
for r in recs:
    print(f"  id={r['id']} value={r['json_value']} user={r['user_id']} "
          f"company={r['company_id']} condition={r.get('condition')}")
ids = [r['id'] for r in recs]

if not ids:
    print('\n(nada para apagar)')
elif APPLY:
    models.execute_kw(DB, uid, KEY, 'ir.default', 'unlink', [ids])
    print(f"\nAPAGADOS ir.default ids={ids}.")
    print("Standard _compute_journal_id volta a decidir: out_invoice -> diario de venda; in_invoice -> diario de compra.")
else:
    print(f"\nDRY-RUN: seriam apagados ir.default ids={ids}. Correr com --apply para aplicar.")

print('\nDONE.')
