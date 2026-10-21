# -*- coding: utf-8 -*-
"""Prova que a cadeia de facturacao resolve, sem deixar nada na base.

`PORQUE ISTO VALE`
E' a tarefa T3.1 do compromisso — «Teste Tecnico de Faturacao». E e' a pergunta
que ninguem respondeu ainda: o plano portugues esta' instalado, mas **uma
factura chega a calcular-se**? Sao coisas diferentes. As contas podem estar
todas la' e a primeira factura falhar por um artigo sem conta de receita, um
contacto sem conta a receber, ou um imposto que nao se aplica.

O cliente quer facturar na proxima semana. Saber isto hoje vale mais do que
descobri-lo com ele ao telefone.

`COMO, SEM ESCREVER`
Cria-se a factura na transaccao e faz-se **rollback**. Nada fica.

  - Uma factura em rascunho nao consome numero: no Odoo 18 o `name` de um
    rascunho e' `/`, e o numero e' atribuido no lancamento. Nao ha' serie
    gasta.
  - O `rollback` desfaz as linhas. O que **nao** volta atras sao os
    contadores internos de id do PostgreSQL, que avancam e ficam com um
    buraco. E' inofensivo e nao e' visivel em sitio nenhum.
  - Nao ha' `commit` neste guiao. Nenhum.

`O QUE ISTO NAO PROVA`
A assinatura dos documentos e o SAF-T, que vivem no PT-Plus e dependem da
licenca Exo. Prova a metade que nao depende de licenca nenhuma: contabilistica.

  FASE=provar
"""
import os

FASE = os.environ.get('FASE', 'provar')


def titulo(t):
    print('')
    print('-' * 72)
    print(t)
    print('-' * 72)


env.cr.execute('SELECT current_database()')
print('')
print('=' * 72)
print('PROVA DA CADEIA DE FACTURACAO (sem escrever)')
print('=' * 72)
print('  base: %s' % env.cr.fetchone()[0])
print('  empresa: %s   moeda: %s'
      % (env.company.name, env.company.currency_id.name))

try:
    # --- escolher um cliente e um artigo reais -----------------------------
    cliente = env['res.partner'].search(
        [('is_company', '=', True), ('country_id.code', '=', 'PT'),
         ('id', '!=', env.company.partner_id.id)], limit=1)
    artigo = env['product.product'].search(
        [('sale_ok', '=', True)], limit=1)
    if not cliente or not artigo:
        print('  PARADO: nao encontro cliente portugues ou artigo vendavel')
        raise SystemExit

    titulo('O QUE VAI NA FACTURA')
    print('  cliente : %s (id %s)' % (cliente.name, cliente.id))
    print('    conta a receber : %s'
          % (cliente.property_account_receivable_id.code or '(vazia)'))
    print('    posicao fiscal  : %s'
          % (cliente.property_account_position_id.display_name or '(nenhuma)'))
    print('  artigo  : %s (id %s)' % (artigo.name, artigo.id))
    print('    categoria       : %s' % artigo.categ_id.complete_name)
    print('    conta de receita: %s'
          % (artigo.property_account_income_id.code
             or artigo.categ_id.property_account_income_categ_id.code
             or '(NENHUMA — a factura vai falhar)'))
    print('    imposto de venda: %s'
          % (', '.join(artigo.taxes_id.mapped('name')) or '(nenhum no artigo)'))

    diario = env['account.journal'].search(
        [('type', '=', 'sale'), ('company_id', '=', env.company.id)], limit=1)
    print('  diario  : %s %s   conta por defeito: %s'
          % (diario.code, diario.name,
             diario.default_account_id.code or '(vazia)'))

    # --- criar, em transaccao que nao fica ---------------------------------
    titulo('A FACTURA, CALCULADA')
    f = env['account.move'].create({
        'move_type': 'out_invoice',
        'partner_id': cliente.id,
        'journal_id': diario.id,
        'invoice_line_ids': [(0, 0, {
            'product_id': artigo.id,
            'quantity': 2,
            'price_unit': 1000.0,
        })],
    })
    print('  numero no rascunho    : %s   (esperado «/» — sem serie gasta)' % f.name)
    print('  estado                : %s' % f.state)
    print('  diario                : %s' % f.journal_id.code)
    print('  moeda                 : %s' % f.currency_id.name)
    print('')
    for l in f.invoice_line_ids:
        print('  linha: %s x %s a %.2f' % (l.quantity, l.product_id.name, l.price_unit))
        print('    conta          : %s %s'
              % (l.account_id.code or '(VAZIA)', l.account_id.name or ''))
        print('    impostos       : %s'
              % (', '.join(l.tax_ids.mapped('name')) or '(NENHUM)'))
        print('    base           : %.2f' % l.price_subtotal)
    print('')
    print('  base tributavel       : %.2f %s' % (f.amount_untaxed, f.currency_id.name))
    print('  imposto               : %.2f' % f.amount_tax)
    print('  total                 : %.2f' % f.amount_total)
    print('  a receber             : %.2f' % f.amount_residual)

    titulo('AS CONTRAPARTIDAS QUE O LANCAMENTO PRODUZIRIA')
    for l in f.line_ids:
        print('  %-10s %-34s debito=%10.2f credito=%10.2f'
              % (l.account_id.code or '?', (l.account_id.name or '')[:34],
                 l.debit, l.credit))
    equilibrio = sum(f.line_ids.mapped('debit')) - sum(f.line_ids.mapped('credit'))
    print('  equilibrio (debito - credito): %.2f  %s'
          % (equilibrio, 'OK' if abs(equilibrio) < 0.01 else 'DESEQUILIBRADO'))

    titulo('E O MESMO PARA UMA FACTURA DE COMPRA')
    dcompra = env['account.journal'].search(
        [('type', '=', 'purchase'), ('company_id', '=', env.company.id)], limit=1)
    c = env['account.move'].create({
        'move_type': 'in_invoice',
        'partner_id': cliente.id,
        'journal_id': dcompra.id,
        'invoice_line_ids': [(0, 0, {
            'product_id': artigo.id,
            'quantity': 1,
            'price_unit': 500.0,
        })],
    })
    for l in c.invoice_line_ids:
        print('  conta de gasto        : %s %s'
              % (l.account_id.code or '(VAZIA)', l.account_id.name or ''))
        print('  imposto de compra     : %s'
              % (', '.join(l.tax_ids.mapped('name')) or '(NENHUM)'))
    print('  total da compra       : %.2f' % c.amount_total)

finally:
    # Sempre, aconteca o que acontecer. Nada fica na base.
    env.cr.rollback()
    print('')
    print('  ROLLBACK feito — nada ficou gravado.')
    env.cr.execute('select count(*) from account_move')
    print('  account_move na base: %s' % env.cr.fetchone()[0])

print('')
print('PROVA=FIM')
