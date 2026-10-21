# -*- coding: utf-8 -*-

{
    'name': 'PG CRM Activity Report Highlight',
    'version': '19.0.1.0.0',
    'category': 'CRM',
    'summary': 'Destaca atividades concluidas no relatorio de atividades CRM.',
    'description': '''
Objetivo de negocio
===================
Ajuda utilizadores comerciais a distinguir rapidamente linhas concluídas no relatório de atividades CRM.

Pre-requisitos
==============
Modulo CRM instalado e vista standard `crm.crm_activity_report_view_tree` disponível.

Como funciona
=============
Herda a list view de `crm.activity.report`, adiciona `decoration-success` quando `date` está preenchida e aplica uma classe SCSS própria para styling adicional.

Passo a passo de utilizacao
===========================
1. Instalar o modulo. 2. Abrir CRM > Relatórios/Atividades. 3. Ver as linhas concluídas realçadas.

Exemplo pratico
===============
Uma atividade com campo `date` preenchido aparece com destaque visual; atividades sem data mantêm o estilo normal.

FAQ / Resolucao de problemas
============================
Se nada muda, confirmar se a vista herdada existe em Odoo 19 e se o asset SCSS foi carregado. Se o critério de conclusão mudar, ajustar a expressão `date != False`.

Pontos de atencao / avisos
==========================
A lógica usa o campo agregado `date` do relatório, não o estado da atividade original. É uma alteração visual, sem impacto nos dados.
''',
    'author': 'PG',
    'license': 'LGPL-3',
    'depends': ['crm'],
    'data': ['views/pg_crm_activity_report_views.xml'],
    'assets': {'web.assets_backend': ['pg_crm_activity_report_highlight/static/src/scss/pg_crm_activity_report.scss']},
    'installable': True,
    'application': False,
}
