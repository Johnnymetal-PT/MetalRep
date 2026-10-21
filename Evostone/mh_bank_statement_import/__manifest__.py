# -*- coding: utf-8 -*-
{
    'name': 'MH Bank Statement Import',
    'version': '18.0.1.0.0',
    'category': 'Accounting/Accounting',
    'summary': 'Importação de extractos bancários BIM, BCI, BCI Cartão Crédito, BIM Pré-Pago, Mozabanco',
    'description': """
MH Bank Statement Import
========================

Módulo para importação de extractos bancários de bancos moçambicanos:

Bancos Suportados:
- BIM (Banco Internacional de Moçambique) - formato xlsx
- BCI (Banco Comercial e de Investimentos) - formato xls
- BCI Cartão de Crédito VISA - formato xls
- BIM Cartão Pré-Pago - formato csv
- Mozabanco - formato csv

Funcionalidades:
- Detecção automática do banco pelo formato do ficheiro
- Parsing de extractos Excel e CSV
- Criação automática de linhas de extracto bancário
- Prevenção de importação duplicada
- Reconciliação automática (se activada)

Autor: MH
    """,
    'author': 'MH',
    'website': '',
    'depends': [
        'account_bank_statement_import',
        'account',
    ],
    'external_dependencies': {
        'python': ['openpyxl', 'xlrd'],
    },
    'data': [
        'security/ir.model.access.csv',
        'wizard/bank_statement_import_preview_views.xml',
        'views/account_journal_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
