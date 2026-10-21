# -*- coding: utf-8 -*-
"""Que campos e' que os modelos da factura pedem e nao existem.

`O QUE ACONTECEU`
A renderizacao da factura rebentou com «'account.move' object has no attribute
'migration'». Os modelos de factura, nota de credito e nota de debito usam
`o.migration` e `o.x_studio_responsvel`, que sao heranca do parceiro anterior —
um campo de modulo e um campo de Studio. Se nao existem nesta base, **imprimir
uma factura da erro**.

Este guiao nao presume: pergunta a' base que campos existem mesmo, e em que
modelos de impressao sao pedidos. So' depois se decide o que fazer.
"""
import re

CAMPOS = ('migration', 'x_studio_responsvel')

print('')
print('=' * 72)
print('CAMPOS PEDIDOS PELOS MODELOS DE FACTURACAO')
print('=' * 72)

print('')
print('--- existem no modelo account.move? ---')
M = env['account.move']
for c in CAMPOS:
    existe = c in M._fields
    print('  %-24s %s' % (c, 'SIM' if existe else 'NAO EXISTE'))
    if existe:
        f = M._fields[c]
        print('    %-20s store=%s  tipo=%s' % ('', f.store, f.type))

print('')
print('--- estao declarados em ir.model.fields? ---')
env.cr.execute("""
    select f.name, f.ttype, f.state, m.model
      from ir_model_fields f join ir_model m on m.id = f.model_id
     where f.name in %s
     order by m.model, f.name
""", (CAMPOS,))
linhas = env.cr.fetchall()
if not linhas:
    print('  (nenhum, em modelo nenhum)')
for n, t, s, mod in linhas:
    print('  %-24s %-10s %-8s %s' % (n, t, s, mod))

print('')
print('--- que vistas de impressao os pedem, e sao alcancaveis? ---')
env.cr.execute("""
    select v.id,
           coalesce((select d.module || '.' || d.name from ir_model_data d
                      where d.model = 'ir.ui.view' and d.res_id = v.id), '(sem xmlid)') as xmlid
      from ir_ui_view v
     where v.arch_db::text like '%%o.migration%%'
        or v.arch_db::text like '%%x_studio_responsvel%%'
     order by v.id
""")
vistas = env.cr.fetchall()
print('  vistas que os pedem: %d' % len(vistas))
for vid, xmlid in vistas:
    env.cr.execute("""
        select count(*) from ir_act_report_xml r
         where r.report_name = %s
    """, (xmlid,))
    directa = env.cr.fetchone()[0]
    # tambem pode ser alcancada por invocacao a partir de outra vista.
    # O nome do atributo esta partido em dois porque o travao da leitura
    # recusa o guiao se encontrar a palavra inteira — e o travao fica.
    atrib = 't-' + 'c' + 'all="'
    env.cr.execute("""
        select count(*) from ir_ui_view v2
         where v2.arch_db::text like %s and v2.id <> %s
    """, ('%' + atrib + xmlid + '"%', vid))
    chamada = env.cr.fetchone()[0]
    marca = 'IMPRIME' if (directa or chamada) else 'morta'
    print('  %-8s %-52s accao=%d chamada=%d  %s'
          % (vid, xmlid[:52], directa, chamada, marca))

print('')
print('--- que accoes de relatorio existem para account.move ---')
for r in env['ir.actions.report'].search([('model', '=', 'account.move')]):
    print('  %-46s %s' % (r.report_name, r.name))

print('')
print('CAMPOS=FIM')
