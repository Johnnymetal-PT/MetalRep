"""SO-LEITURA: diagnostico do erro 'Ja existe um movimento lancado com o mesmo nome'
ao confirmar fatura cliente (GALLERY DESIGN / client_order_ref MIF-PO-001165). Odoo 18."""
import xmlrpc.client
from collections import Counter

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

print('===== 1) Rascunho(s) GALLERY DESIGN / ref MIF-PO-001165 =====')
drafts = rpc('account.move', 'search_read',
             ['|', ('ref', 'ilike', 'MIF-PO-001165'),
              ('invoice_origin', 'ilike', 'MIF-PO-001165')],
             fields=['id', 'name', 'state', 'move_type', 'journal_id', 'invoice_date',
                     'date', 'ref', 'invoice_origin', 'sequence_prefix', 'sequence_number'],
             limit=20)
journ_ids = set()
for d in drafts:
    print(f"  id={d['id']} name={d['name']!r} state={d['state']} type={d['move_type']} "
          f"journal={d['journal_id']} date={d.get('date')} inv_date={d.get('invoice_date')} "
          f"prefix={d.get('sequence_prefix')!r} seq#={d.get('sequence_number')} "
          f"origin={d.get('invoice_origin')}")
    if d.get('journal_id'):
        journ_ids.add(d['journal_id'][0])

print('\n===== 2) Para cada diario envolvido: ultimos publicados + duplicados =====')
for jid in journ_ids:
    j = rpc('account.journal', 'read', [jid], fields=['name', 'code', 'type'])[0]
    print(f"\n  -- Diario {j['name']} ({j['code']}, {j['type']}) id={jid} --")
    posted = rpc('account.move', 'search_read',
                 [('journal_id', '=', jid), ('state', '=', 'posted')],
                 fields=['name', 'sequence_prefix', 'sequence_number', 'date'],
                 order='sequence_prefix, sequence_number desc', limit=2000)
    print(f"    publicados (amostra recente):")
    seen_prefix = set()
    for m in posted:
        p = m.get('sequence_prefix')
        if p not in seen_prefix:
            seen_prefix.add(p)
            print(f"      prefix={p!r} topo: name={m['name']!r} seq#={m.get('sequence_number')} date={m.get('date')}")
    # duplicados de name dentro do diario (a colisao real)
    names = [m['name'] for m in posted]
    dups = {n: c for n, c in Counter(names).items() if c > 1}
    print(f"    nomes DUPLICADOS publicados neste diario: {dups if dups else 'nenhum'}")

print('\nDONE (so-leitura).')
