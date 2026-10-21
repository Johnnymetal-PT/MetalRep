# -*- coding: utf-8 -*-
"""Os restantes 43 modelos com relatorios — e a verificacao do «codigo morto».

`PORQUE E' QUE ISTO E' PRECISO`
O `evo_prova_documentos.py` cobriu seis modelos: compras, vendas, facturas,
entregas, pagamentos. Ficaram de fora os relatorios da **pedra**, que sao
exactamente os que o cliente vai usar quando comecar a receber chapas —
etiquetas, autocolantes, numeros de serie, listagens de stock. Nenhum foi
testado.

`E A SEGUNDA RAZAO`
Eu dei o `other_reports.xml` como codigo morto: 73 vistas com nome uuid, nenhuma
alcancavel. Mas existem **accoes de relatorio** com nome uuid, em `hr.payslip`,
`x_modelo_irps`, `x_placa` e outros. Ou a minha conclusao estava errada, ou as
accoes apontam para vistas que nao sao aquelas. Este guiao pergunta em vez de
presumir.

So' testa modelos que **tem registos reais**. Criar um `stone.stock` ou um
`x_modelo_irps` a' forca daria um erro meu, nao um erro do sistema.
"""
import traceback

SALTAR = ('purchase.order', 'sale.order', 'account.move', 'stock.picking',
          'account.payment', 'proforma.payment')

print('')
print('=' * 74)
print('OS RESTANTES RELATORIOS')
print('=' * 74)

bons, maus, sem = [], [], []
try:
    accoes = env['ir.actions.report'].search([], order='model, report_name')
    accoes = accoes.filtered(lambda a: a.model not in SALTAR)
    print('  accoes a testar: %d' % len(accoes))
    modelo_actual = None
    for a in accoes:
        if a.model != modelo_actual:
            modelo_actual = a.model
            print('')
            print('--- %s ---' % modelo_actual)
        if a.model not in env:
            print('  [--] %-44s (modelo inexistente)' % a.report_name[:44])
            sem.append(a.report_name)
            continue
        reg = env[a.model].search([], order='id desc', limit=1)
        if not reg:
            print('  [--] %-44s (sem registos)' % a.report_name[:44])
            sem.append(a.report_name)
            continue
        try:
            html = a._render_qweb_html(a.report_name, reg.ids)[0]
            if isinstance(html, bytes):
                html = html.decode('utf-8', 'replace')
            bons.append(a.report_name)
            print('  [OK] %-44s %6d car.' % (a.report_name[:44], len(html)))
        except Exception as e:
            env.cr.rollback()
            ls = [l for l in traceback.format_exc().splitlines()
                  if 'Error' in l or 'error' in l]
            msg = (ls[-1] if ls else str(e)).strip()
            maus.append((a.report_name, a.model, msg))
            print('  [!!] %-44s %s' % (a.report_name[:44], msg[:70]))
finally:
    env.cr.rollback()

print('')
print('=' * 74)
print('  imprimem: %d    rebentam: %d    sem registos: %d'
      % (len(bons), len(maus), len(sem)))
for n, m, e in maus:
    print('    REBENTA %-46s (%s)' % (n[:46], m))
    print('             %s' % e[:110])
print('=' * 74)

print('')
print('--- e o other_reports.xml: as accoes uuid apontam para onde? ---')
# A pergunta que eu nao fiz da primeira vez.
env.cr.execute("""
    select r.report_name,
           r.model,
           (select d.module || '.' || d.name from ir_model_data d
             join ir_ui_view v on v.id = d.res_id
            where d.model = 'ir.ui.view'
              and d.module || '.' || d.name = r.report_name) as vista_alvo
      from ir_act_report_xml r
     where r.report_name ~ '[0-9a-f]{8}-[0-9a-f]{4}'
     order by r.model
""")
linhas = env.cr.fetchall()
print('  accoes com nome uuid: %d' % len(linhas))
orfas = 0
for nome, modelo, alvo in linhas:
    estado = alvo if alvo else 'SEM VISTA'
    if not alvo:
        orfas += 1
    print('  %-30s %-26s %s' % (modelo[:30], nome.split('.')[-1][:26], estado and 'vista existe' or ''))
print('')
print('  accoes uuid sem vista correspondente: %d' % orfas)

print('')
print('DOCUMENTOS2=FIM')
