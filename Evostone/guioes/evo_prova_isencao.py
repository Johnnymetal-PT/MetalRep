# -*- coding: utf-8 -*-
"""A factura de compra ao fornecedor turco sai isenta ou com 23%?

`PORQUE E' QUE ESTA PERGUNTA NAO SE RESPONDE A OLHO`
A CFO diz que os 22 artigos sao compra externa e portanto isentos. Eu pus-lhes
23% de IVA de compra. Ambas as coisas podem estar certas ao mesmo tempo, porque
no Odoo o imposto do artigo e' so' um **ponto de partida**: a posicao fiscal do
fornecedor e' que decide o que sai na factura.

A base tem `Extra-comunitario (Nao UE)` a mapear `23% -> 0% EX`, com aplicacao
automatica, e o fornecedor das chapas e' turco. Mas ler a configuracao nao e'
prova — ja' me enganei hoje a ler configuracao. Esta e' a prova: tres facturas
de compra, tres fornecedores de tres origens, e o imposto que cada uma produz.

`E HA UMA TERCEIRA PERGUNTA`
As 23 linhas da P00002 nao tem imposto **nenhum**. Isso nao e' o mesmo que
isento: uma compra isenta tem de sair com o codigo de isencao para entrar bem
na declaracao. Este guiao mostra tambem o que acontece se a P00002 for
facturada como esta.

Tudo em transaccao revertida.
"""

print('')
print('=' * 74)
print('O IMPOSTO QUE CADA COMPRA PRODUZ')
print('=' * 74)


def factura_de(fornecedor, artigo, etiqueta):
    f = env['account.move'].create({
        'move_type': 'in_invoice',
        'partner_id': fornecedor.id,
        'invoice_date': '2026-09-16',
        'invoice_line_ids': [(0, 0, {'product_id': artigo.id,
                                     'quantity': 1, 'price_unit': 1000.0})],
    })
    l = f.invoice_line_ids[0]
    print('')
    print('  %s' % etiqueta)
    print('    fornecedor      : %s (%s)' % (fornecedor.name, fornecedor.country_id.name or '-'))
    print('    posicao fiscal  : %s' % (f.fiscal_position_id.name or '(nenhuma)'))
    print('    artigo          : %s' % (artigo.name or '')[:52])
    print('    imposto na ficha: %s' % (' | '.join(artigo.supplier_taxes_id.mapped('name')) or '(nenhum)'))
    print('    imposto na linha: %s' % (' | '.join(l.tax_ids.mapped('name')) or '>>> NENHUM'))
    print('    base %10.2f   IVA %10.2f   total %10.2f'
          % (f.amount_untaxed, f.amount_tax, f.amount_total))
    return f


try:
    chapa = env['product.product'].search(
        [('name', 'ilike', 'BIANCO LASA')], limit=1)
    if not chapa:
        chapa = env['product.product'].search([('purchase_ok', '=', True)], limit=1)

    turco = env['res.partner'].search([('name', 'ilike', 'KUTAHYA')], limit=1)
    espanhol = env['res.partner'].search([('name', 'ilike', 'ELYCO')], limit=1)
    portugues = env['res.partner'].search([('name', 'ilike', 'JUFIL')], limit=1)

    if turco:
        factura_de(turco, chapa, 'A) TURQUIA — extra-comunitario (o caso dos 22 artigos)')
    if espanhol:
        factura_de(espanhol, chapa, 'B) ESPANHA — intra-comunitario')
    if portugues:
        factura_de(portugues, chapa, 'C) PORTUGAL — mercado interno')

    print('')
    print('-' * 74)
    print('E A P00002 REAL, SE FOR FACTURADA COMO ESTA')
    print('-' * 74)
    enc = env['purchase.order'].search([('name', '=', 'P00002')], limit=1)
    if enc:
        print('  encomenda       : %s   %s   pf=%s'
              % (enc.name, enc.partner_id.name, enc.fiscal_position_id.name or '-'))
        print('  linhas          : %d' % len(enc.order_line))
        print('  linhas sem imposto: %d'
              % len(enc.order_line.filtered(lambda l: not l.taxes_id)))
        print('  total sem imposto : %.2f' % enc.amount_untaxed)
        print('  imposto           : %.2f' % enc.amount_tax)
        print('')
        print('  O que sai na declaracao: uma linha sem imposto nenhum nao')
        print('  transporta codigo de isencao. Uma linha a 0%% EX transporta.')
        print('')
        # e o que aconteceria se as linhas fossem recalculadas agora
        antes = enc.amount_tax
        enc.order_line._compute_tax_id() if hasattr(enc.order_line, '_compute_tax_id') else None
        print('  depois de recalcular os impostos das linhas:')
        for l in enc.order_line[:4]:
            print('    %-44s %s' % ((l.name or '')[:44],
                                    ' | '.join(l.taxes_id.mapped('name')) or '(sem imposto)'))
        print('  linhas sem imposto: %d'
              % len(enc.order_line.filtered(lambda l: not l.taxes_id)))
        print('  imposto: %.2f -> %.2f' % (antes, enc.amount_tax))
finally:
    env.cr.rollback()
    print('')
    print('  ROLLBACK feito — nada ficou gravado.')
    env.cr.execute('select count(*) from account_move')
    print('  account_move na base: %s' % env.cr.fetchone()[0])

print('')
print('ISENCAO=FIM')
