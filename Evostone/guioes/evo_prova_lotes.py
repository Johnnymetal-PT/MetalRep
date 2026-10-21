# -*- coding: utf-8 -*-
"""«Cada chapa nao e' um lote» — a CFO tem razao. Isto prova-o com os dados dela.

`O MAL-ENTENDIDO`
Eu escrevi «cada chapa e' um lote». Usei a palavra no sentido do Odoo, onde um
`stock.lot` e' a unidade rastreada. Ela leu no sentido do negocio, onde um lote
e' o **conjunto** que vem do mesmo bloco. Ela esta certa, e o sistema tambem
modela assim:

    o utilizador escreve UM nome por linha da encomenda  ->  "NOME_BASE"
        base.lot.group    o lote comercial, com o custo medio (PCMP)
        stock.lot         #1/CODIGO/NOME_BASE, #2/..., um por chapa
        lot.price.group   agrupa as chapas de dimensoes iguais — e' aqui o preco

`O QUE ISTO MUDA NA PRATICA`
Ele nao tem de criar 160 lotes a' mao. Escreve o nome do lote do fornecedor em
cada linha e o sistema numera as chapas.

Recebe a P00002 real em transaccao revertida e mostra o que ficou criado.
"""

print('')
print('=' * 74)
print('UM LOTE, MUITAS CHAPAS — PROVADO NA P00002')
print('=' * 74)

antes = {m: env[m].search_count([]) for m in
         ('stock.lot', 'stock.quant') if m in env}
for m in ('base.lot.group', 'lot.price.group'):
    if m in env:
        antes[m] = env[m].search_count([])
print('  antes: %s' % '  '.join('%s=%d' % (k.split('.')[-1], v)
                                for k, v in sorted(antes.items())))

try:
    enc = env['purchase.order'].search([('name', '=', 'P00002')], limit=1)
    linhas = enc.order_line.filtered(lambda l: not l.display_type)
    print('  %s   %d linhas   %.2f EUR   %s'
          % (enc.name, len(linhas), enc.amount_total, enc.partner_id.name))

    print('')
    print('  1. UM nome de lote por linha — como o fornecedor os identifica')
    # `UM NOME POR LINHA, E NAO MENOS` — tentei primeiro dar o mesmo nome a
    # varias linhas e rebentou com «Expected singleton: product.product(...)».
    # O `base.lot.group` e' unico por (nome, produto, empresa): um lote
    # pertence a **um** material. Faz sentido no negocio — um lote e' o
    # conjunto de chapas do mesmo bloco, nao uma remessa com materiais
    # misturados.
    for i, l in enumerate(linhas, 1):
        l.lot_name = 'CONT26-%02d' % i
    nomes = sorted(set(linhas.mapped('lot_name')))
    print('     nomes de lote usados: %d  ->  %s' % (len(nomes), ', '.join(nomes)))
    print('     quantidade total de chapas: %s'
          % sum(linhas.mapped('product_qty')))

    print('')
    print('  2. confirmar e receber...')
    w = env['purchase.confirm.wizard'].create({'purchase_order_id': enc.id})
    w.action_confirm()
    enc.invalidate_recordset()
    p = enc.picking_ids[0]
    for mv in p.move_ids:
        mv.quantity = mv.product_uom_qty
    p.button_validate()
    p.invalidate_recordset()
    print('     %s -> %s' % (p.name, p.state))

    print('')
    print('  3. O QUE O SISTEMA CRIOU')
    print('')
    if 'base.lot.group' in env:
        gs = env['base.lot.group'].search([])
        print('     lotes comerciais (base.lot.group): %d' % len(gs))
        for g in gs[:6]:
            print('       %-18s %-42s pcmp=%s'
                  % (g.base_lot_name or '-', (g.product_id.name or '')[:42],
                     round(getattr(g, 'pcmp', 0) or 0, 2)))
    lotes = env['stock.lot'].search([])
    print('')
    print('     chapas individuais (stock.lot): %d' % len(lotes))
    for lt in lotes[:8]:
        print('       %-34s base=%-14s %sx%sx%s'
              % ((lt.name or '')[:34], getattr(lt, 'base_lot_name', '') or '-',
                 getattr(lt, 'length', 0), getattr(lt, 'width', 0),
                 getattr(lt, 'thickness', 0)))
    if 'lot.price.group' in env:
        pgs = env['lot.price.group'].search([])
        print('')
        print('     grupos de preco (lot.price.group): %d' % len(pgs))
        for g in pgs[:6]:
            print('       %-46s preco=%s'
                  % ((g.display_name or '')[:46], getattr(g, 'list_price', 0)))

    print('')
    print('     existencias: %d     lancamentos contabilisticos: %d'
          % (env['stock.quant'].search_count([]),
             env['account.move'].search_count([])))

    print('')
    print('  4. A CONTA QUE INTERESSA')
    print('     nomes escritos a mao pelo utilizador : %d' % len(nomes))
    print('     chapas numeradas pelo sistema        : %d' % len(lotes))
except Exception as e:
    print('')
    print('  FALHOU: %s' % str(e).replace('\n', ' ')[:300])
finally:
    env.cr.rollback()
    print('')
    print('  ROLLBACK feito — nada ficou gravado.')
    env.cr.execute('select count(*) from stock_quant')
    print('  existencias na base: %s' % env.cr.fetchone()[0])

print('')
print('LOTES=FIM')
