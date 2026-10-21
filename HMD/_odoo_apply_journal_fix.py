"""APLICA o fix do diario por defeito (ESCREVE em producao):
  1) apaga os ir.default de account.move.journal_id (ids 460, 461)
  2) baixa a sequence do diario Vendor Bills (FTF, id=12) de 6 -> 5

Uso:
    python _odoo_apply_journal_fix.py            # dry-run (so mostra)
    python _odoo_apply_journal_fix.py --apply     # aplica
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
ex = xmlrpc.client.ServerProxy(f'{URL}/xmlrpc/2/object', allow_none=True)
APPLY = '--apply' in sys.argv
print('uid =', uid, '| modo =', 'APPLY' if APPLY else 'DRY-RUN')

VENDOR_BILLS_ID = 12
NEW_SEQ = 5

# --- Estado ANTES ---
defs = ex.execute_kw(DB, uid, KEY, 'ir.default', 'search_read',
    [[('field_id.model', '=', 'account.move'), ('field_id.name', '=', 'journal_id')]],
    {'fields': ['id', 'json_value', 'condition']})
def_ids = [d['id'] for d in defs]
print('\nir.default account.move.journal_id (antes):')
for d in defs:
    print(f"  id={d['id']} value={d['json_value']} condition={d.get('condition')}")

jb = ex.execute_kw(DB, uid, KEY, 'account.journal', 'read',
                   [[VENDOR_BILLS_ID]], {'fields': ['name', 'code', 'sequence', 'type']})[0]
print(f"\nVendor Bills (antes): {jb}")

if not APPLY:
    print(f"\nDRY-RUN: apagaria ir.default {def_ids} e poria sequence={NEW_SEQ} no diario {VENDOR_BILLS_ID}.")
    raise SystemExit

# --- Aplicar ---
if def_ids:
    ex.execute_kw(DB, uid, KEY, 'ir.default', 'unlink', [def_ids])
    print(f"\n[OK] ir.default apagados: {def_ids}")
ex.execute_kw(DB, uid, KEY, 'account.journal', 'write', [[VENDOR_BILLS_ID], {'sequence': NEW_SEQ}])
print(f"[OK] Vendor Bills (id={VENDOR_BILLS_ID}) sequence -> {NEW_SEQ}")

# --- Verificacao DEPOIS ---
print('\n--- Verificacao pos-fix ---')
left = ex.execute_kw(DB, uid, KEY, 'ir.default', 'search_count',
    [[('field_id.model', '=', 'account.move'), ('field_id.name', '=', 'journal_id')]])
print(f"ir.default journal_id restantes: {left}")
for jtype in ('sale', 'purchase'):
    js = ex.execute_kw(DB, uid, KEY, 'account.journal', 'search_read',
                       [[('type', '=', jtype), ('company_id', '=', 1)]],
                       {'fields': ['id', 'name', 'code', 'sequence'], 'limit': 1})
    j = js[0]
    print(f"  default {jtype}: {j['name']} (code={j['code']}, seq={j['sequence']})")
for ctx_label, ctx in [("out_invoice", {'default_move_type': 'out_invoice'}),
                       ("in_invoice", {'default_move_type': 'in_invoice'})]:
    vals = ex.execute_kw(DB, uid, KEY, 'account.move', 'default_get',
                         [['journal_id', 'move_type']], {'context': ctx})
    jid = vals.get('journal_id')
    jn = ex.execute_kw(DB, uid, KEY, 'account.journal', 'read', [[jid]], {'fields': ['name']})[0]['name'] if jid else None
    print(f"  default_get[{ctx_label}] -> journal_id={jid} ({jn})")
print('\nDONE.')
