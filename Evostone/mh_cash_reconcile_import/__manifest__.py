# -*- coding: utf-8 -*-
{
    'name': 'MH Cash Reconcile Import/Export',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Exportar movimentos de caixa não reconciliados e importar como extracto',
    'description': """
MH Cash Reconcile Import/Export
===============================

Este módulo permite:
- Exportar movimentos não reconciliados do diário de caixa para Excel
- Importar ficheiro Excel como linhas de extracto para reconciliação

Funcionalidades:
- Botão "Exportar Excel" no diário de caixa
- Botão "Importar Excel" no diário de caixa
- Filtro por período de datas
- Colunas: Data, Referência, Descrição, Parceiro, Conta, Débito, Crédito
- Criação automática de account.bank.statement.line para reconciliação
    """,
    'author': 'MH',
    'website': '',
    'license': 'LGPL-3',
    'depends': [
        'account',
    ],
    'data': [
        'security/ir.model.access.csv',
        'wizard/cash_wizard_views.xml',
        'views/account_journal_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
