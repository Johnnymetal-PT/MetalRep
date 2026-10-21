# -*- coding: utf-8 -*-
{
    'name': 'MH Layout PDF',
    'summary': 'Layout customizado para documentos PDF estilo Stone Trading',
    'description': """
        Layout Customizado para Documentos PDF
        =======================================

        Este módulo fornece um layout profissional para documentos PDF do Odoo,
        replicando o design da fatura Stone Trading com:

        * Cabeçalho com logo e informações da empresa
        * Seção de dados do emissor e destinatário
        * Tabela de produtos/serviços detalhada
        * Totalizadores com IVA
        * Rodapé com dados bancários
        * Referência administrativa

        Compatível com recibos pró-forma, faturas e outros documentos.
    """,
    'author': 'MH',
    'category': 'Accounting/Accounting',
    'version': '18.0.1.0.0',
    'depends': [
        'web',
        'account',
        'sale',
        # 'mh_sale'
    ],
    'data': [
        'data/paperformat_stone.xml',
        'views/report_templates.xml',
        'data/report_layout.xml',
    ],
    'assets': {
        'web.report_assets_common': [
            'mh_layout_pdf/static/src/scss/stone_layout.scss',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
