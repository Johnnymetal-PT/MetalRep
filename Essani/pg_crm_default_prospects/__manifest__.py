# -*- coding: utf-8 -*-

{
    'name': 'PG CRM Default Prospects',
    'version': '19.0.1.0.0',
    'category': 'CRM',
    'summary': 'Abre o CRM diretamente na lista de prospetos.',
    'description': '''
Objetivo de negocio
===================
Alinha a entrada da aplicação CRM com o processo comercial da Essani, onde a primeira vista útil é a lista de prospetos/leads.

Pre-requisitos
==============
Modulo CRM instalado e ação `crm.crm_lead_all_leads` existente.

Como funciona
=============
Atualiza o menu raiz do CRM para apontar para a ação de todos os leads, em vez da pipeline standard.

Passo a passo de utilizacao
===========================
1. Instalar/atualizar. 2. Clicar na aplicação CRM. 3. Confirmar que abre a vista de prospetos/leads.

Exemplo pratico
===============
Um comercial entra no CRM e vê imediatamente a lista de oportunidades/prospetos em vez do kanban de pipeline.

FAQ / Resolucao de problemas
============================
Se continua a abrir a vista antiga, limpar cache do menu ou confirmar se outro modulo também alterou `crm.crm_menu_root`.

Pontos de atencao / avisos
==========================
É uma alteração de navegação, sem dados. Pode ser substituída por configuração/menu se o processo mudar.
''',
    'author': 'PG',
    'license': 'LGPL-3',
    'depends': ['crm'],
    'data': ['views/pg_crm_menu_views.xml'],
    'installable': True,
    'application': False,
}
