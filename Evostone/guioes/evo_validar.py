# -*- coding: utf-8 -*-
"""Validacao do estado final de tudo o que foi alterado em 14 e 15/09.

Nao repete o que eu afirmei: volta a ler a base e compara com o esperado.
"""
import re

ok = []
mau = []


def conferir(titulo, condicao, detalhe):
    (ok if condicao else mau).append((titulo, detalhe))
    print('  [%s] %-44s %s' % ('OK' if condicao else '!!', titulo, detalhe))


print('')
print('=' * 72)
print('VALIDACAO DO ESTADO FINAL')
print('=' * 72)
env.cr.execute('SELECT current_database()')
print('  base: %s' % env.cr.fetchone()[0])
ICP = env['ir.config_parameter'].sudo()

print('')
print('--- 1. correio ---')
conferir('mail.force.smtp.from removido',
         not ICP.get_param('mail.force.smtp.from'),
         ICP.get_param('mail.force.smtp.from') or '(nao definido)')
conferir('mail.bounce.alias', ICP.get_param('mail.bounce.alias') == 'bounce',
         ICP.get_param('mail.bounce.alias'))
S = env['ir.mail_server'].sudo()
msg = S.build_email(
    email_from='%s@%s' % (ICP.get_param('mail.default.from'),
                          ICP.get_param('mail.catchall.domain')),
    email_to=['ninguem@example.invalid'], subject='validacao', body='x')
conferir('remetente no dominio da base',
         'pemaro' not in (msg['From'] or '').lower(), msg['From'])

print('')
print('--- 2. modelos de impressao ---')
VISTAS = ('view_report_purchaseorder_document', 'view_report_invoice_document',
          'view_report_sale_quotation_document', 'view_report_credit_note_document',
          'view_report_debit_note_document', 'view_report_payment_receipt_document',
          'view_report_sale_proforma_document',
          'view_report_sale_detailed_quotation_document',
          'view_report_proforma_payment_document', 'view_report_delivery_guide_document')
sujas, sem_desc = [], []
for nome in VISTAS:
    v = env.ref('mh_stone_reports.' + nome, raise_if_not_found=False)
    if not v:
        sujas.append(nome + ' (ausente)')
        continue
    a = str(v.arch_db or '')
    if re.search('STONE TRADING|Matola|Machava|NUIT|MOZA|4381052010001|Daf:', a):
        sujas.append(nome)
    if 'line.product_id' in a:
        sem_desc.append(nome)
conferir('10 vistas sem vestigio', not sujas, sujas or 'todas limpas')
conferir('nenhuma imprime line.product_id', not sem_desc, sem_desc or 'usam line.name')

print('')
print('--- 3. valorizacao de stock ---')
Cat = env['product.category'].with_context(active_test=False)
rt = Cat.search([('property_valuation', '=', 'real_time')])
conferir('nenhuma categoria exige contas inexistentes', not rt,
         '%d em real_time' % len(rt))

print('')
print('--- 4. areas de actuacao ---')
env.cr.execute("select distinct product_classification from product_template where product_classification is not null")
usadas = set(c for (c,) in env.cr.fetchall())
cobertas = set()
for t in env['service.type'].with_context(active_test=False).search([]):
    cobertas |= set(t.area_ids.mapped('code'))
conferir('catalogo todo coberto por areas', usadas <= cobertas,
         'sem cobertura: %s' % (sorted(usadas - cobertas) or 'nenhuma'))
P = env['purchase.order'].with_context(active_test=False)
desal = [o.name for o in P.search([])
         if set(o.service_type_area_ids.ids) != set(o.service_type_id.area_ids.ids)]
conferir('encomendas com retrato actualizado', not desal, desal or 'as 3 alinhadas')

print('')
print('--- 5. site e nomes ---')
testes = [
    ('paginas do site limpas',
     "select count(*) from website_page p join ir_ui_view v on v.id=p.view_id where v.arch_db::text ~* 'pemaro|matola|machava|stone trading'"),
    ('sequencias sem a marca',
     "select count(*) from ir_sequence where name ilike '%stone trading%' or name ilike '%pemaro%' or name ilike '%maputo%' or prefix ilike '%PMR%' or prefix ilike '%MPT%'"),
    ('modelos de email sem a marca',
     "select count(*) from mail_template where coalesce(name::text,'')||coalesce(subject::text,'')||coalesce(body_html::text,'') ~* 'stone trading|pemaro'"),
    ('campos sem NUIT',
     "select count(*) from ir_model_fields where field_description::text ilike '%nuit%'"),
]
for titulo, sql in testes:
    env.cr.execute(sql)
    v = env.cr.fetchone()[0]
    conferir(titulo, v == 0, '%d' % v)

print('')
print('--- 6. impostos nos artigos ---')
# `PORQUE ESTE TESTE EXISTE`
# Os 22 artigos que o cliente criou a 12/09 herdaram o IVA de venda da empresa
# e **nao** o de compra. O defeito nao aparecia em lado nenhum: so' saltou a'
# vista quando a factura de compra da prova saiu a 500,00 em vez de 615,00.
# Um artigo sem IVA de compra e' uma factura de fornecedor sem IVA.
env.cr.execute("""
    select count(*) from product_template t
     where t.sale_ok and not exists (select 1 from product_taxes_rel r where r.prod_id = t.id)
""")
conferir('artigos vendaveis com IVA de venda', env.cr.fetchone()[0] == 0, 'todos')
env.cr.execute("""
    select count(*) from product_template t
     where t.purchase_ok and not exists (select 1 from product_supplier_taxes_rel r where r.prod_id = t.id)
""")
n_sc = env.cr.fetchone()[0]
conferir('artigos compraveis com IVA de compra', n_sc == 0, '%d sem' % n_sc)

print('')
print('--- 7. efeitos colaterais ---')
conferir('lancamentos contabilisticos a zero',
         env['account.move'].search_count([]) == 0,
         '%d' % env['account.move'].search_count([]))
conferir('existencias a zero', env['stock.quant'].search_count([]) == 0,
         '%d' % env['stock.quant'].search_count([]))
n_p = env['res.partner'].with_context(active_test=False).search_count([])
conferir('contactos intactos', n_p >= 2950, '%d' % n_p)
n_c = env['ir.cron'].sudo().search_count([('active', '=', True)])
conferir('crons repostos', n_c == 32, '%d' % n_c)
conferir('nenhuma janela aberta', not ICP.get_param('pg.janela.crons'),
         ICP.get_param('pg.janela.crons') or '(fechada)')
conferir('modulos protegidos instalados',
         all(env['ir.module.module'].search([('name', '=', m)], limit=1).state == 'installed'
             for m in ('mh_stone_reports', 'mh_accounting_reports', 'mh_base')),
         'os tres')
env.cr.execute("select count(*) from ir_module_module where state in ('to upgrade','to remove','to install')")
conferir('nenhum modulo em transicao', env.cr.fetchone()[0] == 0, 'ok')

print('')
print('=' * 72)
print('  passou: %d    falhou: %d' % (len(ok), len(mau)))
for t, d in mau:
    print('    FALHA: %s -> %s' % (t, d))
print('=' * 72)
print('')
print('VALIDACAO=FIM')
