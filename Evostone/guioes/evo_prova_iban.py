# -*- coding: utf-8 -*-
"""Prova que o IBAN sai impresso nos documentos.

`PORQUE NAO CHEGA VER A CONTA NA FICHA`
A conta existe na `res.partner.bank` — isso prova que foi gravada, nao que
aparece no papel. O bloco dos dados bancarios nos modelos percorre
`o.company_id.partner_id.bank_ids`; se a conta tivesse ficado no parceiro
errado, ou noutra empresa, a listagem da ficha continuaria a dizer que esta' la'
e o documento sairia em branco.

E' a mesma regra que ja' me serviu hoje duas vezes: a contagem nao prova, o
documento prova.

Corre em transaccao revertida — a factura de teste nao fica gravada.
"""
import re

IBAN_NU = 'PT50001800036905960802090'

print('')
print('=' * 72)
print('O IBAN NO PAPEL')
print('=' * 72)

emp = env.company
print('  empresa: %s' % emp.name)
contas = env['res.partner.bank'].search([('partner_id', '=', emp.partner_id.id)])
for c in contas:
    print('  conta  : %-32s %s' % (c.acc_number, c.bank_id.name or '-'))


def procura(html, etiqueta):
    if isinstance(html, bytes):
        html = html.decode('utf-8', 'replace')
    liso = re.sub(r'<[^>]+>', ' ', html)
    liso = re.sub(r'\s+', ' ', liso)
    # o Odoo imprime o IBAN com espacos; comparar sem eles e' o unico modo justo
    sem_espacos = liso.replace(' ', '')
    achou = IBAN_NU in sem_espacos
    print('')
    print('  %-34s %s' % (etiqueta, 'IBAN PRESENTE' if achou else 'IBAN AUSENTE'))
    print('    Santander no texto: %s' % ('sim' if 'Santander' in liso else 'nao'))
    i = sem_espacos.find(IBAN_NU)
    if i > 0:
        j = liso.replace(' ', '').index(IBAN_NU)
        # reconstituir o trecho a partir do texto com espacos, por posicao aproximada
        k = liso.find('PT50')
        if k > 0:
            print('    impresso: %s' % liso[max(0, k - 90):k + 60].strip())
    return achou


try:
    # 1. o documento real do cliente
    enc = env['purchase.order'].search([], order='id desc', limit=1)
    if enc:
        acc = env.ref('mh_stone_reports.action_report_purchaseorder')
        procura(acc._render_qweb_html(acc.report_name, enc.ids)[0],
                'ordem de compra %s' % enc.name)

    # 2. uma factura de venda — e' onde o IBAN importa, porque e' o documento
    #    com que o cliente dele paga. Nao ha nenhuma na base, cria-se e reverte-se.
    cli = env['res.partner'].search([('id', '!=', emp.partner_id.id)], limit=1)
    art = env['product.product'].search([('sale_ok', '=', True)], limit=1)
    fac = env['account.move'].create({
        'move_type': 'out_invoice',
        'partner_id': cli.id,
        'invoice_date': '2026-09-15',
        'invoice_line_ids': [(0, 0, {
            'product_id': art.id,
            'quantity': 1,
            'price_unit': 100.0,
        })],
    })
    accao = env['ir.actions.report'].search(
        [('model', '=', 'account.move'),
         ('report_name', 'like', 'mh_stone_reports.%')], limit=1)
    if not accao:
        print('')
        print('  (sem accao de relatorio de factura em mh_stone_reports)')
    else:
        print('')
        print('  relatorio: %s' % accao.report_name)
        procura(accao._render_qweb_html(accao.report_name, fac.ids)[0],
                'factura de venda (temporaria)')
finally:
    env.cr.rollback()
    print('')
    print('  ROLLBACK feito — a factura de teste nao ficou gravada.')
    env.cr.execute('select count(*) from account_move')
    print('  account_move na base: %s' % env.cr.fetchone()[0])
    env.cr.execute("select count(*) from res_partner_bank where active")
    print('  contas activas: %s' % env.cr.fetchone()[0])

print('')
print('PROVA_IBAN=FIM')
