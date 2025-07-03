# -*- coding: utf-8 -*-
{
    'name': 'PG ZPL TAGS',
    'version': '1.0',
    'summary': 'PG ZPL TAGS',
    'description': """
        Imprimir etiquetas ZPL.
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
        'views/zpl_tags.xml',
    ],
    'installable': True,
    'application': False
}
