# -*- coding: utf-8 -*-
"""Renderiza TODOS os documentos alcancaveis e diz quais rebentam.

`PORQUE E' QUE ISTO TINHA DE EXISTIR`
Eu disse ao cliente que os documentos estavam corrigidos depois de provar **um**
— a ordem de compra P00002. A factura nunca foi renderizada, e rebenta:
`'account.move' object has no attribute 'migration'`, um campo do account_MZ,
a localizacao mocambicana que nao esta instalada nesta base portuguesa.

Provar um documento nao prova os outros. Este guiao percorre todas as accoes de
relatorio, arranja um registo para cada modelo (real se existir, criado e
revertido se nao) e tenta gerar o HTML. O que interessa nao e' a vista estar
bonita: e' o documento **sair**.

Corre sempre em transaccao revertida.
"""
import traceback

MODELOS = ('purchase.order', 'sale.order', 'account.move', 'stock.picking',
           'account.payment', 'proforma.payment')

print('')
print('=' * 74)
print('TODOS OS DOCUMENTOS, RENDERIZADOS')
print('=' * 74)

criados = {}


def arranja(modelo):
    """Um registo deste modelo: o real do cliente, ou um temporario."""
    if modelo in criados:
        return criados[modelo]
    reg = env[modelo].search([], order='id desc', limit=1)
    if reg:
        criados[modelo] = (reg, 'real')
        return criados[modelo]
    parceiro = env['res.partner'].search(
        [('id', '!=', env.company.partner_id.id)], limit=1)
    artigo = env['product.product'].search([], limit=1)
    try:
        if modelo == 'account.move':
            reg = env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': parceiro.id,
                'invoice_date': '2026-09-15',
                'invoice_line_ids': [(0, 0, {'product_id': artigo.id,
                                             'quantity': 2, 'price_unit': 1000.0})],
            })
        elif modelo == 'sale.order':
            reg = env['sale.order'].create({
                'partner_id': parceiro.id,
                'order_line': [(0, 0, {'product_id': artigo.id,
                                       'product_uom_qty': 2, 'price_unit': 1000.0})],
            })
        elif modelo == 'purchase.order':
            tipo = env['service.type'].search([], limit=1)
            reg = env['purchase.order'].create({
                'partner_id': parceiro.id,
                'service_type_id': tipo.id,
                'order_line': [(0, 0, {'product_id': artigo.id, 'name': artigo.name,
                                       'product_qty': 2, 'price_unit': 1000.0,
                                       'date_planned': '2026-09-30'})],
            })
        else:
            reg = None
    except Exception as e:
        print('    (nao consegui criar %s: %s)' % (modelo, str(e)[:90]))
        reg = None
    criados[modelo] = (reg, 'temporario' if reg else 'nenhum')
    return criados[modelo]


bons, maus = [], []
try:
    accoes = env['ir.actions.report'].search(
        [('model', 'in', list(MODELOS))], order='model, report_name')
    print('  accoes de relatorio: %d' % len(accoes))
    modelo_actual = None
    for a in accoes:
        if a.model != modelo_actual:
            modelo_actual = a.model
            print('')
            print('--- %s ---' % modelo_actual)
        reg, origem = arranja(a.model)
        if not reg:
            print('  %-46s  (sem registo para testar)' % a.report_name[:46])
            continue
        try:
            html = a._render_qweb_html(a.report_name, reg.ids)[0]
            if isinstance(html, bytes):
                html = html.decode('utf-8', 'replace')
            bons.append(a.report_name)
            print('  [OK] %-42s %6d car.  (%s %s)'
                  % (a.report_name[:42], len(html), origem, reg.display_name or ''))
        except Exception as e:
            env.cr.rollback()
            criados.clear()
            linha = [l for l in traceback.format_exc().splitlines()
                     if 'Error' in l or 'error' in l]
            maus.append((a.report_name, (linha[-1] if linha else str(e)).strip()))
            print('  [!!] %-42s %s' % (a.report_name[:42], (linha[-1] if linha else str(e)).strip()[:80]))
finally:
    env.cr.rollback()
    print('')
    print('  ROLLBACK feito.')
    env.cr.execute('select count(*) from account_move')
    print('  account_move na base: %s' % env.cr.fetchone()[0])

print('')
print('=' * 74)
print('  imprimem: %d    rebentam: %d' % (len(bons), len(maus)))
for n, e in maus:
    print('    REBENTA: %-40s %s' % (n, e[:100]))
print('=' * 74)
print('')
print('DOCUMENTOS=FIM')
