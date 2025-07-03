# -*- coding: utf-8 -*-
{
    'name': 'PG ZPL TAGS 2',
    'version': '2.0',
    'summary': 'PG ZPL TAGS 2',
    'description': """
        Imprimir etiquetas ZPL 2.
    """,
    'author': 'PG',
    'website': 'https://www.parametro.pt',

    'depends': ['sale_stock'],

    'assets': {
        'point_of_sale._assets': [
            'pg_zpl_tags/static/src/description/*',
        ],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/zpl_label_wizard_view.xml',
        'views/zpl_tags.xml',
    ],
    'installable': True,
    'application': False
}
