# -*- coding: utf-8 -*-
"""As linhas das encomendas estrangeiras nao levam codigo de isencao.

`O QUE SE PASSA`
A P00002 (Turquia) e a P00001 (Espanha) foram criadas antes de os artigos terem
imposto de compra na ficha. As linhas ficaram **sem imposto nenhum** — e isso
nao e' o mesmo que isento: uma linha sem imposto nao transporta codigo para a
declaracao, ao passo que `0% EX` ou `23% EU G` transportam.

Recalcular as linhas repoe o imposto a partir da ficha do artigo e da posicao
fiscal da encomenda. O valor **nao muda**: 0% EX e 23% EU G nao produzem IVA.

`A GUARDA`
O guiao compara o total de cada encomenda antes e depois, e **recusa-se a
gravar** se algum mudar. A P00003 (EDP, Portugal) tem duas linhas sem imposto
que, recalculadas, apanhariam 23% e mudariam o total — por isso nao entra na
lista. Nao e' a mesma situacao: aquelas sao linhas de texto de uma factura
portuguesa, e a decisao e' do cliente.

  FASE=ver       o que mudaria
  FASE=aplicar   grava (exige ESCREVER=1)
"""
import os

FASE = os.environ.get('FASE', 'ver')
ESCREVER = os.environ.get('ESCREVER') == '1'

ALVOS = ('P00001', 'P00002')

print('')
print('=' * 74)
print('CODIGO DE ISENCAO NAS LINHAS DAS ENCOMENDAS ESTRANGEIRAS')
print('=' * 74)

encs = env['purchase.order'].search([('name', 'in', list(ALVOS))])
print('  encomendas: %s' % ', '.join(encs.mapped('name')))

antes = {}
for e in encs:
    antes[e.id] = (e.amount_untaxed, e.amount_tax, e.amount_total)
    print('')
    print('  %s  %s  (%s)  pf=%s'
          % (e.name, e.partner_id.name, e.partner_id.country_id.name or '-',
             e.fiscal_position_id.name or '(nenhuma)'))
    print('    linhas: %d   sem imposto: %d'
          % (len(e.order_line),
             len(e.order_line.filtered(lambda l: not l.taxes_id))))
    print('    base %.2f   IVA %.2f   total %.2f' % antes[e.id])

print('')
print('--- a recalcular (em memoria) ---')
for e in encs:
    for l in e.order_line:
        l._compute_tax_id()
    e.invalidate_recordset()

mudou_valor = []
for e in encs:
    depois = (e.amount_untaxed, e.amount_tax, e.amount_total)
    impostos = sorted(set(e.order_line.mapped('taxes_id.name')))
    print('')
    print('  %s' % e.name)
    print('    impostos nas linhas: %s' % (', '.join(impostos) or '(nenhum)'))
    print('    sem imposto: %d' % len(e.order_line.filtered(lambda l: not l.taxes_id)))
    print('    antes  base %.2f  IVA %.2f  total %.2f' % antes[e.id])
    print('    depois base %.2f  IVA %.2f  total %.2f' % depois)
    if abs(depois[2] - antes[e.id][2]) > 0.005:
        mudou_valor.append(e.name)

print('')
if mudou_valor:
    env.cr.rollback()
    print('  PARADO: o total mudaria em %s. Nao gravo.' % ', '.join(mudou_valor))
elif FASE != 'aplicar':
    env.cr.rollback()
    print('  (ensaio — nenhum total muda; FASE=aplicar ESCREVER=1 para gravar)')
elif not ESCREVER:
    env.cr.rollback()
    print('  (ensaio — ESCREVER=1 para gravar)')
else:
    env.cr.commit()
    print('  GRAVADO.')
    print('')
    print('--- releitura da base ---')
    for e in env['purchase.order'].search([('name', 'in', list(ALVOS))]):
        print('  %s  total %.2f  sem imposto: %d  impostos: %s'
              % (e.name, e.amount_total,
                 len(e.order_line.filtered(lambda l: not l.taxes_id)),
                 ', '.join(sorted(set(e.order_line.mapped('taxes_id.name')))) or '-'))

print('')
print('IMPOSTOS_ENC=FIM')
