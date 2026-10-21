# -*- coding: utf-8 -*-
"""Poe o IVA portugues nos 13 artigos que ficaram sem imposto.

`COMO ISTO APARECEU`
A prova da cadeia de facturacao (`evo_prova_factura.py`) criou uma factura em
memoria e ela saiu com **IVA a zero**:

    imposto de venda: (nenhum no artigo)
    imposto        : 0.00
    total          : 2000.00

`A CAUSA, E O QUE EU TINHA REPORTADO MAL`
Eu escrevi «imposto por defeito compra=23% / venda=23%» como sinal de que os
impostos estavam configurados. Estao — para artigos **novos**. O
`account_sale_tax_id` da empresa e' o defeito de criacao de um artigo, nao uma
regra que se aplique aos que ja existem. O Odoo tira o imposto da linha do
**artigo**, e os 13 artigos ficaram com o `taxes_id` vazio quando as taxas
mocambicanas foram apagadas com o plano antigo.

Sem isto, a primeira factura da EVOSTONE sai sem IVA. E ninguem descobre lendo
a configuracao, porque a configuracao esta' certa: descobre-se tentando
facturar.

`ESCOLHA DOS IMPOSTOS`
Os normais que o `l10n_pt` criou: venda «23%» e compra «23%». As variantes
`23% EU G` e `23% EU S` sao para operacoes intracomunitarias e entram pelas
posicoes fiscais, nao pelo defeito do artigo — atribui-las aqui punha IVA
intracomunitario em vendas nacionais.

`OS ARTIGOS DE DESPESA` (Meals, Travel, Mileage, Gifts, Communication,
Expenses) sao de origem do Odoo e nao se vendem. Levam os dois impostos de
qualquer forma, que e' o que o Odoo faz a um artigo novo — nao ha' razao para os
tratar de forma diferente, e um artigo de despesa com imposto de venda nao
produz efeito nenhum enquanto ninguem o vender.

  FASE=ver       le e mostra o que faria
  FASE=aplicar   escreve (exige ESCREVER=1)
"""
import os

FASE = os.environ.get('FASE', 'ver')
ESCREVER = os.environ.get('ESCREVER') == '1'


def guarda():
    env.cr.execute('SELECT current_database()')
    b = env.cr.fetchone()[0]
    print('  base: %s' % b)
    if '-staging-' in b:
        return True
    if os.environ.get('PRODUCAO') != 'confirmo':
        print('  PARADO: a base nao e de staging. Para correr aqui: PRODUCAO=confirmo')
        return False
    print('  !!! ESTA BASE NAO E DE STAGING !!!')
    return True


print('')
print('=' * 72)
print('IVA PORTUGUES NOS ARTIGOS')
print('=' * 72)

if not guarda():
    pass
else:
    T = env['account.tax'].with_context(active_test=False)
    # Pelo defeito da empresa, e nao por id escrito a mao: se alguem mudar o
    # imposto por defeito, este guiao segue-o em vez de contradize-lo.
    venda = env.company.account_sale_tax_id
    compra = env.company.account_purchase_tax_id
    print('  imposto de venda da empresa : %s'
          % (venda.display_name if venda else '(NENHUM)'))
    print('  imposto de compra da empresa: %s'
          % (compra.display_name if compra else '(NENHUM)'))

    if not venda or not compra:
        print('')
        print('  PARADO: a empresa nao tem imposto por defeito nos dois lados.')
        print('  Sem ele nao sei o que atribuir, e nao escolho por mim.')
    else:
        P = env['product.template'].with_context(active_test=False)
        artigos = P.search([])
        sem_venda = artigos.filtered(lambda a: not a.taxes_id)
        sem_compra = artigos.filtered(lambda a: not a.supplier_taxes_id)
        print('')
        print('  artigos: %d   sem imposto de venda: %d   sem imposto de compra: %d'
              % (len(artigos), len(sem_venda), len(sem_compra)))
        print('')
        print('  %-6s %-46s %-14s %s' % ('id', 'artigo', 'venda', 'compra'))
        for a in artigos:
            print('  %-6s %-46s %-14s %s'
                  % (a.id, (a.name or '')[:46],
                     ', '.join(a.taxes_id.mapped('name')) or 'FALTA',
                     ', '.join(a.supplier_taxes_id.mapped('name')) or 'FALTA'))

        if not sem_venda and not sem_compra:
            print('')
            print('  nada a fazer')
        elif FASE != 'aplicar':
            print('')
            print('  a FASE=aplicar poria %s na venda e %s na compra'
                  % (venda.name, compra.name))
        elif not ESCREVER:
            print('')
            print('  (ensaio — ESCREVER=1 para escrever)')
        else:
            print('')
            print('  a escrever...')
            if sem_venda:
                sem_venda.write({'taxes_id': [(6, 0, venda.ids)]})
                print('    imposto de venda em %d artigos' % len(sem_venda))
            if sem_compra:
                sem_compra.write({'supplier_taxes_id': [(6, 0, compra.ids)]})
                print('    imposto de compra em %d artigos' % len(sem_compra))
            env.cr.commit()
            print('')
            print('  a reconferir...')
            artigos = P.search([])
            falta_v = len(artigos.filtered(lambda a: not a.taxes_id))
            falta_c = len(artigos.filtered(lambda a: not a.supplier_taxes_id))
            print('  ainda sem imposto — venda: %d   compra: %d' % (falta_v, falta_c))
            print('')
            print('  Correr o evo_prova_factura.py a seguir: e ele que diz se')
            print('  a factura passa a sair com IVA, e nao esta contagem.')

print('')
print('IMPOSTOS=FIM')
