# -*- coding: utf-8 -*-
"""Prova a recepcao completa da P00002, atribuindo lotes as linhas.

`PORQUE` — a confirmacao falha com «Existem produtos com lote 'SEM-LOTE' que
requerem rastreamento». Falta saber se, **com** lote, a cadeia inteira passa:
confirmar, receber, valorizar, criar existencias. Sem isso eu estaria a dizer ao
cliente «crie lotes» sem saber se depois disso corre.

Nada fica: rollback no fim.
"""
import os

print('')
print('=' * 72)
print('RECEPCAO COMPLETA COM LOTES — ENSAIO REVERTIDO')
print('=' * 72)
env.cr.execute('SELECT current_database()')
print('  base: %s' % env.cr.fetchone()[0])

try:
    enc = env['purchase.order'].search([('name', '=', 'P00002')], limit=1)
    linhas = enc.order_line.filtered(lambda l: not l.display_type)
    print('  %s   %d linhas   %.2f EUR' % (enc.name, len(linhas), enc.amount_total))

    campo = 'lot_name' if 'lot_name' in linhas._fields else None
    print('  campo de lote na linha: %s' % (campo or 'NAO EXISTE'))
    if not campo:
        raise SystemExit
    sem = linhas.filtered(lambda l: l.lot_name == 'SEM-LOTE')
    print('  linhas com SEM-LOTE: %d de %d' % (len(sem), len(linhas)))

    print('')
    print('  1. dar nome de lote a cada linha...')
    for i, l in enumerate(linhas, 1):
        if l.lot_name == 'SEM-LOTE' or not l.lot_name:
            l.lot_name = 'ENS-%03d' % i
    print('     linhas com lote proprio: %d'
          % len(linhas.filtered(lambda l: l.lot_name and l.lot_name != 'SEM-LOTE')))

    print('')
    print('  2. confirmar pelo assistente...')
    w = env['purchase.confirm.wizard'].create({'purchase_order_id': enc.id})
    w.action_confirm()
    enc.invalidate_recordset()
    print('     estado: %s' % enc.state)
    rec = enc.picking_ids
    print('     recepcoes: %d  %s' % (len(rec), ', '.join(rec.mapped('name'))))

    if rec:
        p = rec[0]
        print('')
        print('  3. receber...')
        for mv in p.move_ids:
            mv.quantity = mv.product_uom_qty
        p.button_validate()
        p.invalidate_recordset()
        print('     estado da recepcao: %s' % p.state)
        print('')
        print('  4. o que ficou:')
        print('     existencias  : %d' % env['stock.quant'].search_count([]))
        print('     lotes        : %d' % env['stock.lot'].search_count([]))
        print('     lancamentos  : %d' % env['account.move'].search_count([]))
        q = env['stock.quant'].search([], limit=3)
        for x in q:
            print('       %-42s %s %s em %s'
                  % ((x.product_id.name or '')[:42], x.quantity,
                     x.product_uom_id.name, x.location_id.complete_name))
except Exception as e:
    print('')
    print('  FALHOU: %s' % str(e).replace('\n', ' ')[:280])
finally:
    env.cr.rollback()
    print('')
    print('  ROLLBACK feito.')
    env.cr.execute('select count(*) from stock_quant')
    print('  existencias na base: %s' % env.cr.fetchone()[0])

print('')
print('RECEPCAO_LOTE=FIM')
